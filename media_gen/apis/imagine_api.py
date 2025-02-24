import requests
import time
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class ImagineArtAI:
    def __init__(self, api_key: str):
        """
        Initialize the ImagineArtAI client.

        Args:
            api_key (str): Your API key for ImagineArt AI.
        """
        self.api_key = api_key
        self.base_url = "https://api.vyro.ai/v2"

    def generate_image(
        self,
        prompt: str,
        style: str,
        model: str = "stable-diffusion-xl",
        width: int = 512,
        height: int = 512,
        steps: int = 50,
        guidance_scale: float = 7.5
    ) :
        url = f"{self.base_url}/image/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Prepare payload for multipart/form-data
        payload = {
            "model": (None, model),
            "prompt": (None, prompt),
            "style": (None, style),
            "width": (None, str(width)),
            "height": (None, str(height)),
            "steps": (None, str(steps)),
            "guidance_scale": (None, str(guidance_scale)),
            "negative_prompt": (None, "low quality, watermark, blurry"),
            "seed": (None, "-1")
        }

        try:
            response = requests.post(url, headers=headers, files=payload)
        except Exception as e:
            error_msg = f"Request error: {e}"
            return error_msg, None

        if response.status_code == 200:
            image_path = "generated_image.png"
            try:
                with open(image_path, "wb") as file:
                    file.write(response.content)
                print(f"Image saved: {image_path}")
                return "Image Successfully Generated", image_path
            except Exception as e:
                return "Error Saving Image", None
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return "Image Generation Failed", None
