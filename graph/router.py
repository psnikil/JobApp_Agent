from services.ollama_client import OllamaClient, OllamaConfig
from typing import List  
from pydantic import BaseModel
from typing import TypedDict

class RouterState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        query: query
        generation: LLM generation
        documents: list of documents
    """

    query: str
    generation: str
    context: str
    resume_content: str
    jd_content: str
    project_content: str
    cover_letter_content: str
    jd_url:str
    Tool_Used: List[str]

class Router:
    def __init__(self, state):
        self.state = state
        config = OllamaConfig()
        self.llm = OllamaClient(config)

    def route_query(self,state:RouterState) -> str:
        """
        Route user query internal knowledge, jd or resume.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """

        print("---ROUTE QUESTION---")
        question = state["query"]
    
        # url_pattern = r'https?://[^\s]+'
        # match = re.search(url_pattern, question)
        # print(f"URL pattern match is : {match.group(0)}")
        # if match:
        #     state["jd_url"] = match.group(0)
        # else:
        #     state["jd_url"] = None
        

        source = self.llm.router_llm_f(question)

        
        if source.Tool_use == "update_documents":
            print("---ROUTE QUESTION TO UPDATE CV,COVER LETTER---")
            return "update_documents"
        elif source.Tool_use == "internal_knowledge":
            print("---ROUTE QUESTION TO INTERNAL KNOWLEDGE---")
            return "internal_knowledge"
        elif source.Tool_use == "Transcription":
            print("---ROUTE QUESTION TO TRANSCRIPTION---")
            return "transcription"
        elif source.Tool_use == "None":
            print("---NO JD URL, END AGENT---")
            return "end"
        self.state = state
        return "internal_knowledge"
