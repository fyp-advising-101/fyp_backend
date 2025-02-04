from openai import OpenAI


class ChatGptApi:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the ChatGPT client.

        Args:
            api_key (str): Your OpenAI API key.
            model (str, optional): The ChatGPT model to use (default is "gpt-4").
        """
        self.model = model
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

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
            completion = self.client.chat.completions.create(model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7)
            generated_prompt = completion.choices[0].message.content.strip()
            return generated_prompt
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return ""
