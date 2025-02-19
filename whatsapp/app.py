from flask import Flask, request
import requests
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import os
from chromadb import HttpClient
import openai

app = Flask(__name__)

VAULT_URL = "https://advising101vault.vault.azure.net"
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)
WEBHOOK_VERIFY_TOKEN = client.get_secret("WHATSAPP-WEBHOOK-VERIFY-TOKEN").value
GRAPH_API_TOKEN = client.get_secret("INSTAGRAM-ACCESS-TOKEN").value
openai.api_key = openai_api_key = client.get_secret('OPENAI-API-KEY').value

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

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info("Incoming webhook message:" + str(data))
    
    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    
    if message and message.get("type") == "text":
        business_phone_number_id = data["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
        
        # Send message to gpt
        chatbot_response = get_response_from_gpt(data)
        
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
    
    
    if 'messages' in data['entry'][0]['changes'][0]['value']:
      business_phone_number_id = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
      message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
      user_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
      # Send reply
      requests.post(
          f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
          headers={"Authorization": f"Bearer {GRAPH_API_TOKEN}"},
          json={
              "messaging_product": "whatsapp",
              "to": user_number,
              "text": {"body": chatbot_response},
              "context": {"message_id": message["id"]}
          }
      )
    
    return "Message Received", 200

def get_response_from_gpt(data):
    message = data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0]
    message_text = message.get("text", {}).get("body", "") 
    
    logging.info("MESSAGE FROM USER: " + str(message_text))
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
