from openai import OpenAI

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

    def get_openai_embedding(self, text: str) -> list:
        """
        Generates an embedding vector for the given text using OpenAI Embeddings.

        Args:
            text (str): The text to embed.

        Returns:
            list: The embedding vector as a list of floats.
        """
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-large"
        )
        return response.data[0].embedding

    def get_response_from_gpt(self, message_text: str, collection) -> str:
        """
        Retrieves a response from GPT using a vector-based context retrieval step.
        
        Args:
            message_text (str): The user's question or prompt.
            collection: A vector store or database collection that supports the 'query' method 
                        to retrieve context based on embeddings.

        Returns:
            str: The GPT-generated response.
        """
        # 1. Generate embeddings for the user query
        embeddings = self.get_openai_embedding(message_text)
        
        # 2. Query your vector store for context
        results = collection.query(
            embeddings, 
            n_results=30,  
            where={"id": {"$ne": "none"}}
        )
        
        # 3. Build a context string from retrieved documents
        retrieved_docs = results["documents"][0]
        context = "\n".join(retrieved_docs)
        
        # 4. Construct the prompt for GPT
        prompt = f"""You are an AI assistant answering questions about a university.

Context:
{context}

Question: {message_text}
Answer:
"""
        
        # 5. Get the GPT response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        chatbot_response = response.choices[0].message.content
        return chatbot_response

    def generate_image_generation_prompt(self, context: str):
        """
        Generates an image generation prompt based on the given context.

        Args:
            context (str): A description or context that the image should capture.

        Returns:
            str: A detailed image generation prompt. If an error occurs, returns an empty string.
        """
        system_prompt = (
"""
Imagine you are a creative assistant for image generation, tasked with producing detailed and inspiring prompts. 
Focus on generating prompts that feature the distinctive elements of the Middle East, particularly the ambiance and architectural style of the American University of Beirut in Lebanon. 
Ensure your output is free from extraneous details like dates or time indicators unless they enhance the creative narrative.
"""
        )
        user_prompt = (
            f"Based on the following context, generate a detailed image generation prompt that "
            f"describes what to depict in a creative and inspiring manner:\n\n"
            f"Context: {context}\n\nImage Generation Prompt:"
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
            generated_prompt = completion.choices[0].message.content.strip()
            print("Prompt Generated!")
            return generated_prompt 
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return ""
