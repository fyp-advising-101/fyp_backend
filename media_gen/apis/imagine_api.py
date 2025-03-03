import requests
import logging
import os
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
        style: str = random.choice(["flux-dev",'realistic']) ,
        model: str = "stable-diffusion-xl",
        width: int = 512,
        height: int = 512,
        steps: int = 50,
        guidance_scale: float = 7.5
    ):
        """
        Generates an image using the ImagineArt AI API.

        Args:
            prompt (str): Text prompt for the image generation.
            style (str): Style of the generated image (default: "flux-dev").
            model (str): The AI model to use (default: "stable-diffusion-xl").
            width (int): Image width in pixels (default: 512).
            height (int): Image height in pixels (default: 512).
            steps (int): Number of generation steps (default: 50).
            guidance_scale (float): Strength of adherence to the prompt (default: 7.5).

        Returns:
            Tuple[str, str | None]: Status message and file path of the generated image.
        """
        url = f"{self.base_url}/image/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # Validate input values
        if not prompt or not isinstance(prompt, str):
            logging.error("Invalid prompt provided for image generation.")
            return "Invalid prompt", None

        # Prepare payload for multipart/form-data
        print(style)
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
            # Send request to the API with a timeout
            response = requests.post(url, headers=headers, files=payload, timeout=15)
            response.raise_for_status()  # Raise an HTTPError if the response status is 4xx or 5xx
        except requests.exceptions.Timeout:
            logging.error("Request to ImagineArtAI API timed out.")
            raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during API request: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during API request: {e}")
            raise

        # Check if the response is valid
        if response.status_code != 200:
            logging.error(f"API error: {response.status_code}, {response.text}")
            raise

        # Define where to save the image
        image_path = os.path.join(os.getcwd(), "generated_image.png")

        try:
            with open(image_path, "wb") as file:
                file.write(response.content)
            logging.info(f"Image successfully saved at {image_path}")
            return image_path
        except OSError as e:
            logging.error(f"File system error while saving image: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while saving image: {e}")
            raise
