import os
import logging
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Ensure your API key is set (best practice: via environment variable)
os.environ["OPENAI_API_KEY"] = "your-api-key-here"

class LangChainManager:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        self.user_agents = {}  # Stores one agent per user
    
    def get_user_agent(self, user_phone_number, collection):
        """
        Retrieve or create a LangChain agent for a given user.
        The agent is equipped with:
          - A vector retrieval tool that queries ChromaDB.
          - Conversation memory to preserve past interactions.
        """
        if user_phone_number not in self.user_agents:
            # Create conversation memory for this user.
            memory = ConversationBufferMemory(
                memory_key="chat_history",   # Key used to store the conversation
                input_key="input",           # Input key for the agent
                return_messages=True
            )
            
            # Define a retrieval tool that queries your ChromaDB collection.
            def retrieve_context(query: str) -> str:
                results = collection.query(
                    query_texts=[query],
                    n_results=10,
                    where={"id": {"$ne": "none"}}
                )
                # Use your existing filtering logic.
                retrieved_docs = [
                    doc for doc, score in zip(results["documents"][0], results["distances"][0])
                    #if score > 0.7
                ]
                logging.info("QUERY RESULTS: "+ str(retrieved_docs))
                context = "\n".join(retrieved_docs) if retrieved_docs else "No context available."
                return context
            
            vector_tool = Tool(
                name="VectorDB",
                func=retrieve_context,
                description="This tool retrieves context from the vector database. Make use of the chat history too."
                    "Use it when additional domain-specific context about the American University of Beirut is needed to answer a question. Assume the user is asking about this university, but don't include the university name in the query."
                    "If the first call returns no relevant context, you MUST rephrase the query and use this tool again at least two more times."
                    "if the user asks about a specific course code, retrieve its syllabus description from the catalogue."
                    "Course codes usually have a 4-letter prefix and a 3-digit number. "
                    "you will be using the previous conversation history if the user/human ask question on previous conversation."
                    
                    
            )
            
            chat_history = MessagesPlaceholder(variable_name="chat_history")

            # Initialize the agent using the Zero-Shot React description approach.
            agent = initialize_agent(
                tools=[vector_tool],
                llm=ChatOpenAI(model_name="gpt-4", openai_api_key=self.openai_api_key),
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=memory,
                agent_kwargs={
                    'chat_history': [chat_history],
                    'memory_prompts': [chat_history],
                    'input_variables': ["input", "agent_scratchpad", "chat_history"],
                }
            )
            
            self.user_agents[user_phone_number] = agent
        return self.user_agents[user_phone_number]
    
    def get_response_from_gpt(self, message_text, collection, user_phone_number) -> str:
        """
        Uses the agent for the given user to generate a response to the message_text.
        The agent will automatically leverage conversation memory and call the retrieval tool as needed.
        """
        agent = self.get_user_agent(user_phone_number, collection)
        response = agent.run(message_text)
        return response

