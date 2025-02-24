from flask import Flask, request
import requests
import logging
import os, sys
from chromadb import HttpClient
import openai

# Add the parent directory to sys.path to import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from whatsapp.database import db
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

mysql_password = vault.get_secret("DB-PASSWORD")
ssl_cert = vault.get_secret("DigiCert-CA-Cert")

chatgpt_api = ChatGptApi(api_key=openai_api_key, model="gpt-4")

# Prepare certificate file for MySQL connection
cert = "-----BEGIN CERTIFICATE-----\n" + '\n'.join([ssl_cert[i:i+64] for i in range(0, len(ssl_cert), 64)]) + "\n-----END CERTIFICATE-----"
os.makedirs('tmp', exist_ok=True)
cert_path = "./tmp/DigiCertGlobalRootCA.crt.pem"
with open(cert_path, "w") as f:
    f.write(cert)

# Configure the SQLAlchemy database URI using the retrieved MySQL password and certificate
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f'mysql+pymysql://advisor:{mysql_password}@mysqladvising101.mysql.database.azure.com:3306/fyp_db'
    f'?ssl_ca={cert_path}'
)
db.init_app(app)

# Initialize the vector database client and get the collection
vector_client = HttpClient(host='vectordb.bluedune-c06522b4.uaenorth.azurecontainerapps.io', port=80)
collection = vector_client.get_collection(name="aub_embeddings")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def reply_to_user(business_phone_number_id, user_number, reply, message_id):
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
