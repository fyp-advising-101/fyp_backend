from flask import Flask , request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.apis.azure_key_vault import AzureKeyVault
from shared.apis.azure_blob import AzureBlobManager
from shared.models.job import Job
from shared.models.media_category_options import MediaCategoryOptions
from shared.models.media_gen_options import MediaGenOptions
from shared.database import engine, SessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import text
from media_gen.apis.imagine_api import ImagineArtAI
from shared.models.media_asset import MediaAsset
from media_gen.apis.runway_api import RunwayAPI 
from shared.apis.chatgpt_api import ChatGptApi
from datetime import timedelta
import datetime
import random
from chromadb import HttpClient
import requests
import logging

#Set up Azure Key Vault credentials
key_vault = AzureKeyVault()
IMAGINE_API_KEY = key_vault.get_secret("IMAGINE-API-KEY")
OPENAI_API_KEY = key_vault.get_secret("OPENAI-API-KEY")
RUNWAY_API_KEY = key_vault.get_secret("AI-VIDEO-API-KEY")
runway_api = RunwayAPI(api_key=RUNWAY_API_KEY)
AZURE_STORAGE_CONNECTION_STRING =key_vault.get_secret("posting-connection-key")

# Initialize NovitaAI and ChatGPT API instances
chatgpt_api = ChatGptApi(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
azureBlob = AzureBlobManager(AZURE_STORAGE_CONNECTION_STRING)
# Initialize the vector database client and get the collection
vector_client = HttpClient(host='20.203.61.164', port=8000)
collection = vector_client.get_collection(name="aub_embeddings")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route("/generate-image/<int:job_id>", methods=["POST"])
def generate_image_route(job_id):
    """
    Generate an image using ImagineArt AI by:
    - Retrieving the related `question` from `media_gen_options`.
    - Generating an embedding from `question` and querying ChromaDB.
    - Getting the best-matching document from the results.
    - Using ChatGPT to generate an enhanced image prompt.
    - Sending the prompt to ImagineArtAI to generate an image.
    - Uploading the generated image to Azure Blob Storage.
    """

    db_session = SessionLocal()
    job = None
    try:
        # Step 1: Query the Job by ID
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")

        # Verify that the job has the correct task type and status
        if job.task_name.lower() != "create image" or job.status != 1:
            raise Exception("Job is not valid for image generation")

        # Step 2: Retrieve MediaGenOption based on task_id
        media_gen_option = (
            db_session.query(MediaGenOptions)
            .options(joinedload(MediaGenOptions.category_options))
            .filter_by(id=job.task_id)
            .first()
        )
        
        if not media_gen_option:
            raise Exception("Media Generation Option not found")
        
        category_options = media_gen_option.category_options
        if not category_options:
            raise Exception("No category options found for this media generation option")
        
        # Randomly select one MediaCategoryOption
        selected_option = random.choice(category_options)
        chroma_query = selected_option.chroma_query

        # Step 3: Generate an Embedding for the Question
        question_embedding = chatgpt_api.get_openai_embedding(chroma_query)

        # Step 4: Query ChromaDB for the Most Relevant Context
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=1,  # Get the best match
            where={"id": {"$ne": "none"}}  # Ensure we're not matching empty results
        )

        # Step 5: Validate the Retrieved Documents
        if "documents" not in results or not results["documents"]:
            raise Exception("No relevant documents found in vector database.")

        retrieved_docs = results["documents"][0]
        context = "\n".join(retrieved_docs) if retrieved_docs else "No context available."

        # Step 6: Generate a More Detailed AI Image Prompt Using ChatGPT
        image_prompt = chatgpt_api.generate_image_generation_prompt(
            f"Context: {context}\nOriginal Question: {chroma_query}"
        )
        # Step 7: Ask ChatGPT to Recommend a Style
        allowed_styles = ["flux-dev"]

        random_style = random.choice(allowed_styles)
        logging.info("Random Style: %s", random_style)


        # Step 8: Generate the Image Using ImagineArtAI
        
        imagine = ImagineArtAI(api_key=IMAGINE_API_KEY)
        try:
            logging.info("Calling ImagineArtAI.generate_image with style: %s", random_style)
            image_path = imagine.generate_image(image_prompt, style=random_style)
            logging.info("Image generated at path: %s", image_path)
        except Exception as e:
            logging.exception("Error while generating image")
            raise

        # Step 9: Upload the Generated Image to Azure Blob Storage
        safe_category = media_gen_option.category.lower().replace(" ", "_")

        # Add the category as part of the filename
        upload_result = azureBlob.upload_file(image_path, f"{safe_category}/image", "image/png")

        media_blob_url = upload_result.get("blob_url")

        caption = chatgpt_api.generate_caption(context, image_prompt, chroma_query)

        # Step 10: Update the Current Job Status
        job.status = 2
        job.updated_at = datetime.datetime.now().date()
        db_session.commit()

        new_asset = MediaAsset(
            media_blob_url=media_blob_url,
            caption=caption,
            media_type='image'
        )

        db_session.add(new_asset)
        db_session.commit()

        # Step 11: Create a New Job with Task Name "post image"
        insta_job = Job(
            task_name="post image instagram",
            task_id=new_asset.id,
            scheduled_date=(datetime.datetime.now() - timedelta(days=1)).date(),
            status=0,
            error_message=None,
            created_at=datetime.datetime.now().date(),
            updated_at=datetime.datetime.now().date()
        )
        db_session.add(insta_job)

        whats_job = Job(
            task_name="post image whatsapp",
            task_id=new_asset.id,
            scheduled_date=(datetime.datetime.now() - timedelta(days=1)).date(),
            status=0,
            error_message=None,
            created_at=datetime.datetime.now().date(),
            updated_at=datetime.datetime.now().date()
        )
        db_session.add(whats_job)
        
        db_session.commit()

        return jsonify({
            "media_asset_id": new_asset.id,
            "chroma_query": selected_option.chroma_query,
            "category": media_gen_option.category,  
            "job_id": job.id,
            "insta_job_id": insta_job.id,
            "whats_job_id": whats_job.id
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route("/generate-video/<int:job_id>", methods=["POST"])
def generate_video_route(job_id):
    """
    Generate a video using Runway AI by:
    - Retrieving the related category option from media_gen_options
    - Generating an embedding from the query and querying ChromaDB
    - Getting the best-matching document from the results
    - Using ChatGPT to generate an enhanced video prompt
    - Sending the prompt to Runway API to generate a video
    - Creating a job to monitor the video generation status
    """
    db_session = SessionLocal()
    job = None
    
    try:
        # Step 1: Query the Job by ID
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")

        # Verify that the job has the correct task type and status
        if job.task_name.lower() != "create video" or job.status != 1:
            raise Exception("Job is not valid for video generation")

        # Step 2: Retrieve MediaGenOption based on task_id
        media_gen_option = (
            db_session.query(MediaGenOptions)
            .options(joinedload(MediaGenOptions.category_options))
            .filter_by(id=job.task_id)
            .first()
        )
        
        if not media_gen_option:
            raise Exception("Media Generation Option not found")
        
        category_options = media_gen_option.category_options
        if not category_options:
            raise Exception("No category options found for this media generation option")
        
        # Randomly select one MediaCategoryOption
        selected_option = random.choice(category_options)
        prompt_text = selected_option.prompt_text
        chroma_query = selected_option.chroma_query

        # Step 3: Generate an Embedding for the Question
        question_embedding = chatgpt_api.get_openai_embedding(chroma_query)

        # Step 4: Query ChromaDB for the Most Relevant Context
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=1, 
            where={"id": {"$ne": "none"}}
        )

        # Step 5: Validate the Retrieved Documents
        if "documents" not in results or not results["documents"]:
            raise Exception("No relevant documents found in vector database.")

        retrieved_docs = results["documents"][0]
        context = "\n".join(retrieved_docs) if retrieved_docs else "No context available."

        # Step 6: Generate a More Detailed Video Prompt Using ChatGPT
        video_prompt = chatgpt_api.generate_video_generation_prompt(
            f"Context: {context}\nOriginal Question: {chroma_query}"
        )

        # Step 7: Send request to Runway API to generate the video
        uuid = runway_api.generate_video(
            prompt=video_prompt
        )

        if not uuid:
            raise Exception("Failed to generate video")

        # Step 8: Create a Media Asset entry (without URL yet)
        caption = chatgpt_api.generate_video_caption(context, video_prompt, chroma_query)
        
        new_asset = MediaAsset(
            media_blob_url="None",  # URL will be updated when video is ready
            caption=caption,
            media_type='video'
        )
        db_session.add(new_asset)
        db_session.commit()

        # Step 9: Create a job to monitor the video status
        monitor_job = Job(
            task_name="monitor video",
            task_id=uuid,  # Store the Runway task ID
            scheduled_date=datetime.datetime.now(),
            status=0,  # Pending
            error_message=None,
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        
        # Store the asset ID in a specific format in the error_message field (temporary storage)
        monitor_job.error_message = f"asset_id:{new_asset.id}"
        
        db_session.add(monitor_job)
        db_session.commit()

        # Step 10: Update the Current Job Status
        job.status = 2  # Completed
        job.updated_at = datetime.datetime.now()
        db_session.commit()

        return jsonify({
            "message": "Video generation started successfully",
            "media_asset_id": new_asset.id,
            "runway_uuid": uuid,
            "monitor_job_id": monitor_job.id
        }), 200

    except Exception as e:
        db_session.rollback()
        if job:
            job.status = -1  # Error
            job.error_message = str(e)
            db_session.commit()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route("/monitor-video/<int:job_id>", methods=["POST"])
def monitor_video_route(job_id):
    """
    Check the status of a video generation task and update the asset if complete.
    When the video is ready, create jobs to post it to social media.
    If the video is still processing, just return the current status.
    """
    db_session = SessionLocal()
    try:
        # Step 1: Query the monitoring job by ID
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")

        # Verify that the job is for monitoring a video
        if job.task_name.lower() != "monitor video" or job.status != 1:
            raise Exception("Job is not valid for video monitoring")

        # Step 2: Extract the Runway task ID and asset ID
        uuid = job.task_id
        asset_id = None
        
        # Extract asset_id from error_message field where we temporarily stored it
        if job.error_message and "asset_id:" in job.error_message:
            asset_id = int(job.error_message.split("asset_id:")[1])
        
        if not asset_id:
            raise Exception("Asset ID not found in monitoring job")
            
        # Step 3: Query the media asset
        asset = db_session.query(MediaAsset).filter_by(id=asset_id).first()
        if not asset:
            raise Exception("Media asset not found")

        # Step 4: Check video status - just a single check, not waiting
        data = runway_api.check_video_status(uuid)
        status = data.get("status", "").lower()

        if status == "success":
            # Video is ready - update the asset with the video URL
            video_url = data.get("url")
            if not video_url:
                raise Exception("Video completed but no URL provided")
              
            # Upload to Azure Blob Storage
            video_data = requests.get(video_url).content
            temp_path = f"/tmp/runway_video_{uuid}.mp4"
            
            with open(temp_path, "wb") as f:
                f.write(video_data)
                
            upload_result = azureBlob.upload_file(temp_path, "videos", "video/mp4")
            os.remove(temp_path)  # Clean up temp file
            
            if not upload_result or "blob_url" not in upload_result:
                raise Exception("Failed to upload video to Azure Blob Storage")
                
            # Update asset with the blob URL
            asset.media_blob_url = upload_result["blob_url"]
            db_session.commit()
            
            # Create jobs to post the video to social media
            insta_job = Job(
                task_name="post video instagram",
                task_id=asset.id,
                scheduled_date=datetime.datetime.now(),
                status=0,  # Pending
                error_message=None,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            db_session.add(insta_job)
            
            whats_job = Job(
                task_name="post video whatsapp",
                task_id=asset.id,
                scheduled_date=datetime.datetime.now(),
                status=0,  # Pending
                error_message=None,
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            db_session.add(whats_job)
            
            # Mark the monitoring job as completed
            job.status = 2  # Completed
            job.updated_at = datetime.datetime.now()
            db_session.commit()
            
            return jsonify({
                "message": "Video generation completed successfully",
                "media_asset_id": asset.id,
                "video_url": asset.media_blob_url,
                "instagram_job_id": insta_job.id,
                "whatsapp_job_id": whats_job.id
            }), 200        
        elif status == "failed":
            # Video generation failed
            job.status = -1  # Error
            job.error_message = f"Video generation failed: {status.get('error', 'Unknown error')}"
            job.updated_at = datetime.datetime.now()
            db_session.commit()
            
            return jsonify({
                "error": "Video generation failed", 
                "details": status.get('error', 'Unknown error')
            }), 400         
        else:
            job.status = 0 
            job.updated_at = datetime.datetime.now()
            db_session.commit()
            return jsonify({
                "message": "Video is still processing",
                "state": data,
                "media_asset_id": asset.id
            }), 200

    except Exception as e:
        db_session.rollback()
        if 'job' in locals() and job:
            job.status = -1  # Error
            job.error_message = str(e)
            db_session.commit()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route("/test-image-prompt", methods=["POST"])
def test_image_prompt_route():
    """
    Test route to generate an image prompt based on a query.
    Expects a JSON payload with a "context" and query field.
    Returns the generated image prompt without actually creating an image.
    """
    data = request.json
    db_session = SessionLocal()
    
    try:
        # Validate the request
        if not data or "context" not in data:
            return jsonify({"error": "Request must include a 'context' field"}), 400
            
        context = data["context"]
        query = data["query"]
         
        # Generate the image prompt
        image_prompt = chatgpt_api.generate_image_generation_prompt(
            f"Context: {context}\nOriginal Question: {query}"
        )

        caption = chatgpt_api.generate_caption(context=context, chroma_query=query)
        
        # Return the results
        return jsonify({
            "query": query,
            "generated_image_prompt": image_prompt,
            "generated_caption" : caption
        }), 200
        
    except Exception as e:
        logging.error(f"Error in test-image-prompt: {str(e)}")
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route("/test-chroma-query", methods=["POST"])
def test_chroma_query_route():
    """
    Test route to test chroma query.
    Expects a JSON payload with a "query" field.
    Returns the generated top 3 similar queries without actually creating an image.
    """
    data = request.json
    db_session = SessionLocal()
    try:
        # Validate the request
        if not data or "query" not in data:
            return jsonify({"error": "Request must include a 'query' field"}), 400
        
        query = data["query"]
        
        # Generate embedding for the query
        question_embedding = chatgpt_api.get_openai_embedding(query)
        
        # Query ChromaDB
        results = collection.query(
            query_embeddings=[question_embedding],
            n_results=1,  # Get top 3 results
            where={"id": {"$ne": "none"}},
            include=["documents", "distances"]
        )
        
        # Process results
        if "documents" not in results or not results["documents"]:
            return jsonify({"error": "No relevant documents found in vector database."}), 404
        
        retrieved_docs = results["documents"][0]
        distances = results["distances"][0]
        
        # Create a list of document results with separate fields
        docs_results = []
        for i, doc in enumerate(retrieved_docs):
            docs_results.append({
                "document": doc,
                "distance": distances[i]
            })
        
        # Return the results with each document as a separate entry
        return jsonify({
            "query": query,
            "results": docs_results
        }), 200
        
    except Exception as e:
        logging.error(f"Error in test-image-prompt: {str(e)}")
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3002)