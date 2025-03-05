from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.apis.azure_key_vault import AzureKeyVault
from shared.apis.azure_blob import AzureBlobManager
from apis.instagram_api import InstagramAPI
from shared.models.job import Job
from shared.database import engine, SessionLocal
from sqlalchemy.sql import text
from shared.apis.chatgpt_api import ChatGptApi
from shared.models.media_asset import MediaAsset
from datetime import timedelta
import datetime

#Set up Azure Key Vault credentials
key_vault = AzureKeyVault()
APP_ID = key_vault.get_secret("APP-ID")
APP_SECRET = key_vault.get_secret("APP-SECRET")
ACCESS_TOKEN = key_vault.get_secret("INSTAGRAM-ACCESS-TOKEN")
INSTAGRAM_USER_ID = key_vault.get_secret("INSTAGRAM-USER-ID")
AZURE_STORAGE_CONNECTION_STRING =key_vault.get_secret("posting-connection-key")

# Initialize NovitaAI and ChatGPT API instances
azureBlob = AzureBlobManager(AZURE_STORAGE_CONNECTION_STRING)
instagram_api = InstagramAPI(APP_ID, APP_SECRET, ACCESS_TOKEN, INSTAGRAM_USER_ID, azureBlob)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route("/post-image/<int:job_id>", methods=["POST"])
def post_image_route(job_id):
    """
    Route to post an image to Instagram.
    - Expects a JSON payload with an optional "caption".
    - Queries the job with the given job_id and verifies that its task_name is "post image" and its status is 1.
    - Computes the public blob URL using the Azure Blob Manager and the job's task_id (which holds the blob identifier).
    - Calls the Instagram API to post the image.
    - Updates the job's status to 2 and commits the changes.
    In case of an error, updates the job status to -1 and records the error message.
    """
    db_session = SessionLocal()
    job = None
    try:
        # Query the job by job_id
        job = db_session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise Exception("Job not found")
        
        
        # Validate that the job is for posting an image and is pending (status 1)
        if job.task_name.lower() != "post image instagram" or job.status != 1:
            raise Exception("Job is not valid for posting an image")

        asset_id = job.task_id
        asset = db_session.query(MediaAsset).filter_by(id=asset_id).first()
        if not asset:
            raise Exception("Asset not found")
        
        if not asset.media_blob_url or not asset.caption:
            raise Exception("No URL or Caption for this asset")

        instagram_api.refresh_access_token()

        # Call the Instagram API to upload and publish the picture
        instagram_api.upload_and_publish_pic(asset.media_blob_url, caption=asset.caption)
        
        # Update the job status to indicate it has been processed (status 2)
        job.status = 2
        job.updated_at = datetime.datetime.now().date()
        db_session.commit()

        return jsonify({"message": "Image posted successfully", "job_id": job.id}), 200

    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3003)