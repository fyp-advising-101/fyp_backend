import requests
import time
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient
from datetime import datetime


class InstagramAPI:
    def __init__(self, app_id, app_secret, short_lived_token, instagram_user_id, blob_service_client, container_name):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = short_lived_token
        self.instagram_user_id = instagram_user_id
        self.blob_service_client = blob_service_client
        self.container_name = container_name

    def get_blob_url(self, blob_name):
        """
        Generates a publicly accessible URL for a blob stored in Azure Storage.
        """
        return f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"

    def get_latest_blob(self, file_type):
        """
        Retrieves the most recently uploaded image or video from Azure Blob Storage.
        file_type should be 'image' or 'video'.
        """
        blob_list = self.blob_service_client.get_container_client(self.container_name).list_blobs()

        # Filter blobs by file type (store images in "images/" and videos in "videos/")
        prefix = f"{file_type}s/"  # 'images/' or 'videos/'
        blobs = [blob for blob in blob_list if blob.name.startswith(prefix)]

        if not blobs:
            print(f"No {file_type}s found in Azure Blob Storage.")
            return None

        # Sort blobs by last modified time (latest first)
        blobs.sort(key=lambda blob: blob.last_modified, reverse=True)

        latest_blob = blobs[0]  # Get the latest file
        print(f"Latest {file_type}: {latest_blob.name}")

        return latest_blob.name  # Return the blob name (relative path)

    def refresh_access_token(self):
        url = "https://graph.facebook.com/v20.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': self.access_token
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            print("Access token refreshed successfully.")
        else:
            print(f"Error refreshing token: {response.status_code}, {response.text}")

    def upload_and_publish_pic(self, caption="Automated post via Instagram API"):
        """
        Automatically fetches the latest image from Azure Blob Storage and uploads it to Instagram.
        """
        latest_blob_name = self.get_latest_blob("image")
        if not latest_blob_name:
            print("No image found to upload.")
            return

        # Generate Azure Blob public URL
        image_url = self.get_blob_url(latest_blob_name)
        print(f"Uploading image from Azure Blob: {image_url}")

        # Send request to Instagram API
        url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media"
        params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token
        }
        response = requests.post(url, params=params)

        if response.status_code == 200:
            media_object_id = response.json().get('id')
            print(f"Media object created with ID: {media_object_id}")
        else:
            print(f"Error creating media object: {response.status_code}, {response.text}")
            return

        # Wait for processing
        print("Waiting for media processing...")
        time.sleep(10)

        # Publish media
        publish_url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media_publish"
        publish_params = {
            "creation_id": media_object_id,
            "access_token": self.access_token
        }
        publish_response = requests.post(publish_url, params=publish_params)

        if publish_response.status_code == 200:
            print("Media successfully published!")
        else:
            print(f"Error publishing media: {publish_response.status_code}, {publish_response.text}")

    def upload_and_publish_video(self, caption="Automated video post via Instagram API"):
        """
        Automatically fetches the latest video from Azure Blob Storage and uploads it to Instagram.
        """
        latest_blob_name = self.get_latest_blob("video")
        if not latest_blob_name:
            print("No video found to upload.")
            return

        # Generate Azure Blob public URL
        video_url = self.get_blob_url(latest_blob_name)
        print(f"Uploading video from Azure Blob: {video_url}")

        # Step 1: Create video media object
        url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media"
        params = {
            "video_url": video_url,
            "caption": caption,
            "media_type": "REELS",
            "access_token": self.access_token
        }
        response = requests.post(url, params=params)

        if response.status_code == 200:
            media_object_id = response.json().get('id')
            print(f"Video media object created with ID: {media_object_id}")
        else:
            print(f"Error creating video media object: {response.status_code}, {response.text}")
            return

        # Step 2: Check status of the video upload
        print("Waiting for video processing...")
        while True:
            status_url = f"https://graph.facebook.com/v20.0/{media_object_id}?fields=status_code"
            status_params = {"access_token": self.access_token}
            status_response = requests.get(status_url, params=status_params)

            if status_response.status_code == 200:
                status = status_response.json().get("status_code")
                if status == "FINISHED":
                    print("Video processing complete!")
                    break
                else:
                    print("Video is still processing... Checking again in 10 seconds.")
                    time.sleep(10)
            else:
                print(f"Error checking video status: {status_response.status_code}, {status_response.text}")
                return

        # Step 3: Publish the video
        publish_url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media_publish"
        publish_params = {
            "creation_id": media_object_id,
            "access_token": self.access_token
        }
        publish_response = requests.post(publish_url, params=publish_params)

        if publish_response.status_code == 200:
            print("Video successfully published!")
        else:
            print(f"Error publishing video: {publish_response.status_code}, {publish_response.text}")


if __name__ == "__main__":
    # Initialize Azure Key Vault
    VAULT_URL = "https://advising101vault.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=VAULT_URL, credential=credential)

    # Retrieve secrets
    APP_ID = client.get_secret("APP-ID").value
    APP_SECRET = client.get_secret("APP-SECRET").value
    ACCESS_TOKEN = client.get_secret("INSTAGRAM-ACCESS-TOKEN").value
    INSTAGRAM_USER_ID = client.get_secret("INSTAGRAM-USER-ID").value
    AZURE_STORAGE_CONNECTION_STRING = client.get_secret("posting-connection-key").value
    AZURE_CONTAINER_NAME = "media-gen"

    # Initialize Azure Blob Storage
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

    # Initialize Instagram API with Blob Storage
    instagram_api = InstagramAPI(
        APP_ID, APP_SECRET, ACCESS_TOKEN, INSTAGRAM_USER_ID, 
        blob_service_client, AZURE_CONTAINER_NAME
    )

    # Refresh access token
    instagram_api.refresh_access_token()
    
    # Automatically upload and publish the latest image
    instagram_api.upload_and_publish_pic()

    # Automatically upload and publish the latest video
    instagram_api.upload_and_publish_video()
