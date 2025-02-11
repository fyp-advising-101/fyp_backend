from flask import Flask, request
import requests
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os

app = Flask(__name__)

VAULT_URL = "https://advising101vault.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)
WEBHOOK_VERIFY_TOKEN = client.get_secret("WHATSAPP-WEBHOOK-VERIFY-TOKEN").value
GRAPH_API_TOKEN = client.get_secret("INSTAGRAM-ACCESS-TOKEN").value


logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
    datefmt="%Y-%m-%d %H:%M:%S",  # Define the date format
)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info("Incoming webhook message:" + str(data))
    
    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    
    if message and message.get("type") == "text":
        business_phone_number_id = data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
        
        # Send message to gpt # TO DO
        #requests.post("https://marmalade-deciduous-router.glitch.me/mock_chatbot", json={"payload_from_user": data})
        
        # Mark message as read
        requests.post(
            f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
            headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message["id"]
            }
        )
    
    return "Message Received", 200

@app.route("/mock_chatbot", methods=["POST"])
def mock_chatbot():
    data = request.get_json()
    message = data.get("payload_from_user", {}).get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    message_text = message.get("text", {}).get("body", "")
    
    logging.info("MESSAGE FROM USER: " + str(message_text))
    chatbot_response = f"Response to your message '{message_text}':\n This is an example response from Advising101's chatbot"
    
    requests.post("https://marmalade-deciduous-router.glitch.me/reply_to_user", json={
        "chatbot_response": chatbot_response,
        "payload_from_user": data["payload_from_user"]
    })
    
    return "Chatbot Reply Obtained", 200

@app.route("/reply_to_user", methods=["POST"])
def reply_to_user():
    data = request.get_json()
    payload_from_user = data.get("payload_from_user", {})
    
    business_phone_number_id = payload_from_user.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
    message = payload_from_user.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    chatbot_response = data.get("chatbot_response", "")
    
    # Send reply
    requests.post(
        f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
        headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
        json={
            "messaging_product": "whatsapp",
            "to": message["from"],
            "text": {"body": chatbot_response},
            "context": {"message_id": message["id"]}
        }
    )
    
    return "Reply Sent", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        logging.info("Webhook verified successfully!")
        return challenge, 200
    else:
        return "Forbidden", 403

@app.route("/")
def home():
    return "<pre>Nothing to see here. Checkout README.md to start.</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
