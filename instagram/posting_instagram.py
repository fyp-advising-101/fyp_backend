import requests
import time
import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class InstagramAPI:
    def __init__(self, app_id, app_secret, short_lived_token, instagram_user_id):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = short_lived_token
        self.instagram_user_id = instagram_user_id

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

    def upload_and_publish_pic(self, image_url, caption="Automated post via Instagram API"):
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

    def upload_and_publish_video(self, video_url, caption="Automated video post via Instagram API"):
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

# Usage Example
if __name__ == "__main__":
    VAULT_URL = "https://advising101vault.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=VAULT_URL, credential=credential)

    APP_ID = client.get_secret("APP-ID").value
    APP_SECRET = client.get_secret("APP-SECRET").value
    ACCESS_TOKEN = client.get_secret("INSTAGRAM-ACCESS-TOKEN").value
    INSTAGRAM_USER_ID = client.get_secret("INSTAGRAM-USER-ID").value
    

    instagram_api = InstagramAPI(APP_ID, APP_SECRET, ACCESS_TOKEN, INSTAGRAM_USER_ID)

    # Refresh access token
    instagram_api.refresh_access_token()
    
    # Upload and publish a new post
    #test_image_url = "https://i.imgur.com/q4EPE4Q.jpeg"
    #instagram_api.upload_and_publish_pic(test_image_url, caption="This is an automated test post!")
    # Upload and publish a new video
    test_video_url = "https://www.dropbox.com/scl/fi/g5qxeicprnvrtp6143zte/generated_video.mp4?rlkey=05cjmy1bpmnc1p1f16w6ae9j4&st=5dnuxyfs&raw=1"
    instagram_api.upload_and_publish_video(test_video_url, caption="This is an automated video post!")
