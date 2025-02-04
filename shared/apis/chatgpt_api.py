import openai
from openai import OpenAI

class ChatGptApi:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the ChatGPT client.

        Args:
            api_key (str): Your OpenAI API key.
            model (str, optional): The ChatGPT model to use (default is "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = self.api_key

    def generate_image_generation_prompt(self, context: str) -> str:
        """
        Generates an image generation prompt based on the given context.

        Args:
            context (str): A description or context that the image should capture.

        Returns:
            str: A detailed image generation prompt. If an error occurs, returns an empty string.
        """
        # Craft a system and user prompt to instruct ChatGPT
        system_prompt = "You are a creative assistant specialized in generating detailed and imaginative image prompts."
        user_prompt = (
            f"Based on the following context, generate a detailed image generation prompt that "
            f"describes what to depict in a creative and inspiring manner:\n\nContext: {context}\n\n"
            f"Image Generation Prompt:"
        )

        try:
            response = OpenAI().completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            )
            generated_prompt = response.choices[0].message
            print(generated_prompt)
            return generated_prompt
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return ""
