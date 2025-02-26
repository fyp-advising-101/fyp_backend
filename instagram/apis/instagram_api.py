import requests
import time
from shared.apis.azure_blob import AzureBlobManager
import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class InstagramAPI:
    def __init__(self, app_id, app_secret, short_lived_token, instagram_user_id, azure_blob_manager):
        """
        Initializes the InstagramAPI client.

        Args:
            app_id (str): Instagram App ID.
            app_secret (str): Instagram App Secret.
            short_lived_token (str): The initial short-lived access token.
            instagram_user_id (str): Instagram User ID.
            azure_blob_manager (AzureBlobManager): Instance of AzureBlobManager for handling media uploads.
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = short_lived_token
        self.instagram_user_id = instagram_user_id
        self.azure_blob_manager = azure_blob_manager

    def refresh_access_token(self):
        """
        Refreshes the Instagram access token.
        Raises an exception if the request fails.
        """
        url = "https://graph.facebook.com/v20.0/oauth/access_token"
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': self.access_token
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()

            new_access_token = response.json().get('access_token')
            if not new_access_token:
                raise ValueError("No access token returned in response.")

            self.access_token = new_access_token
            logging.info("Access token refreshed successfully.")

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while refreshing access token: {e}")
            raise
        except ValueError as e:
            logging.error(f"Invalid response format while refreshing token: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while refreshing token: {e}")
            raise

    def upload_and_publish_pic(self, blob_url, caption="Automated post via Instagram API"):
        """
        Uploads an image to Instagram and publishes it.

        Args:
            blob_url (str): Public URL of the image stored in Azure Blob Storage.
            caption (str): Caption for the Instagram post.

        Raises:
            Exception: If any step fails, it raises an exception.
        """
        logging.info(f"Uploading image from Azure Blob: {blob_url}")

        # Step 1: Create the media object on Instagram
        url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media"
        params = {
            "image_url": blob_url,
            "caption": caption,
            "access_token": self.access_token
        }

        try:
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()

            media_object_id = response.json().get('id')
            if not media_object_id:
                raise ValueError("No media object ID returned in response.")

            logging.info(f"Media object created with ID: {media_object_id}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while creating media object: {e}")
            raise
        except ValueError as e:
            logging.error(f"Invalid response format while creating media object: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while creating media object: {e}")
            raise

        # Wait for media processing
        logging.info("Waiting for media processing...")
        time.sleep(10)

        # Step 2: Publish the media
        publish_url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media_publish"
        publish_params = {
            "creation_id": media_object_id,
            "access_token": self.access_token
        }

        try:
            publish_response = requests.post(publish_url, params=publish_params, timeout=10)
            publish_response.raise_for_status()

            logging.info("Media successfully published!")

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while publishing media: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while publishing media: {e}")
            raise

    def upload_and_publish_video(self, blob_url, caption="Automated video post via Instagram API"):
        """
        Uploads a video to Instagram using the provided blob URL.
        
        :param blob_url: Public URL of the video stored in Azure Blob Storage.
        :param caption: Caption for the Instagram post.
        """
        print(f"Uploading video from Azure Blob: {blob_url}")

        # Step 1: Create the video media object on Instagram
        url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}/media"
        params = {
            "video_url": blob_url,
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

        # Step 2: Check the status of the video upload
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


