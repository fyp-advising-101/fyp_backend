from flask import Flask, request, jsonify
import requests
import logging
import os, sys
from chromadb import HttpClient
import datetime

# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from subscriptionManager import subscribe_user, unsubscribe_user
from apis.whatsapp_api import WhatsAppAPI
from shared.apis.chatgpt_api import ChatGptApi  # Our ChatGPT API class
from shared.apis.azure_key_vault import AzureKeyVault  # Our Key Vault access class
from shared.models.job import Job
from shared.models.media_asset import MediaAsset
from shared.models.user_subscriptions import UserSubscriptions
from shared.database import SessionLocal

app = Flask(__name__)

# Initialize Azure Key Vault using the AzureKeyVault class
vault = AzureKeyVault()  # uses default vault URL: "https://advising101vault.vault.azure.net"

# Retrieve secrets using the vault class
WEBHOOK_VERIFY_TOKEN = vault.get_secret("WHATSAPP-WEBHOOK-VERIFY-TOKEN")
GRAPH_API_TOKEN = vault.get_secret("INSTAGRAM-ACCESS-TOKEN")
openai_api_key = vault.get_secret("OPENAI-API-KEY")

chatgpt_api = ChatGptApi(api_key=openai_api_key, model="gpt-4")
whatsapp_api = WhatsAppAPI(graph_api_token=GRAPH_API_TOKEN)

# Initialize the vector database client and get the collection
vector_client = HttpClient(host='vectordb.bluedune-c06522b4.uaenorth.azurecontainerapps.io', port=80)
collection = vector_client.get_collection(name="aub_embeddings")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@app.route("/", methods=["POST"])
def webhook():
    """
    Handles incoming WhatsApp webhook events.
    
    This function processes messages received via the WhatsApp Business API and responds accordingly.
    It supports the following commands:
    - "subscribe <category>": Subscribes the user to a specific category.
    - "unsubscribe <category>": Unsubscribes the user from a specific category.
    - Any other text: Processes the message using a chatbot API.
    
    The function also marks the message as read and sends a response back to the user.
    """
    data = request.get_json()
    logging.info("Incoming webhook message")
    
    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    message_text = message.get("text", {}).get("body", "")
    
    if message and message.get("type") == "text":
        business_phone_number_id = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
        user_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        message_id = message['id']

        # Mark message as read
        whatsapp_api.mark_message_as_read(message_id)

        split_message = message_text.split(' ', 1)
        category = split_message[1].lower() if len(split_message) > 1 else ""
        if split_message[0].lower() == "subscribe":
            result = subscribe_user(user_number, category)
            whatsapp_api.reply_to_user(user_number, result[0], message_id)
            return result
        
        if split_message[0].lower() == "unsubscribe":
            result = unsubscribe_user(user_number, category)
            whatsapp_api.reply_to_user(user_number, result[0], message_id)
            return result
        
        logging.info("Incoming message:" + message_text)
        # Use the ChatGptApi instance to generate a GPT response
        chatbot_response = chatgpt_api.get_response_from_gpt(message_text, collection)
        
        # Reply to the user with the chatbot's response
        whatsapp_api.reply_to_user(user_number, chatbot_response, message_id)
    
    return "Replied to Message", 200

@app.route("/post-image/<int:job_id>", methods=["POST"])
def post_image_whatsapp(job_id):
    """
    Route to post an image to WhatsApp.
    - Optionally accepts a JSON payload with a "category" to filter user subscriptions.
    - Queries the job with the given job_id and verifies that its task_name is "post image" and its status is 1.
    - Retrieves the media asset using the job's task_id.
    - Validates that the asset has both a media_blob_url and caption_blob_url.
    - Fetches user subscriptions for the provided (or default) category.
    - Calls the WhatsApp API to send a template message with the asset's details.
    - Updates the job's status to 2 and commits the changes.
    In case of an error, rolls back the transaction and returns an error message.
    """
    db_session = SessionLocal()
    try:
        # Query the job by job_id
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")
        
        # Validate that the job is for posting an image and is pending (status 1)
        if job.task_name.lower() != "post image whatsapp" or job.status != 1:
            raise Exception("Job is not valid for posting an image")
        
        # Retrieve the media asset using the job's task_id (asset id)
        asset_id = job.task_id
        asset = db_session.query(MediaAsset).filter_by(id=asset_id).first()
        if not asset:
            raise Exception("Asset not found")
        
        if not asset.media_blob_url or not asset.caption:
            raise Exception("Asset missing media blob URL or caption blob URL")
        
        # Get category from payload if provided, default to "sports"
        data = request.get_json() or {}
        category = data.get("category", "sports")
        
        # Query user subscriptions for the given category
        users = db_session.query(UserSubscriptions).filter(UserSubscriptions.category == category).all()
        if not users:
            raise Exception("No user subscriptions found for category: " + category)
        
        # Call the WhatsApp API to send the template message to each subscribed user
        for user in users:
            whatsapp_api.send_template_message(user.phone_number, category, asset.media_blob_url, asset.caption)
        
        # Update job status to indicate successful processing (status 2)
        job.status = 2
        job.updated_at = datetime.datetime.now().date()
        db_session.commit()
        
        return jsonify({"message": "Image posted successfully", "job_id": job.id}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

@app.route("/", methods=["GET"])
def verify_webhook():
    """
    Verifies the WhatsApp webhook during the setup process.
    
    When a GET request is received, this function checks if the mode and token match
    the expected values and returns the challenge token for verification.
    
    Returns:
        str: The challenge token if verification is successful.
        int: HTTP status code (200 for success, 403 for failure).
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        logging.info("Webhook verified successfully!")
        return challenge, 200
    else:
        return "Forbidden", 403

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
