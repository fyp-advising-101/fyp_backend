from flask import Flask, request
import requests
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os, sys
from chromadb import HttpClient
import openai
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from whatsapp.database import db
from subscriptionManager import subscribe_user, unsubscribe_user

app = Flask(__name__)

VAULT_URL = "https://advising101vault.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)
WEBHOOK_VERIFY_TOKEN = client.get_secret("WHATSAPP-WEBHOOK-VERIFY-TOKEN").value
GRAPH_API_TOKEN = client.get_secret("INSTAGRAM-ACCESS-TOKEN").value
openai.api_key = openai_api_key = client.get_secret('OPENAI-API-KEY').value

mysql_password = client.get_secret("DB-PASSWORD").value
ssl_cert = client.get_secret("DigiCert-CA-Cert").value
cert = "-----BEGIN CERTIFICATE-----\n" + '\n'.join([ssl_cert[i:i+64] for i in range(0, len(ssl_cert), 64)]) + "\n-----END CERTIFICATE-----"
os.makedirs('tmp', exist_ok=True)
cert_path = "./tmp/DigiCertGlobalRootCA.crt.pem"
with open(cert_path, "w") as f:
    f.write(cert)

app.config["SQLALCHEMY_DATABASE_URI"] = f'mysql+pymysql://advisor:{mysql_password}@mysqladvising101.mysql.database.azure.com:3306/fyp_db?ssl_ca={cert_path}'
db.init_app(app)

client = HttpClient(host='vectordb.bluedune-c06522b4.uaenorth.azurecontainerapps.io', port=80)
collection = client.get_collection(name="aub_embeddings")

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Define the log message format
    datefmt="%Y-%m-%d %H:%M:%S",  # Define the date format
)

def get_openai_embedding(text):
    response = openai.embeddings.create(input=text, model="text-embedding-3-large")
    return response.data[0].embedding

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
        category = split_message[1].lower()
        if split_message[0].lower() == "subscribe":
            result = subscribe_user(user_number, category)
            reply_to_user(business_phone_number_id, user_number, result[0], message_id)
            return result
        
        if split_message[0].lower() == "unsubscribe":
            result = unsubscribe_user(user_number, category)
            reply_to_user(business_phone_number_id, user_number, result[0], message_id)
            return result
        
        # Send message to gpt
        chatbot_response = get_response_from_gpt(message_text)
        
        # Send reply
        reply_to_user(business_phone_number_id, user_number, chatbot_response, message_id)
    
    return "Replied to Message", 200

def get_response_from_gpt(message_text):    
    embeddings = get_openai_embedding(message_text)
    results = collection.query(
        embeddings, n_results=30,  
        where={"id": {"$ne": "none"}}
        )
    retrieved_docs = results["documents"][0] 
    context = "\n".join(retrieved_docs)
    prompt = f"""You are an AI assistant answering questions about a university.

    Context:
    {context}

    Question: {message_text}
    Answer:
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}]
    )

    chatbot_response = response.choices[0].message.content
    
    return chatbot_response

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
