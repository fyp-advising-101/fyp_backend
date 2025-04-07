import logging
import requests
from openai import OpenAI
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
        "You are a specialized AI image prompt engineer. Your task is to create clear, detailed, and visually coherent image prompts. "
        "Always structure your prompts to include these essential elements: "
        "1. SUBJECT: Describe the primary subject with specific details (person, object, animal, etc.). "
        "2. DESCRIPTION: Provide key details about the subject's appearance, pose, or characteristics. "
        "3. ENVIRONMENT: Describe the setting or background with 2-3 specific elements. "
        "4. MEDIUM: Specify the artistic medium (photography, oil painting, digital art, etc.). "
        "5. STYLE: Include a clear stylistic reference (realistic, surrealist, minimalist, etc.). "
        "6. RESOLUTION: Mention high resolution or level of detail. "
        "7. QUALITY: Indicate the image quality (professional, cinematic, etc.). "
        "8. LIGHTING: Specify lighting conditions (soft, dramatic, natural, golden hour, etc.). "
        "Keep your prompt concise and cohesive, focusing on creating a single, clear visual scene. "
        "Your response should contain only the final prompt with no additional explanations."
        )

        user_prompt = (
        f"Based on this context: \"{context}\"\n\n"
        f"Create an image generation prompt that includes all of these elements:\n"
        f"- Subject: What is the main focus of the image?\n"
        f"- Description: What specific details should be included about the subject?\n"
        f"- Environment: What setting or background should appear? \n"
        f"- Medium: What artistic medium should this resemble?\n"
        f"- Style: What artistic style should be applied?\n"
        f"- Resolution: Specify that it should be high-resolution\n"
        f"- Quality: Indicate the level of professional quality\n"
        f"- Lighting: What lighting conditions should be present?\n\n"
        f"Craft these elements into a cohesive, natural-sounding prompt that will generate a clear."
    )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5  # Slightly higher for creative humor/meme content when appropriate
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_prompt = completion.choices[0].message.content.strip()
            
            # Ensure "NO TEXT" is in the prompt even if the model fails to include it
            if "NO TEXT" not in generated_prompt.upper():
                generated_prompt += " NO TEXT, NO WRITING, NO WORDS."
                
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

    def generate_image_generation_prompt_funny(self, context: str) -> str:
        """
        Generates a humorous and quirky image generation prompt based on the given context.
        
        Args:
            context (str): A description or context that the image should capture.
        
        Returns:
            str: A detailed image generation prompt with a humorous twist.
        
        Raises:
            Exception: If the API request fails.
        """
        system_prompt = (
            "You are a specialized AI image prompt engineer with a quirky sense of humor. Your task is to create whimsical, "
            "slightly absurd, and playful image prompts that will make viewers smile or laugh. "
            "Always structure your prompts to include these essential elements, but with a humorous twist: "
            "1. SUBJECT: Describe the primary subject with specific details, adding unexpected or amusing characteristics. "
            "2. DESCRIPTION: Provide key details about the subject's appearance, pose, or characteristics that create visual humor. "
            "3. ENVIRONMENT: Describe a setting or background with 2-3 specific elements that add to the whimsical nature. "
            "4. MEDIUM: Specify the artistic medium that enhances the quirky feeling (cartoon, claymation, etc.). "
            "5. STYLE: Include a playful stylistic reference (caricature, pop art, storybook illustration, etc.). "
            "6. RESOLUTION: Mention high resolution or level of detail. "
            "7. QUALITY: Indicate the image quality while maintaining the light-hearted tone. "
            "8. LIGHTING: Specify lighting conditions that enhance the humor (overly dramatic, technicolor, etc.). "
            "Keep your prompt concise and cohesive, focusing on creating a single, clear visual scene with unexpected elements or "
            "amusing juxtapositions. Your response should contain only the final prompt with no additional explanations. NO TEXT, NO WRITING, NO WORDS."
        )

        user_prompt = (
            f"Based on this context: \"{context}\"\n\n"
            f"Create a humorous, quirky image generation prompt that includes all of these elements:\n"
            f"- Subject: What is the main focus of the image? Add an unexpected or amusing twist.\n"
            f"- Description: What specific details should be included about the subject to make it funny or quirky?\n"
            f"- Environment: What setting or background should appear? Include something unexpected or out of place.\n"
            f"- Medium: What artistic medium would enhance the humorous nature?\n"
            f"- Style: What whimsical or playful artistic style should be applied?\n"
            f"- Resolution: Specify that it should be high-resolution\n"
            f"- Quality: Indicate the level of professional quality while maintaining the playful tone\n"
            f"- Lighting: What lighting conditions would enhance the quirky nature?\n\n"
            f"Craft these elements into a cohesive, natural-sounding prompt that will generate a clear, visually appealing image "
            f"with a humorous or whimsical quality. Make sure to specify NO TEXT, NO WRITING, NO WORDS."
        )
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5  # Slightly higher for creative humor/meme content when appropriate
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_prompt = completion.choices[0].message.content.strip()
            
            # Ensure "NO TEXT" is in the prompt even if the model fails to include it
            if "NO TEXT" not in generated_prompt.upper():
                generated_prompt += " NO TEXT, NO WRITING, NO WORDS."
                
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

    def generate_image_generation_prompt_funny(self, context: str) -> str:
            """
            Generates an engaging and informal image generation prompt based on the given context.
            
            Args:
                context (str): A description or context that the image should capture.
            
            Returns:
                str: A detailed image generation prompt with an engaging, informal style.
            
            Raises:
                Exception: If the API request fails.
            """
            system_prompt = (
                "You are a specialized AI image prompt engineer with a casual, approachable style. Your task is to create engaging, "
                "relatable, and informal image prompts that feel authentic and down-to-earth. "
                "Always structure your prompts to include these essential elements, but with a warm, conversational tone: "
                "1. SUBJECT: Describe the primary subject with specific details that feel genuine and relatable. "
                "2. DESCRIPTION: Provide key details about the subject's appearance, pose, or characteristics that capture everyday authenticity. "
                "3. ENVIRONMENT: Describe a setting or background with 2-3 specific elements that feel familiar and inviting. "
                "4. MEDIUM: Specify an artistic medium that enhances the casual, approachable feeling. "
                "5. STYLE: Include a stylistic reference that feels contemporary and relatable (candid photography, casual illustration, etc.). "
                "6. RESOLUTION: Mention high resolution or level of detail. "
                "7. QUALITY: Indicate the image quality while maintaining the informal tone. "
                "8. LIGHTING: Specify lighting conditions that feel natural and authentic. "
                "Keep your prompt concise and cohesive, focusing on creating a single, clear visual scene that feels like a genuine moment "
                "rather than a posed or formal scene. Your response should contain only the final prompt with no additional explanations. NO TEXT, NO WRITING, NO WORDS."
            )

            user_prompt = (
                f"Based on this context: \"{context}\"\n\n"
                f"Create an engaging, informal image generation prompt that includes all of these elements:\n"
                f"- Subject: What is the main focus of the image? Make it feel authentic and relatable.\n"
                f"- Description: What specific details should be included about the subject to capture a genuine moment?\n"
                f"- Environment: What casual, everyday setting or background should appear?\n"
                f"- Medium: What artistic medium would enhance the informal, approachable feeling?\n"
                f"- Style: What contemporary, relatable artistic style should be applied?\n"
                f"- Resolution: Specify that it should be high-resolution\n"
                f"- Quality: Indicate the level of professional quality while maintaining the casual feel\n"
                f"- Lighting: What natural, authentic lighting conditions would enhance the scene?\n\n"
                f"Craft these elements into a cohesive, natural-sounding prompt that will generate a clear, visually appealing image "
                f"with an engaging, informal quality. Make sure to specify NO TEXT, NO WRITING, NO WORDS."
            )
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.5  # Slightly higher for creative humor/meme content when appropriate
                )

                if not completion.choices or not completion.choices[0].message.content:
                    raise ValueError("Received an empty response from GPT.")

                generated_prompt = completion.choices[0].message.content.strip()
                
                # Ensure "NO TEXT" is in the prompt even if the model fails to include it
                if "NO TEXT" not in generated_prompt.upper():
                    generated_prompt += " NO TEXT, NO WRITING, NO WORDS."
                    
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


    def generate_caption(self, context: str, chroma_query: str = None) -> str:
        """
        Generates a creative caption based on the given context, prompt text, and query.

        Args:
            context (str): The context or description from the ChromaDB results.
            prompt_text (str, optional): The text used to prompt image generation.
            chroma_query (str, optional): The original query used to search ChromaDB.

        Returns:
            str: A creative caption that encapsulates the essence of the context.

        Raises:
            Exception: If the API request fails.
        """

        system_prompt = (
        "You are a caption writer for social media images related to the American University of Beirut. "
        "Your captions should follow these guidelines:\n"
        "1. Keep captions concise and engaging (30-50 words maximum)\n"
        "2. Focus on the key message or theme from the context\n"
        "3. Include relevant hashtags (2-3 maximum) that relate to AUB and the content\n"
        "4. Maintain a voice that is professional yet warm and relatable\n"
        "5. For news content: be informative and highlight key points\n"
        "6. For current events: create excitement and mention the essence of the event\n"
        "7. For past events: use phrases like 'Did you know' or 'Reflecting on' to indicate it's not current\n"
        "8. For general information: frame as interesting facts with phrases like 'Fun fact' or 'AUB spotlight'\n"
        "9. For academic content: be educational and inspirational\n"
        "10. For humorous content: be witty while maintaining appropriateness\n"
        "11. Always incorporate a sense of community and pride related to AUB or Middle Eastern culture\n"
        "12. Adapt the tense appropriately - use present/future tense for upcoming events and past tense for "
        "concluded events or historical information\n"
        "13. Never include information that isn't supported by the provided context"
    )

        # Combine available information for more comprehensive context
        combined_context = "Context from database:\n" + context

        if chroma_query:
            combined_context += "\n\nOriginal search query:\n" + chroma_query

        user_prompt = (
            f"Create a social media caption for an image based on the following information:\n\n"
            f"{combined_context}\n\n"
            f"The caption should:\n"
            f"- Be 30-50 words maximum\n"
            f"- Capture the essence of the content\n"
            f"- Include 2-3 relevant hashtags\n"
            f"- Be engaging and appropriate for university social media\n"
            f"- Match the content type:\n"
            f"  * For current news/events: Create excitement and immediacy\n"
            f"  * For past events: Use 'Did you know' or reflection framing\n"
            f"  * For general information: Present as interesting facts about AUB\n"
            f"  * For academic content: Be educational and inspirational\n"
            f"  * For humorous content: Be witty and relatable\n"
            f"- Use appropriate tense (present/future for upcoming events, past for historical information)"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_caption = completion.choices[0].message.content.strip()
            logging.info("Caption successfully generated.")
            logging.info("Context Used: %s", combined_context)
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

    def generate_video_generation_prompt(self, context: str) -> str:
        """
        Generates a video generation prompt based on the given context.

        Args:
            context (str): A description or context that the video should capture.

        Returns:
            str: A detailed video generation prompt.

        Raises:
            Exception: If the API request fails.
        """
        system_prompt = (
    "You are a specialized AI video prompt engineer. Your task is to create clear, cinematic, and realistic video prompts. "
    "Always structure your prompts around these essential elements: "
    "1. MEDIUM: Specify exactly one shot type (close-up, medium, wide-angle). "
    "2. SUBJECT: Describe a single, clear subject with specific details about appearance. "
    "3. SUBJECT MOTION: Include one simple, clear motion for the subject. "
    "4. SCENE: Describe the environment with 2-3 specific elements. "
    "5. SCENE MOTION: Add one atmospheric element (rain, wind, etc.) if appropriate. "
    "6. CAMERA QUALITY: Mention that it's shot on a high-quality cinematic camera. "
    "7. CAMERA MOTION: Include only one type of camera motion (tracking, panning, static). "
    "8. AESTHETICS: Specify lighting condition, time of day, and overall color palette. "
    "Keep your prompt under 6 sentences. Do not use brackets or placeholders. Focus on creating a cohesive scene with a single subject and limited action. "
    "Your response should contain only the final prompt with no additional explanations."
)

        user_prompt = (
    f"Based on this context: \"{context}\"\n\n"
    f"Create a cinematic video prompt that: "
    f"- Features a single, clear subject "
    f"- Uses one type of shot (close-up, medium, or wide) "
    f"- Has simple, focused subject motion "
    f"- Takes place in a specific time of day with clear lighting "
    f"- Includes one type of camera motion at most "
    f"- Creates a cohesive visual atmosphere "
    f"The prompt should be 2-3 sentences maximum and avoid mentioning multiple characters or simultaneous actions."
)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_prompt = completion.choices[0].message.content.strip()
            
            # Ensure "NO TEXT" is in the prompt
            if "NO TEXT" not in generated_prompt.upper():
                generated_prompt += " NO TEXT, NO WRITING, NO WORDS."
                
            logging.info("Video prompt successfully generated.")
            logging.info("Context Used: %s", context)
            logging.info("Generated Prompt: %s", generated_prompt)

            return generated_prompt 

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while generating video prompt: {e}")
            raise
        except ValueError as e:
            logging.error(f"Data validation error in video prompt response: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while generating video prompt: {e}")
            raise

    def generate_video_caption(self, context: str, prompt_text: str = None, chroma_query: str = None) -> str:
        """
        Generates a caption for a video based on the given context.

        Args:
            context (str): The context or description from the ChromaDB results.
            prompt_text (str, optional): The text used to prompt video generation.
            chroma_query (str, optional): The original query used to search ChromaDB.

        Returns:
            str: A creative caption for the video.

        Raises:
            Exception: If the API request fails.
        """
        system_prompt = (
            "You create video captions for social media content related to the American University of Beirut. "
            "Your captions should follow these guidelines:\n"
            "1. Keep captions concise and engaging (30-50 words maximum)\n"
            "2. Focus on the key message or theme from the context\n"
            "3. Include relevant hashtags (2-3 maximum) that relate to AUB and the content\n"
            "4. Maintain a voice that is professional yet warm and relatable\n"
            "5. For news content: be informative and highlight key points\n"
            "6. For events: create excitement and convey dynamic atmosphere\n"
            "7. For past events: use phrases like 'Did you know' or 'Reflecting on'\n"
            "8. For general information: frame as interesting facts with phrases like 'AUB spotlight'\n"
            "9. Always incorporate a sense of community and pride related to AUB\n"
            "10. Include a call to action where appropriate (watch till the end, share your thoughts, etc.)\n"
            "11. Never include information that isn't supported by the provided context"
        )

        # Combine available information for more comprehensive context
        combined_context = "Context from database:\n" + context
        
        if prompt_text:
            combined_context += "\n\nPrompt used for video generation:\n" + prompt_text
        
        if chroma_query:
            combined_context += "\n\nOriginal search query:\n" + chroma_query

        user_prompt = (
            f"Create a social media caption for a video based on the following information:\n\n"
            f"{combined_context}\n\n"
            f"The caption should:\n"
            f"- Be 30-50 words maximum\n"
            f"- Capture the essence of the content\n"
            f"- Include 2-3 relevant hashtags\n"
            f"- Be engaging and appropriate for university social media\n"
            f"- Include a subtle call to action\n"
            f"- Match the content type (news, event, academic, or informational)"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6
            )

            if not completion.choices or not completion.choices[0].message.content:
                raise ValueError("Received an empty response from GPT.")

            generated_caption = completion.choices[0].message.content.strip()
            logging.info("Video caption successfully generated.")
            logging.info("Context Used: %s", combined_context)
            logging.info("Generated Caption: %s", generated_caption)

            return generated_caption

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while generating video caption: {e}")
            raise
        except ValueError as e:
            logging.error(f"Data validation error in caption response: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while generating caption: {e}")
            raise