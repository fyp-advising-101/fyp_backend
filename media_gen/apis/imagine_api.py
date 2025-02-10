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
            print(error_msg)
            return {"error": error_msg}, None

        # Attempt to parse the response as JSON
        try:
            response_data = response.json()
        except Exception:
            response_data = {"error": "Failed to parse JSON response", "status_code": response.status_code}

        if response.status_code == 200:
            image_path = "generated_image.png"
            try:
                with open(image_path, "wb") as file:
                    file.write(response.content)
                print(f"Image saved: {image_path}")
                return response_data, image_path
            except Exception as e:
                error_msg = f"Error saving image: {e}"
                print(error_msg)
                return response_data, None
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return response_data, None

# ====== USAGE ======
if __name__ == "__main__":

    VAULT_URL = "https://advising101vault.vault.azure.net"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=VAULT_URL, credential=credential)
    IMAGINE_API_KEY = client.get_secret("IMAGINE-API-KEY").value

    # Initialize Vyro AI API
    imagine = ImagineArtAI(IMAGINE_API_KEY)

    # Define prompt for image generation
    prompt = "A futuristic city at sunset with flying cars and neon lights"
    style = "realistic"
    image_path = imagine.generate_image(prompt, style)
    if image_path:
        print(f"Image successfully saved at: {image_path}")
