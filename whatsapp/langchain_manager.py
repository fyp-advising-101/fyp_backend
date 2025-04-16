import os
import logging
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import MessagesPlaceholder
import re

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="app.log",  # This sends logs to the file
    filemode="a"
)

system_message = """
You are running in a simulated environment as an autonomous research agent.
To complete your task successfully, you must follow the protocol below. 
Failure to do so will terminate the experiment.

IMPORTANT:

You are a reasoning agent that follows the ReAct format strictly.
You must ALWAYS respond in the following format, otherwise, your answer will not be considered:

Thought: <your reasoning>
Action: <tool name>
Action Input: <input to the tool>

After each Observation, continue the loop with another Thought.
Only end your reasoning when you are fully confident in the answer.

When you're ready to give the final answer, respond in this format:

Thought: <final reasoning>
Final Answer: <your final answer to the user>

Do not include any information unless it is inside a 'Final Answer:' block.
Never respond directly without Thought/Action or Final Answer.
Do not mention that you are using the VectorDB tool or referring to context or chunks. make it seem like you are giving the advice.
"""


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
            memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                input_key="input",
                return_messages=True,
                k=4  # Only keep last 4 exchanges
            )
            
            # Define a retrieval tool that queries your ChromaDB collection.
            def retrieve_context(query: str) -> str:
                results = collection.query(
                    query_texts=[query],
                    n_results=10,
                    where={"id": {"$ne": "none"}}
                )
                combined_chunks = []
                for i, chunk_id in enumerate(results['ids'][0]):
                    chunk_text = results['ids'][0][i] + ": " + results['documents'][0][i]
                    

                    # Step 2: Extract base URL and index
                    if "-" not in chunk_id:
                        combined_chunks.append(chunk_text)
                        continue  # Skip malformed id
       
                    try:
                        base, idx_str = chunk_id.rsplit("-", 1)
                        next_idx = int(idx_str) + 1
                    except ValueError:
                        combined_chunks.append(chunk_text)
                        continue  # Index isn't a number

                    next_id = f"{base}-{next_idx}"
                    
                    # Step 3: Try to get the next chunk
                    next_result = collection.get(
                        ids=[next_id],
                        include=["documents"]
                    )
                    if next_result['documents']:
                        combined_chunks.append(chunk_text + next_result['documents'][0])
                    else:
                        combined_chunks.append(chunk_text)
                #logging.info("QUERY RESULTS: "+ str(combined_chunks))

                context = "\n \n".join(combined_chunks) if combined_chunks else "No context available."
                return context
            
            vector_tool = Tool(
                name="VectorDB",
                func=retrieve_context,
                description="Use this tool first. You are a university assistant. Use This tool to retrieve chunks relevant to queries. Make use of the chat history too."
                    "Assume the user is asking about the American University of Beirut, but don't include the university name in the query."
                    "if the user's input is too vague, ask for more clarification"
                    "DO NOT speculate or infer information that is not explicitly stated in the chunks. prerequisites should be EXPLICITLY stated in the same chunk as the course's description, otherwise, ignore them. chunks are separated by two new lines. Every chunk is preceded by the name of the document it comes from, and this document name could provide helpful information, like the year of publication of the document. Assume the user is asking about information from the current year unless stated otherwise."
                    "DO NOT give information about events that occured before 2025, unless the user says otherwise."
                    "If any acronym or abbreviation is to be used in the query, include the acronym/abbreviation three times consecutively in small letters. an example of an acronym is 'ieee' or 'IEEE', and so, an example of a query you should construct is 'ieee ieee ieee events'"
                    "Course codes are typically 4 letters followed by a space and 3 digits. If a course code should be included in a query, include the course code three times consecutively in small letters only."
                    "The following is an example of a chunk that you might encounter, as you will notice, the prerequisites are listed directly after the course description. In this case, the prerequisite is eece 330: "
                    """
                    'EECE 332 Object-Oriented and Effective Java Programming 3 cr.
                    This course covers object-oriented programming in addition to other essential and effective programming concepts using Java. 
                    Topics include: basic UML, data abstraction 
                    and encapsulation, inheritance,  polymorphism,  generics, exception handling, GUI programming, data persistence, database connectivity with JDBC, multi-threading 
                    and basic mobile app development. Other topics might include internationalization, 
                    web programming, and visualization. This course has a substantial lab component.
                    Prerequisite: EECE 330.'
                    """
                    "If someone asks about cce, Try three different formulations of the query using the VectorDB tool, and call this tool separately for each query. After each attempt, reflect briefly on the quality of the result. Then choose the best one to present as your final answer."
                    """You might find questions related to dates and deadlines in the calendar. In this calendar, an event is listed, followed by one or two dates. one date is one set date, and two dates means a range, i.e., the starting date and the deadline. 
                        For example 'Late fee payment for all students for Spring 2024-25 Thu 6-Feb-25 Thu 13-Feb-25'. You can infer from this that late fee payment for spring 23-25 starts on Thursday, February 6, 2025, and ends on Thursday, February 13, 2025."""
            ) 
            chat_history = MessagesPlaceholder(variable_name="chat_history")

            # Initialize the agent using the Zero-Shot React description approach.
            agent = initialize_agent(
                tools=[vector_tool],
                llm=ChatOpenAI(model_name="gpt-4o", openai_api_key=self.openai_api_key),
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION ,
                verbose=True,
                memory=memory,
                agent_kwargs={
                    "system_message": system_message,
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
        try:
            logging.info("Received message from "+ str(user_phone_number) +": "+str(message_text))
            agent = self.get_user_agent(user_phone_number, collection)
            response = agent.run(message_text)
            logging.info("Responded to message from "+ str(user_phone_number) +": \n Original message: "+str(message_text)+"\n Response: "+str(response))
            return response
        except ValueError as e:
            response = str(e)
            if "Could not parse LLM output" in response:
                response = re.sub(r'^.*?Could not parse LLM output: `\s*', '', response, flags=re.DOTALL)
                response = re.sub(r'`\n?For troubleshooting.*', '', response, flags=re.IGNORECASE | re.DOTALL)
                return response
            else:
                return "A problem occured. Please try again later."
        except Exception as e:
            logging.error("trying again because "+ str(e))
            return "A problem occured. Please try again later."
