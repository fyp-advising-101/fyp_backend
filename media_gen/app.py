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
from shared.apis.chatgpt_api import ChatGptApi
from dotenv import load_dotenv
import json
import datetime


from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

#Set up Azure Key Vault credentials
VAULT_URL = "https://advising101vault.vault.azure.net"  
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)

#Fetch secrets from Azure Key Vault
IMAGINE_API_KEY = client.get_secret("IMAGINE-API-KEY").value
OPENAI_API_KEY = client.get_secret("OPENAI-API-KEY").value

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)
load_dotenv()

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

    # Return the API response and image path (or null if an error occurred)
    return jsonify({
        "response": response_data,
        "image_path": image_path
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3002)