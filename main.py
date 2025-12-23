from langgraph.graph import END, StateGraph, START
from IPython.display import display, Image
from graph.nodes import Nodes,GraphState
from graph.router import Router
from services.ollama_client import OllamaConfig
from typing_extensions import TypedDict
from typing import List
from pprint import pprint
import io
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# class GraphState(TypedDict):
#     """
#     Represents the state of our graph.

#     Attributes:
#         query: query
#         generation: LLM generation
#         documents: list of documents
#     """

#     query: str
#     generation: str
#     context: str
#     resume_content: str
#     jd_content: str
#     project_content: str
#     cover_letter_content: str
#     jd_url:str
#     Tool_Used: List[str]




def build_graph():

    state = GraphState()
    
    workflow = StateGraph(GraphState)
    workflow_nodes = Nodes(state)
    workflow_routers = Router(state)
    
    workflow.add_node("get_data", workflow_nodes.get_data)
    workflow.add_node("chat", workflow_nodes.chat)
    workflow.add_node("summarise_projects", workflow_nodes.summarise_projects)
    workflow.add_node("update_resume", workflow_nodes.update_resume)
    workflow.add_node("update_latex", workflow_nodes.update_latex) #updates and generates the latex file
    workflow.add_node("update_cover_letter", workflow_nodes.update_cover_letter)
    workflow.add_node("transcription_task", workflow_nodes.transcription_task)


    # Build the graph
    workflow.add_conditional_edges(
        START,
        workflow_routers.route_query,
        {
            "update_documents": "get_data",
            "internal_knowledge": "chat",
            "transcription": "transcription_task",
            "end": END,
        },
    )

    workflow.add_conditional_edges( 
        "chat",
        workflow_routers.route_query,
        {
            "internal_knowledge": END,
            "update_documents": END,
            "transcription": END,
            "end": END,
        },
    )

    workflow.add_edge("get_data", "summarise_projects")
    workflow.add_edge("summarise_projects", "update_resume")
    workflow.add_edge("update_resume", "update_latex")
    workflow.add_edge("update_latex", "update_cover_letter")
    workflow.add_edge("transcription_task", END)

    # Compile
    app = workflow.compile()


    app = workflow.compile()
    # debug to check the flow of the agent
    # graph_png_bytes = app.get_graph().draw_mermaid_png()
    # img = Image.open(io.BytesIO(graph_png_bytes))
    # img.show()
    

    return app


if __name__ == "__main__":
    agent = build_graph()
    # "I am applying for this job https://ohme-ev.com/job-postings/?gh_jid=4694069101&gh_src=05b7581f6us"
    inputs = {"query": "Can you give me a summary of the video?"}
    for output in agent.stream(inputs):
        for key, value in output.items():
            # Node
            pprint(f"Node '{key}':")
            # Optional: print full state at each node
            # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
        pprint("\n---\n")

    # Final generation
    pprint(value.keys())