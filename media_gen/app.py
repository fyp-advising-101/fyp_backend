from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.jobScheduler import JobScheduler
from shared.models.scrapeTarget import ScrapeTarget
from shared.database import engine, SessionLocal
from sqlalchemy.sql import text
from media_gen.apis.imagine_api import ImagineArtAI
from media_gen.apis.novita_api import NovitaAI 
from shared.apis.chatgpt_api import ChatGptApi
from dotenv import load_dotenv
import json
import datetime


from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
import uuid
#Set up Azure Key Vault credentials
VAULT_URL = "https://advising101vault.vault.azure.net"  
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)

#Fetch secrets from Azure Key Vault
IMAGINE_API_KEY = client.get_secret("IMAGINE-API-KEY").value
OPENAI_API_KEY = client.get_secret("OPENAI-API-KEY").value
NOVITA_API_KEY = client.get_secret("NOVITA-API-KEY").value

# Initialize NovitaAI and ChatGPT API instances
novita = NovitaAI(NOVITA_API_KEY)
chatgpt = ChatGptApi(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)
load_dotenv()


# Fetch Azure Storage credentials from Key Vault
AZURE_STORAGE_CONNECTION_STRING = client.get_secret("posting-connection-key").value
AZURE_CONTAINER_NAME = "media-gen"

# Initialize Azure Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def upload_to_azure(file_path, file_type="image"):
    """
    Uploads a file to Azure Blob Storage and returns the public URL.
    """
    try:
        # Generate a unique blob name
        blob_name = f"{file_type}s/{uuid.uuid4().hex}_{os.path.basename(file_path)}"
        
        # Get the blob client
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=blob_name)

        # Upload the file
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        # Generate a public URL
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{blob_name}"
        return blob_url
    except Exception as e:
        print(f"Azure Upload Error: {str(e)}")
        return None
    
def validate_request(data):
    if not isinstance(data, dict):
        return "Invalid JSON format"
    if "context" not in data or "style" not in data:
        return "Missing required fields: 'context' and 'style'"
    if not isinstance(data["context"], str) or not isinstance(data["style"], str):
        return "Invalid data type for 'context' or 'style'"
    return None


@app.route("/generate-image", methods=["POST"])
def generate_image_route():
    """
    Flask route to generate an image using ImagineArt AI.
    Expects a JSON payload with 'context' and 'style'.
    Returns a JSON response with the API response and image path.
    """
    data = request.get_json()
    validation_error = validate_request(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400
    
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    context = data.get("context")
    style = data.get("style")

    if not context or not style:
        return jsonify({"error": "Missing required parameters: 'context' and 'style'"}), 400
    
    chatgpt = ChatGptApi(api_key=OPENAI_API_KEY, model="gpt-4o-mini")

    generated_prompt = chatgpt.generate_image_generation_prompt(context)
   
    if not generated_prompt:
        return jsonify({"error": "Failed to generate a prompt from the context"}), 500

    else:
        print("Generated image prompt:", generated_prompt)

    imagine = ImagineArtAI(api_key=IMAGINE_API_KEY)

    response_data, image_path = imagine.generate_image(generated_prompt, style)

    if image_path:
        # Upload to Azure Blob Storage
        image_url = upload_to_azure(image_path, "image")
        if image_url:
            return jsonify({"response": response_data, "image_url": image_url})
        else:
            return jsonify({"error": "Failed to upload image to Azure"}), 500
    else:
        return jsonify({"error": "Image generation failed"}), 500
   



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
    generated_prompt = chatgpt.generate_video_generation_prompt(context, style)

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