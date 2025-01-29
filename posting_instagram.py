import requests
import time
import os

class InstagramAPI:
    def __init__(self, app_id, app_secret, short_lived_token, instagram_user_id):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = short_lived_token
        self.instagram_user_id = instagram_user_id

    def short_to_long_lived_token(self):
        url = "https://graph.instagram.com/access_token"
        params = {
            'grant_type': 'ig_exchange_token',
            'client_secret': self.app_secret,
            'access_token': self.access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            print(f"New long-lived token expires in {response.json().get('expires_in')} seconds.")
        else:
            print(f"Error generating long-lived token: {response.status_code}, {response.text}")

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

    def get_user_media(self, username, download_folder="pics"):
        url = f"https://graph.facebook.com/v20.0/{self.instagram_user_id}"
        params = {
            "fields": f"business_discovery.username({username}){{followers_count,media_count,media{{media_url}},follows_count}}",
            "access_token": self.access_token
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            print("User data retrieved:", data)

            os.makedirs(download_folder, exist_ok=True)

            for idx, media in enumerate(data['business_discovery']['media']['data']):
                image_url = media['media_url']
                file_path = os.path.join(download_folder, f"image_{idx + 1}.jpg")
                self.download_image(image_url, file_path)
        else:
            print(f"Error fetching media: {response.status_code}, {response.text}")

    @staticmethod
    def download_image(url, file_path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Image saved: {file_path}")
        else:
            print(f"Failed to download image from {url}")

    def upload_and_publish_pic(self, image_url, caption="Automated post via Instagram API"):
        # Step 1: Create media object
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

        # Step 2: Publish media object
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

# Usage Example
if __name__ == "__main__":
    app_id = '861942379371299'
    app_secret = '760999b7887a59c7bcb6a642e83d9c9a'
    short_lived_token = 'EAAMP7plW2yMBO7eFc3VMgi9awrZB1gI6OV8AuzDS2ir1UW5GWjutCiqbEfj7iVBmxPY8ug4CMCv8TeyOSFZA1Av3Q4ZC25P6qg1ZBeNiZB6QGvxYLoW3EpMTJSsDZB7g1zdxTo5TmOwzSb1FYabwDyFpu8z0dTBZAZAcZATpKj9ktEiHqb1PnxIZC4ZClPSXZAk3O1MM'
    instagram_user_id = "17841469360862189"

    instagram_api = InstagramAPI(app_id, app_secret, short_lived_token, instagram_user_id)

    # Refresh access token
    instagram_api.refresh_access_token()

    # Fetch and download user media
    instagram_api.get_user_media(username="theaubjcc")

    # Upload and publish a new post
    test_image_url = "https://i.imgur.com/q4EPE4Q.jpeg"
    instagram_api.upload_and_publish_pic(test_image_url, caption="This is an automated test post!")