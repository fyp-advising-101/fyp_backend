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
from media_gen.apis.novita_api import NovitaAI 
from shared.apis.chatgpt_api import ChatGptApi
from datetime import timedelta
import datetime
import random
from chromadb import HttpClient
import logging

#Set up Azure Key Vault credentials
key_vault = AzureKeyVault()
IMAGINE_API_KEY = key_vault.get_secret("IMAGINE-API-KEY")
OPENAI_API_KEY = key_vault.get_secret("OPENAI-API-KEY")
NOVITA_API_KEY = key_vault.get_secret("NOVITA-API-KEY")
AZURE_STORAGE_CONNECTION_STRING =key_vault.get_secret("posting-connection-key")

# Initialize NovitaAI and ChatGPT API instances
novita = NovitaAI(NOVITA_API_KEY)
chatgpt_api = ChatGptApi(api_key=OPENAI_API_KEY, model="gpt-4o-mini")
azureBlob = AzureBlobManager(AZURE_STORAGE_CONNECTION_STRING)
# Initialize the vector database client and get the collection
vector_client = HttpClient(host='20.203.61.164', port=8000)
collection = vector_client.get_collection(name="aub_embeddings")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)

def validate_request(data):
    if not isinstance(data, dict):
        return "Invalid JSON format"
    if "context" not in data or "style" not in data:
        return "Missing required fields: 'context' and 'style'"
    if not isinstance(data["context"], str) or not isinstance(data["style"], str):
        return "Invalid data type for 'context' or 'style'"
    return None

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
        if job.task_name.lower() != "create media" or job.status != 1:
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
        prompt_text = selected_option.prompt_text
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
        prompt = chatgpt_api.generate_image_generation_prompt(
            f"Prompt: {prompt_text}\nContext: {context}\nOriginal Question: {chroma_query}"
        )
        # Step 6: Generate a More Detailed AI Image Prompt Using ChatGPT
        prompt = chatgpt_api.generate_image_generation_prompt(
            f"Prompt: {prompt_text}\nContext: {context}\nOriginal Question: {chroma_query}"
        )

        # Step 7: Ask ChatGPT to Recommend a Style
        allowed_styles = ["realistic", "anime", "flux-schnell", "flux-dev-fast", "flux-dev", "imagine-turbo"]
        style_prompt = f"""
        Based on this image generation prompt:
        ---
        {prompt}
        ---
        Select the most appropriate style from this list: {allowed_styles}.
        Only return the style name, nothing else.
        """

        # Call ChatGPT API to get the style recommendation
        logging.info("Style prompt: %s", style_prompt)
        recommended_style = chatgpt_api.get_completion(style_prompt).strip()
        logging.info("Recommended style: %s", recommended_style)

        # Validate the response from ChatGPT
        if recommended_style not in allowed_styles:
            recommended_style = "realistic"  # Default fallback if ChatGPT gives an invalid style

        # Step 8: Generate the Image Using ImagineArtAI
        
        imagine = ImagineArtAI(api_key=IMAGINE_API_KEY)
        try:
            logging.info("Calling ImagineArtAI.generate_image with style: %s", recommended_style)
            image_path = imagine.generate_image(prompt, style=recommended_style)
            logging.info("Image generated at path: %s", image_path)
        except Exception as e:
            logging.exception("Error while generating image")
            raise


       
        # Step 9: Upload the Generated Image to Azure Blob Storage
        safe_category = media_gen_option.category.lower().replace(" ", "_")

        # Add the category as part of the filename
        upload_result = azureBlob.upload_file(image_path, f"{safe_category}/image", "image/png")

        media_blob_url = upload_result.get("blob_url")

        caption = chatgpt_api.generate_caption(context)

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
            "prompt_text": selected_option.prompt_text,  
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

@app.route("/generate-video", methods=["POST"])
@app.route("/generate-video/<int:job_id>", methods=["POST"])
def generate_video(job_id):
    """
    Generate a video using NovitaAI.
    - Retrieves the media category and relevant context.
    - Uses ChromaDB to fetch the best-matching document.
    - Uses ChatGPT to generate an improved video prompt.
    - Uses ChatGPT to determine the most appropriate video style.
    - Sends the request to NovitaAI to generate the video.
    """

    db_session = SessionLocal()
    job = None

    try:
        # Step 1: Query the Job by ID
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")

        # Verify that the job has the correct task type and status
        if job.task_name.lower() != "create media" or job.status != 1:
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
            n_results=1,  # Get the best match
            where={"id": {"$ne": "none"}}  # Ensure we're not matching empty results
        )

        # Step 5: Validate the Retrieved Documents
        if "documents" not in results or not results["documents"]:
            raise Exception("No relevant documents found in vector database.")

        retrieved_docs = results["documents"][0]
        context = "\n".join(retrieved_docs) if retrieved_docs else "No context available."

        # Step 6: Generate a More Detailed AI Video Prompt Using ChatGPT
        video_prompt = chatgpt_api.generate_video_generation_prompt(
            f"Prompt: {prompt_text}\nContext: {context}\nOriginal Question: {chroma_query}"
        )


        # Convert generated prompt into the required format for NovitaAI
        prompts = [
            {"frames": 32, "prompt": segment} for segment in video_prompt.split(". ") if segment
        ]

        model_name = "darkSushiMixMix_225D_64380.safetensors"  # Default model name

        # Step 7: Send request to NovitaAI to generate the video
        task_id = novita.generate_video(model_name, prompts)

        if not task_id:
            raise Exception("Failed to generate video")

        # Step 8: Update the Current Job Status
        job.status = 2
        job.updated_at = datetime.datetime.now().date()
        db_session.commit()

        # Step 9: Store the Video Metadata in MediaAsset
        new_asset = MediaAsset(
            media_blob_url=None,  # URL will be updated when video is ready
            caption=context,
            media_type='video'
        )
        db_session.add(new_asset)
        db_session.commit()

        # Step 10: Create a New Job for posting the video
        insta_job = Job(
            task_name="post video instagram",
            task_id=new_asset.id,
            scheduled_date=(datetime.datetime.now() - timedelta(days=1)).date(),
            status=0,
            error_message=None,
            created_at=datetime.datetime.now().date(),
            updated_at=datetime.datetime.now().date()
        )
        db_session.add(insta_job)

        whats_job = Job(
            task_name="post video whatsapp",
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
            "prompt_text": selected_option.prompt_text,
            "category": media_gen_option.category,
            "job_id": job.id,
            "insta_job_id": insta_job.id,
            "whats_job_id": whats_job.id,
            "task_id": task_id,
          
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()


@app.route("/video-status/<task_id>", methods=["GET"])
def video_status(task_id):
    """
    Flask route to check the status of a video generation request.
    If video generation is complete, returns the video URL.
    """
    video_url = novita.get_video_status(task_id)

    if video_url:
        return jsonify({"status": "success", "video_url": video_url})
    else:
        return jsonify({"status": "failed or processing"}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3002)