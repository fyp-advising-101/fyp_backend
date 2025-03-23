import logging
import requests
from openai import OpenAI
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChatGptApi:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the ChatGPT client.

        Args:
            api_key (str): Your OpenAI API key.
            model (str, optional): The ChatGPT model to use (default is "gpt-4").
        """
        self.model = model
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def get_openai_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding vector for the given text using OpenAI Embeddings.

        Args:
            text (str): The text to embed.

        Returns:
            List[float]: The embedding vector as a list of floats.

        Raises:
            Exception: If the OpenAI API request fails.
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-large"
            )
            embedding = response.data[0].embedding
            if not embedding:
                raise ValueError("Received an empty embedding response.")
            return embedding

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while generating embeddings: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error generating embedding: {e}")
            raise

    

    def generate_image_generation_prompt(self, context: str) -> str:
        """
        Generates an image generation prompt based on the given context.

        Args:
            context (str): A description or context that the image should capture.

        Returns:
            str: A detailed image generation prompt.

        Raises:
            Exception: If the API request fails.
        """
        system_prompt = (
            "Imagine you are a creative assistant for image generation, tasked with producing detailed and inspiring prompts. "
            "Focus on generating prompts that feature the distinctive elements of the Middle East, particularly the ambiance and architectural style of the American University of Beirut in Lebanon. "
            "Ensure your output is free from extraneous details like dates or time indicators unless they enhance the creative narrative."
        )

        user_prompt = (
            f"You are given an image prompt context from a vector database and the question used to query into the vector database generate a detailed image generation prompt that "
            f"describes what to depict in a creative and inspiring manner:\n\n"
            f"{context}\n\nImage Generation Prompt:"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_prompt = completion.choices[0].message.content.strip()
            logging.info("Image prompt successfully generated.")
            logging.info("Context Used: %s", context)
            logging.info("Generated Prompt: %s", generated_prompt)


            return generated_prompt 

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while generating image prompt: {e}")
            raise
        except ValueError as e:
            logging.error(f"Data validation error in image prompt response: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while generating image prompt: {e}")
            raise

    def get_completion(self, prompt: str) -> str:
        """
        Get a raw ChatGPT response for a simple prompt (e.g., style selection).

        Args:
            prompt (str): The prompt string to send to the assistant.

        Returns:
            str: The assistant's text response.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0  # deterministic output for things like selecting a style
            )
            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            return completion.choices[0].message.content.strip()

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while getting completion: {e}")
            raise
        except ValueError as e:
            logging.error(f"Validation error in completion response: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while getting completion: {e}")
            raise


    def generate_caption(self, context: str) -> str:
        """
        Generates a creative caption based on the given context.

        Args:
            context (str): The context or description from which to generate a caption.

        Returns:
            str: A creative caption that encapsulates the essence of the context.

        Raises:
            Exception: If the API request fails.
        """
        system_prompt = (
            "Imagine you are a creative assistant specialized in crafting engaging captions. "
            "Your goal is to produce a short, impactful, and creative caption that reflects the core message of the provided context. "
            "Keep it succinct and expressive. Limit to 50 words."
        )

        user_prompt = (
            f"Using the context below, generate a creative caption that captures its essence:\n\n"
            f"{context}\n\nCaption:"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_caption = completion.choices[0].message.content.strip()
            logging.info("Caption successfully generated.")
            logging.info("Context Used: %s", context)
            logging.info("Generated Caption: %s", generated_caption)

            return generated_caption

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while generating caption: {e}")
            raise
        except ValueError as e:
            logging.error(f"Data validation error in caption response: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while generating caption: {e}")
            raise

