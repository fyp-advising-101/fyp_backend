# runway_api.py (new file in media_gen/apis/)
import requests
import logging
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RunwayAPI:
    """Client for Runway AI video generation API."""
    
    def __init__(self, api_key: str):
        """
        Initialize the Runway API client.
        
        Args:
            api_key (str): Your API key for Runway API.
        """
        self.api_key = api_key
        self.base_url = "https://api.aivideoapi.com"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def generate_video(self, prompt: str, model: str = "gen3", 
                       height: int = 768, width: int = 1280, 
                       motion: int = 5, seconds: int = 5):
        """
        Generates a video based on a text prompt.
        """
        url = f"{self.base_url}/runway/generate/text"
        
        payload = {
            "text_prompt": prompt,
            "model": model,
            "height": height,
            "width": width,
            "motion": motion,
            "seed": 0,
            "time": seconds
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "uuid" not in data:
                raise ValueError("No uuid returned in response")
            
            logging.info(f"Video generation task started with ID: {data['uuid']}")
            return data["uuid"]
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during video generation request: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during video generation: {e}")
            raise
    
    def check_video_status(self, uuid: str):
        """
        Checks the status of a video generation task.
        
        Args:
            task_id (str): The task ID to check.
            
        Returns:
            dict: Status information including state and possibly video URL.
        """
        url = f"{self.base_url}/status"
        params = {"uuid": uuid}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            logging.info(f"Video task status: {data.get('status', 'unknown')} for task {uuid}")
            return data
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error checking video status: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response content: {e.response.text}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error checking video status: {e}")
            raise