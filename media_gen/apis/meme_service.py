import os
import json
import requests
import base64
import logging
import random
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class MemeService:
    """
    Service for generating memes through the meme-surprise API.
    """
    
    def __init__(self):
        """
        Initialize the Meme Service.
        """
        self.api_url = "https://meme-surprise-online-tool.onrender.com/generate-meme"
        self.output_directory = "memes"
        
        # Ensure the output directory exists
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)
    
    def generate_meme(self, sentence: str, roast_level: str):
        """
        Generates a meme using the provided content, calls the meme generation service,
        and saves the generated image in the 'memes' folder with a unique filename.
        
        Args:
            sentence (str): The text to use in the meme
            roast_level (str): The roast level (wholesome, spicy, or savage)
            
        Returns:
            str: The file path where the meme image is saved.
            
        Raises:
            Exception: If any step of the meme generation or saving process fails.
        """
        # Validate input
        valid_levels = ["wholesome", "spicy", "savage"]
        if roast_level.lower() not in valid_levels:
            roast_level = "wholesome"  # default if not valid
        
        logging.info(f"Generating meme with sentence: {sentence}, roast level: {roast_level}")
        
        # Generate a unique filename based on timestamp + random number to avoid collisions
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = random.randint(1000, 9999)
        base_name = "generatedmeme"
        extension = ".jpg"
        filename = os.path.join(self.output_directory, f"{base_name}_{timestamp}_{random_suffix}{extension}")
        
        # Call the meme generation service
        payload = {
            "roast_level": roast_level,
            "fun_fact": sentence  # Using the provided sentence as the meme text
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # In case of hitting a rate limit
            if response.status_code == 429:
                raise Exception("Use limit reached. Please wait a minute and try again.")
            
            # Process the image data returned by the meme generation service
            image_blob = response.content
            image_base64 = base64.b64encode(image_blob).decode("utf-8")
            image_url = f"data:image/jpeg;base64,{image_base64}"
            
            if image_url.startswith("data:image/jpeg;base64,"):
                base64_data = image_url.split(",")[1]
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(base64_data))
                logging.info(f"Meme saved as '{filename}'")
                return filename
            else:
                raise Exception("Failed to generate a valid meme URL.")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error communicating with meme generation service: {e}")
            raise Exception(f"Error generating meme: {e}")
        except Exception as e:
            logging.error(f"Error generating or saving meme: {e}")
            raise