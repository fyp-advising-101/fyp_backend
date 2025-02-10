import requests
import time
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class NovitaAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.novita.ai/v3"

    def generate_video(self, model_name, prompts, height=512, width=512, steps=20):
        """Sends a request to Novita AI API to generate a video."""
        url = f"{self.base_url}/async/txt2video"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model_name": model_name,
            "height": height,
            "width": width,
            "steps": steps,
            "prompts": prompts,
            "negative_prompt": "nsfw, lowres, bad quality, watermark",
            "guidance_scale": 7.5,
            "seed": -1,
            "closed_loop": False
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            task_id = response.json().get("task_id")
            print(f"Task started successfully. Task ID: {task_id}")
            return task_id
        else:
            print(f"Error: {response.text}")
            return None

    def get_video_status(self, task_id, max_wait_time=600):
        """Checks the status of the Novita AI video generation task with a timeout."""
        url = f"{self.base_url}/async/task-result"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"task_id": task_id}

        start_time = time.time()

        while True:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                result = response.json()
                print(f"API Response: {result}")  # Debugging

                task_status = result.get("task", {}).get("status", "")

                if task_status == "TASK_STATUS_SUCCEED":
                    print("Video generation complete.")

                    # Extract the video URL
                    videos = result.get("videos", [])
                    if videos and "video_url" in videos[0]:
                        video_url = videos[0]["video_url"]
                        print(f"Video URL: {video_url}")
                        return video_url
                    else:
                        print("No video found in response.")
                        return None

                elif task_status == "TASK_STATUS_FAILED":
                    print("Video generation failed.")
                    return None
                else:
                    print("Processing... Waiting 15 seconds before checking again.")
                    time.sleep(15)

            else:
                print(f"API Error: {response.status_code}, {response.text}")
                return None

            if time.time() - start_time > max_wait_time:
                print("Timeout: Video generation took too long.")
                return None

    @staticmethod
    def download_video(url, save_path):
        """Downloads video from Novita AI and saves it locally."""
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                file.write(response.content)
            print(f"Video saved: {save_path}")
            return save_path
        else:
            print(f"Failed to download video: {url}")
            return None



# ====== USAGE ======
if __name__ == "__main__":
    VAULT_URL = "https://advising101vault.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=VAULT_URL, credential=credential)
    NOVITA_API_KEY = client.get_secret("NOVITA-API-KEY").value
    
    # Initialize Novita AI API
    novita = NovitaAI(NOVITA_API_KEY)

    # Define prompts for video generation
    prompts = [
        {"frames": 32, "prompt": "In the wintry dusk, a bear is eating a fish."},
        {"frames": 32, "prompt": "A little girl, barefoot on the frosty pavement, walks up to him and waves."},
        {"frames": 32, "prompt": "A little girl and the bear start dancing."},
        {"frames": 32, "prompt": "In the quiet night, a little girl and the bear sleep."}
    ]

    # Generate video
    task_id = novita.generate_video("darkSushiMixMix_225D_64380.safetensors", prompts)
    
    if task_id:
        # Wait for video to be ready
        video_urls = novita.get_video_status(task_id)
        
        if video_urls:
            # Download the first generated video
            save_path = "generated_video.mp4"  # Save as video file
            downloaded_video = novita.download_video(video_urls, save_path)

        