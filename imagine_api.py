import requests
import time
import os
from dotenv import load_dotenv
class ImagineArtAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.vyro.ai/v2"

    def generate_image(self, prompt, style, model="stable-diffusion-xl", width=512, height=512, steps=50, guidance_scale=7.5):
        """
        Sends a request to Vyro AI's API to generate an image using multipart/form-data.
        """
        url = f"{self.base_url}/image/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # API expects multipart/form-data
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

        response = requests.post(url, headers=headers, files=payload)
        if response.status_code == 200:
            image_path = "generated_image.png"
            with open(image_path, "wb") as file:
                file.write(response.content)
            print(f"Image saved: {image_path}")
            return image_path
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

# ====== USAGE ======
if __name__ == "__main__":
    # Vyro AI API Key
    IMAGINE_API_KEY = os.getenv("IMAGINE_API_KEY")

    # Initialize Vyro AI API
    imagine = ImagineArtAI(IMAGINE_API_KEY)

    # Define prompt for image generation
    prompt = "A futuristic city at sunset with flying cars and neon lights"
    style = "realistic"
    image_path = imagine.generate_image(prompt, style)
    if image_path:
        print(f"Image successfully saved at: {image_path}")
