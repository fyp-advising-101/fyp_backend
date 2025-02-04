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

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)
load_dotenv()
IMAGINE_ART_API_KEY = os.environ.get("IMAGINE_ART_API_KEY","vk-YBq8n4X3PjtAwTLYh2eH7eUNnCNymT42DEJ8d9pXPoE2BS9")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY","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")

@app.route("/generate-image", methods=["POST"])
def generate_image_route():
    """
    Flask route to generate an image using ImagineArt AI.
    Expects a JSON payload with 'context' and 'style'.
    Returns a JSON response with the API response and image path.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload provided"}), 400

    context = data.get("context")
    style = data.get("style")

    if not context or not style:
        return jsonify({"error": "Missing required parameters: 'context' and 'style'"}), 400
    
    print(OPENAI_API_KEY)

    chatgpt = ChatGptApi(api_key=OPENAI_API_KEY, model="gpt-4o")

    generated_prompt = chatgpt.generate_image_generation_prompt(context)

    if not generated_prompt:
        return jsonify({"error": "Failed to generate a prompt from the context"}), 500

    else:
        print("Generated image prompt:", generated_prompt)

    imagine = ImagineArtAI(api_key=IMAGINE_ART_API_KEY)

    response_data, image_path = imagine.generate_image(generated_prompt, style)

    # Return the API response and image path (or null if an error occurred)
    return jsonify({
        "response": response_data,
        "image_path": image_path
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3002)