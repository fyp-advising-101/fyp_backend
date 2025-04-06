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
            "You create image generation prompts with these mandatory requirements:\n"
            "1. THEME: Always incorporate elements of the American University of Beirut and Middle Eastern aesthetics, "
            "   architecture, landscapes, or cultural elements regardless of the specific content.\n"
            "2. NO TEXT: Always include 'NO TEXT, NO WRITING, NO WORDS' in your prompt to ensure the image generator "
            "   doesn't include any text, captions, signs, or written elements.\n"
            "3. CONTEXT ADHERENCE: Base your prompt only on the factual information from the provided context.\n"
            "4. CONTENT-SPECIFIC RULES:\n"
            "   - FOR NEWS: Focus on depicting the location, key visual elements, and atmosphere of the news story. "
            "     For academic news, show scholars in AUB settings. For achievements, show celebration scenes.\n"
            "   - FOR EVENTS: For current/upcoming events, emphasize event atmosphere, venue decoration, and typical activities. "
            "     For past events, create a visual that represents the essence of what happened without suggesting it's current.\n"
            "   - FOR GENERAL INFORMATION: Create an illustrative scene that represents the information visually. For example, "
            "     if sharing facts about campus buildings, show the architectural elements mentioned.\n"
            "   - FOR 'DID YOU KNOW' CONTENT: Create visual representations of interesting facts without attempting to show text "
            "     explaining the fact.\n"
            "   - FOR ACADEMIC CONTENT: Show relevant academic settings like libraries, labs, classrooms with "
            "     Middle Eastern architectural influence.\n"
            "   - FOR MEMES/HUMOR: Create visually funny scenarios with exaggerated expressions, humorous situations "
            "     in AUB settings, or playful representations of campus life.\n"
            "5. MIDDLE EASTERN ELEMENTS: Incorporate authentic Middle Eastern architectural elements, colors, "
            "   patterns, landscapes, or cultural references where appropriate.\n"
            "6. SEASONS & TIME: If seasonality or time of day is mentioned or implied, reflect this accurately "
            "   (AUB in spring, during sunset, at night, etc.).\n"
            "7. ACCURACY: Never invent details not mentioned in the context, but do apply the AUB/Middle Eastern theme."
        )

        user_prompt = (
            f"Below is content scraped from either a university website or social media post:\n\n"
            f"{context}\n\n"
            f"Create an image generation prompt that visualizes this content while following these requirements:\n"
            f"1. Frame the scene at or related to the American University of Beirut\n"
            f"2. Incorporate Middle Eastern aesthetic elements\n"
            f"3. DO NOT generate any text or writing in the image\n"
            f"4. Focus on visual elements and atmosphere\n"
            f"5. Identify the content type:\n"
            f"   - Current news/events: Show the activity/situation as it happens\n"
            f"   - Past events: Create a representative scene that captures the essence without implying it's current\n"
            f"   - General information/facts: Illustrate the information visually (like 'Did you know?' content)\n"
            f"   - Academic content: Show relevant educational settings\n"
            f"   - Humor/memes: Create visually amusing scenarios related to the content\n\n"
            f"Your final prompt must include the phrase 'NO TEXT' and emphasize the AUB/Middle Eastern setting."
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


    def generate_caption(self, context: str, prompt_text: str = None, chroma_query: str = None) -> str:
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
        
        if prompt_text:
            combined_context += "\n\nPrompt used for image generation:\n" + prompt_text
        
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
            "You create video generation prompts with these mandatory requirements:\n"
            "1. THEME: Always incorporate elements of the American University of Beirut and Middle Eastern aesthetics, "
            "   architecture, landscapes, or cultural elements regardless of the specific content.\n"
            "2. NO TEXT: Always include 'NO TEXT, NO WRITING, NO WORDS' in your prompt to ensure the video generator "
            "   doesn't include any text, captions, signs, or written elements.\n"
            "3. CONTEXT ADHERENCE: Base your prompt only on the factual information from the provided context.\n"
            "4. MOTION & FLOW: Since this is for video generation, emphasize motion, transitions, and flow. "
            "   Describe how elements should move or change throughout the video sequence.\n"
            "5. CONTENT-SPECIFIC RULES:\n"
            "   - FOR NEWS: Focus on depicting key visual elements with subtle motion and atmosphere.\n"
            "   - FOR EVENTS: Emphasize dynamic activity, crowd movements, and event progression.\n"
            "   - FOR GENERAL INFORMATION: Create illustrative scenes with gentle camera movement to highlight details.\n"
            "   - FOR ACADEMIC CONTENT: Show academic settings with natural activity like students moving, pages turning, etc.\n"
            "6. MIDDLE EASTERN ELEMENTS: Incorporate authentic Middle Eastern architectural elements, colors, "
            "   patterns, landscapes, or cultural references where appropriate.\n"
            "7. BREVITY: Keep the prompt concise as video generators work best with clear, focused descriptions.\n"
            "8. ACCURACY: Never invent details not mentioned in the context, but do apply the AUB/Middle Eastern theme."
        )

        user_prompt = (
            f"Below is content scraped from a university website or social media post:\n\n"
            f"{context}\n\n"
            f"Create a video generation prompt that visualizes this content while following these requirements:\n"
            f"1. Frame the scene at or related to the American University of Beirut\n"
            f"2. Incorporate Middle Eastern aesthetic elements\n"
            f"3. DO NOT generate any text or writing in the video\n"
            f"4. Emphasize motion, dynamic elements, and visual flow\n"
            f"5. Keep the prompt concise and focused (50-70 words maximum)\n"
            f"6. Include specific motion directions (camera movements, transitions, etc.)\n"
            f"Your final prompt must include the phrase 'NO TEXT' and emphasize the AUB/Middle Eastern setting."
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