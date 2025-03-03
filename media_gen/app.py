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
from media_gen.apis.novita_api import NovitaAI 
from shared.apis.chatgpt_api import ChatGptApi
from datetime import timedelta
import datetime
import random
from chromadb import HttpClient

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
vector_client = HttpClient(host='vectordb.bluedune-c06522b4.uaenorth.azurecontainerapps.io', port=80)
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

        # Step 7: Generate the Image Using ImagineArtAI
        imagine = ImagineArtAI(api_key=IMAGINE_API_KEY)
        image_path = imagine.generate_image(prompt)

        # Step 8: Upload the Generated Image to Azure Blob Storage
        upload_result = azureBlob.upload_file(image_path, "image", "image/png")
        blob_url = upload_result.get("blob_url")

        # Step 9: Update the Current Job Status
        job.status = 2
        job.updated_at = datetime.datetime.now().date()
        db_session.commit()

        # Step 10: Create a New Job with Task Name "post image"
        new_job = Job(
            task_name="post image",
            task_id=blob_url,
            scheduled_date=(datetime.datetime.now() - timedelta(days=1)).date(),
            status=0,
            error_message=None,
            created_at=datetime.datetime.now().date(),
            updated_at=datetime.datetime.now().date()
        )
        db_session.add(new_job)
        db_session.commit()

        return jsonify({
            "blob_url": blob_url,
            "chroma_query": selected_option.chroma_query,
            "category": media_gen_option.category,  
            "job_id": job.id,
            "new_job_id": new_job.id
        }), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route("/generate-video", methods=["POST"])
def generate_video():
    """
    Flask route to generate a video using NovitaAI.
    Expects a JSON payload with 'context' and 'style'.
    Uses ChatGPT to generate a structured prompt.
    """
    data = request.get_json()
    
    validation_error = validate_request(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    context = data["context"]
    style = data["style"]

    # Generate structured prompts using ChatGPT
    generated_prompt = chatgpt_api.generate_video_generation_prompt(context, style)

    if not generated_prompt:
        return jsonify({"error": "Failed to generate a structured prompt from the context"}), 500
    else:
        print("Generated video prompt:", generated_prompt)

    # Convert generated prompt into the required format for NovitaAI
    prompts = [
        {"frames": 32, "prompt": segment} for segment in generated_prompt.split(". ") if segment
    ]

    model_name = "darkSushiMixMix_225D_64380.safetensors"  # Default model name

    # Send request to NovitaAI to generate the video
    task_id = novita.generate_video(model_name, prompts)

    if task_id:
        return jsonify({"message": "Video generation started", "task_id": task_id})
    else:
        return jsonify({"error": "Failed to generate video"}), 500


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