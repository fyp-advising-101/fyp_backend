from flask import Flask, request
import requests
import logging
import os, sys
from chromadb import HttpClient
import openai

# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from subscriptionManager import subscribe_user, unsubscribe_user
from shared.apis.chatgpt_api import ChatGptApi  # Our ChatGPT API class
from shared.apis.azure_key_vault import AzureKeyVault  # Our Key Vault access class

app = Flask(__name__)

# Initialize Azure Key Vault using the AzureKeyVault class
vault = AzureKeyVault()  # uses default vault URL: "https://advising101vault.vault.azure.net"

# Retrieve secrets using the vault class
WEBHOOK_VERIFY_TOKEN = vault.get_secret("WHATSAPP-WEBHOOK-VERIFY-TOKEN")
GRAPH_API_TOKEN = vault.get_secret("INSTAGRAM-ACCESS-TOKEN")
openai_api_key = vault.get_secret("OPENAI-API-KEY")

chatgpt_api = ChatGptApi(api_key=openai_api_key, model="gpt-4")


# Initialize the vector database client and get the collection
vector_client = HttpClient(host='vectordb.bluedune-c06522b4.uaenorth.azurecontainerapps.io', port=80)
collection = vector_client.get_collection(name="aub_embeddings")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def reply_to_user(business_phone_number_id, user_number, reply, message_id):
    """
    Sends a reply to a user via WhatsApp using the Meta Graph API.
    
    This function sends a message from the business's WhatsApp number to a user,
    replying to a specific message the user sent.
    
    Args:
        business_phone_number_id (str): The ID of the business's WhatsApp phone number.
        user_number (str): The phone number of the recipient.
        reply (str): The message content to be sent as a reply.
        message_id (str): The ID of the message being replied to.
    
    Returns:
        None
    """
    requests.post(
        f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
        headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": user_number,
            "text": {"body": reply},
            "context": {"message_id": message_id}
        }
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
    logging.info("Incoming webhook message:" + str(data))
    
    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    message_text = message.get("text", {}).get("body", "")
    
    if message and message.get("type") == "text":
        business_phone_number_id = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
        user_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        message_id = message['id']

        # Mark message as read
        requests.post(
            f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
            headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
        )

        split_message = message_text.split(' ', 1)
        category = split_message[1].lower() if len(split_message) > 1 else ""
        if split_message[0].lower() == "subscribe":
            result = subscribe_user(user_number, category)
            reply_to_user(business_phone_number_id, user_number, result[0], message_id)
            return result
        
        if split_message[0].lower() == "unsubscribe":
            result = unsubscribe_user(user_number, category)
            reply_to_user(business_phone_number_id, user_number, result[0], message_id)
            return result
        
        # Use the ChatGptApi instance to generate a GPT response
        chatbot_response = chatgpt_api.get_response_from_gpt(message_text, collection)
        
        # Reply to the user with the chatbot's response
        reply_to_user(business_phone_number_id, user_number, chatbot_response, message_id)
    
    return "Replied to Message", 200

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
