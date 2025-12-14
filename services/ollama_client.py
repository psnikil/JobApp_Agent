from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser


"""
Make all fucntions to be able o be used a tools for LLMs orchestrator   
"""


# TODO: make a general class for config of LLM , then make two classes that inherite the llm class
#  One should be a stochastic generator, and the other the detetermistic generator
# this is to split 'nodes' from 'routers'

class OllamaConfig(BaseSettings):
    model: str = "gpt-oss"
    api_url: str = "http://localhost:11434/v1"
    temperature: float = 0.7

class OllamaModelConfig(BaseModel):
    temperature: float = 0.7
    max_tokens: int 
    top_p: float 
    top_k: int
    frequency_penalty: float 
    presence_penalty: float

class RouteQuery(BaseModel):
    """Route a user query to the most relevant Option out of the given:
        * internal knowledge
        * job description
        * overleaf resume
    """

    Tool_use: Literal["update_documents", "internal_knowledge", "None"] = Field(
        ...,
        description="Given a user prompt choose to route it to job description or overleaf resume or use the LLMs internal knowledge.",
    )
        

class OllamaClient:
    def __init__(self, config: OllamaConfig):
        self.config = config

        # TODO: understand if config llm them modify for each fucntion or config llm for each function


    def chat_llm_f(self, query:str) -> str:
        """
        This is a simple chat function using LLM to answer user queries.

        Args:
            query (str): The user query.

        Returns:
            str: The answer from the LLM.
        """


        chat_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.7,
                    stream_usage=True,
                )

        system_prompt = '''
                        You are an helpful and knowledgeable assistant. Help the user by asnwer their questions.
                        '''
        # question = 'How are you?'
        # print("the query is: ", query)

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]

        )

        chat_llm_chain = prompt | chat_llm | StrOutputParser()
        answer = chat_llm_chain.invoke({"question": query})
        return answer

    def summaries_readme_llm_f(self,content:str, project_name:str) -> str:
        """
        This function summarizes the README.md file of a project.

        Args:
            content (str): The content of the README.md file.
            project_name (str): The name of the project.

        Returns:
            str: The summary of the README.md file.
        """

        summary_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.5,
                    stream_usage=True,
                )

        summary_system_prompt = '''
                        You are an expert in summarizing the README.md files of projects for 
                        extracting the key information useful for the users resume.
                        You are given the content from the project along with the name of the project folder.
                        The summary should contain the following:
                        * The tech stack 
                        * The project description
                        * The project objectives
                        * The project outcomes
                        * The project challenges
                        * The project solutions
                        * The project learnings
                        the summary should be concise and retain all the key information.
                        '''
        # question = "# Local Chess\n\nA full-stack chess application for playing chess locally against an AI engine or another player. Built with React/TypeScript frontend and Python/FastAPI backend, powered by Stockfish chess engine.\n\n## Features\n\n- **Player vs AI**: Play against Stockfish engine with customizable difficulty levels\n- **Local Multiplayer**: Play against another player on the same device or local network\n- **Move Rating System**: Real-time move evaluation (brilliant, good, inaccuracy, mistake, blunder)\n- **Training Mode**: Get move suggestions and hints to improve your game\n- **Game Analysis**: Comprehensive post-game analysis with move-by-move breakdown\n- **Fully Local**: No internet connection required, runs entirely on your machine\n\n## Architecture Overview\n\nThe application follows a client-server architecture with three main layers:\n\n```\n┌──────────────────────────────────────────┐\n│         Frontend (React + TS)            │\n│   -  Interactive chessboard UI           │\n│   -  Game state management               │\n│   -  Real-time updates via WebSocket     │\n└──────────────────────────────────────────┘\n                    ↕\n┌──────────────────────────────────────────┐\n│        Backend (FastAPI + Python)        │\n│   -  Game logic & validation             │\n│   -  WebSocket server                    │\n│   -  Move analysis & rating              │\n└──────────────────────────────────────────┘\n                    ↕\n┌──────────────────────────────────────────┐\n│      Chess Engine (Stockfish)            │\n│   -  AI move generation                  │\n│   -  Position evaluation                 │\n│   -  Move suggestions                    │\n└──────────────────────────────────────────┘\n```\n\n### Frontend Layer\nBuilt with modern React framework (Vite) and TypeScript. Handles user interactions, board visualization using `react-chessboard`, and communicates with backend via REST API and WebSocket for real-time gameplay.\n\n### Backend Layer\nFastAPI-based server managing game sessions, move validation with `python-chess` library, and coordination with Stockfish engine. Supports both HTTP endpoints and WebSocket connections for real-time multiplayer synchronization.\n\n### Chess Engine Layer\nStockfish integrated via UCI protocol, providing AI opponents at various difficulty levels, position evaluations, and move quality ratings.\n\n## Project Structure\n\n```\nlocal_chess/\n├── frontend/                  # React + TypeScript frontend\n│   ├── src/\n│   │   ├── components/        # React components (Board, Game, Analysis, Settings)\n│   │   ├── services/          # API and WebSocket clients\n│   │   ├── hooks/             # Custom React hooks\n│   │   ├── types/             # TypeScript type definitions\n│   │   ├── utils/             # Helper functions\n│   │   └── styles/            # CSS/styling\n│   ├── public/                # Static assets (images, sounds)\n│   ├── package.json\n│   ├── vite.config.ts\n│   └── README.md              # Frontend documentation\n│\n├── backend/                   # FastAPI + Python backend\n│   ├── app/\n│   │   ├── api/               # API routes (game, analysis, websocket)\n│   │   ├── services/          # Business logic (game, engine, analysis)\n│   │   ├── models/            # Data models\n│   │   ├── core/              # Core functionality (config, engine wrapper)\n│   │   ├── schemas/           # Pydantic request/response schemas\n│   │   └── main.py            # Application entry point\n│   ├── engines/               # Stockfish binary\n│   ├── tests/                 # Backend tests\n│   ├── requirements.txt\n│   └── README.md              # Backend documentation\n│\n├── docker-compose.yml         # Docker setup\n├── .gitignore\n└── README.md                  # This file\n```\n\n## Technology Stack\n\n**Frontend:**\n<!-- This has to be more specific , prolly will use nextJS -->\n- React 18 + TypeScript\n- Vite (build tool)\n- chess.js (game logic)\n- react-chessboard (UI component)\n- Axios (HTTP client)\n- WebSocket API\n\n**Backend:**\n- Python 3.10+\n- FastAPI (web framework)\n- python-chess (chess logic)\n- Stockfish 16+ (chess engine)\n- uvicorn (ASGI server)\n- Pydantic (data validation)\n\n## Quick Start\n\n### Prerequisites\n- Node.js 18+\n- Python 3.10+\n- Stockfish chess engine binary\n\n### Installation\n\n1. **Clone repository**\n```bash\ngit clone https://github.com/psnikil/local_chess.git\ncd chess-master\n```\n\n2. **Setup Backend**\n```bash\ncd backend\npython -m venv venv\nsource venv/bin/activate  # Windows: venv\\Scripts\\activate\npip install -r requirements.txt\n```\n\n3. **Setup Frontend**\n```bash\ncd frontend\nnpm install\n```\n\n4. **Configure Environment**\n\nBackend `.env`:\n```bash\nSTOCKFISH_PATH=./engines/stockfish\nHOST=0.0.0.0\nPORT=8000\n```\n\nFrontend `.env`:\n```bash\nVITE_API_URL=http://localhost:8000\nVITE_WS_URL=ws://localhost:8000\n```\n\n### Running the Application\n\n**Terminal 1 - Backend:**\n```bash\ncd backend\nuvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n```\n\n**Terminal 2 - Frontend:**\n```bash\ncd frontend\nnpm run dev\n```\n\nAccess at `http://localhost:5173`\n\n### Local Network Play\nUpdate frontend `.env` with your local IP (e.g., `http://192.168.1.100:8000`) and share the frontend URL with other players on your network.\n\n## Game Modes\n\n### Player vs AI\n- Adjustable difficulty: Beginner to Expert\n- Customizable engine depth and skill level\n<!-- Test this , this is not certain -ai generated -->\n- AI response time: 100ms - 3s based on difficulty \n\n### Local Multiplayer\n- Hot-seat: Two players on same device\n- Network: Players on same local network\n- Real-time synchronization via WebSocket\n\n## Documentation\n\n- **Frontend**: See `frontend/README.md` for component architecture, state management, and UI details\n- **Backend**: See `backend/README.md` for API endpoints, service layers, and engine integration\n- **API Reference**: Available at `http://localhost:8000/docs` when backend is running\n\n## Testing\n\n```bash\n# Backend tests\ncd backend\npytest tests/ -v\n\n# Frontend tests\ncd frontend\nnpm test\n```\n\n## License\n\nMIT License - see LICENSE file\n\n---\n\n**Built with ♟️ by psnikil**\n\n',"
        summary_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=summary_system_prompt),
                HumanMessage(content=f"The content to be summarized is:{content}")
            ]
        )

        summary_llm_chain = summary_prompt | summary_llm | StrOutputParser()
        summary = summary_llm_chain.invoke({"content": content})
        return summary

    # TODO: update function such that it goes through each section and updates it
    def update_resume_llm_f(self, jd_content:str, 
                            project_content:str, 
                            resume_content:str) -> str:

        """
        This function updates the resume content based on:
        job description
        project content
        resume content
        The modification is done using LLM.

        Args:
            jd_content (str): Job description content.
            project_content (str): Project content.
            resume_content (str): Resume content.

        Returns:
            str: Updated resume content.

        """
        resume_content_len = len(resume_content)
        tokens = int(resume_content_len / 4.0)
        # adding padding so the ouput limit is not an hard restriction
        tokens = int(tokens*1.15)
        update_resume_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.5,
                    stream_usage=True,
                )

        update_resume_system_prompt = f"""
                                You are an expert in updating the resume of a candidate for a job application.
                                You are given summaries of all the projects the candidate has worked on.
                                You are given the job description pf the job the candidate is applying for.
                                You are given the current resume of the candidate in an object format which you need to update.
                                The format of the current resume is the key as the section name and the value is the content of the section.
                                # Rules to follow when updating the resume
                                1. You need to update the resume of the candidate based on the job description and the projects the candidate has worked on.
                                2. You should only update the content of the resume.
                                3. Do not add any new sections or information which is not present in the current resume or projects summaries
                                4. you output should be in the same format as the current resume. DO NOT CHANGE THE KEY NAMES, only update the values
                                5. The output of resume content should be within the character limit of {int(resume_content_len * 1.15)}.
                                6. Update the resume such that the resume pass ATS (Automated Resume Screening) and is more likely to get selected for the job.
                                You will be rewarded  $10000 for every resume that passed the resume screening and for following all the above rules.

                                """
        query_content = f"""
                        The job description I am applying for is:{jd_content}.
                        The summaries of the projects I have worked on are:{project_content}.
                        My current resume is:{resume_content}.
                        Update my resume based on the job description and the projects I have worked on.
                        """
        update_resume_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=update_resume_system_prompt),
                HumanMessage(content=query_content)
            ]
        )
        update_resume_llm_chain = update_resume_prompt | update_resume_llm | StrOutputParser()

        updated_resume = update_resume_llm_chain.invoke({"resume_content": resume_content, "jd_content": jd_content, "project_content": project_content})

        return updated_resume

    # TODO: try and extract the resume content using an llm rather than the class
    # Not used
    def extract_resume_llm_f(self, resume_content:str) -> str:
        """
        This function extracts the resume content from the given resume in latex format.
        
        Args:
            resume_content (str): The content of the resume in latex format.

        Returns:
            str: The extracted resume content.
        """
        
        extract_resume_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.0,
                    stream_usage=True,
                )

        extract_resume_system_prompt = """
                                You are an expert in extracting the resume content from the given resume.
                                You are given the resume in latex format.
                                Your job is to extract the content of resume and return only the content as string.
                                The formart returned should have header for each setion of the resume followed by the content of the section.
                                Do not include any formatting or structure or latex syntax of the resume in the returned content.
                                """
        query_content = f"""
                        The resume is:```{resume_content}```.
                        Extract the content of the resume and return only the content as string.
                        The formart returned should have header for each setion of the resume followed by the content of the section.
                        Do not include any formatting or structure or latex syntax of the resume in the returned content.
                        """
        extract_resume_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=extract_resume_system_prompt),
                HumanMessage(content=query_content)
            ]
        )
        extract_resume_llm_chain = extract_resume_prompt | extract_resume_llm | StrOutputParser()

        extracted_resume = extract_resume_llm_chain.invoke({"resume_content": resume_content})

        return extracted_resume

    # fucntion to update the content of latex code without touching the sytax, formatting, etc
    def update_latex_llm_f(self, latex_content:str, updated_section_content:tuple) -> str:
        """
        This function updates the content of the latex code without 
        touching the formatting, syntax or structure of the latex file.
        
        Args:
            latex_content (str): The content of the latex file.
            updated_section_content (tuple): section name,updated content of the section.

        Returns:
            str: The updated content of the latex file.
        """
        latex_content_len = len(latex_content)
        tokens = int(len(latex_content) / 4.0)
        # adding padding so the ouput limit is not an hard restriction
        tokens = int(tokens*1.15)
        update_latex_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.0,
                    max_tokens=tokens,
                )
        resume_section, updated_content = updated_section_content
        update_latex_system_prompt = """
                                You are an expert is modifying the contents of the larex section without touching the formatting or structure of the latex file.
                                You are given a section of the users resume in latex.
                                You are given the updated content of the same section in plain text/markdown format.
                                If the provided section such as name, email, phone number, linkedin profile link, etc which are unlikly to change, do not modify.
                                Your job is to modify the latext content without touching the formatting, syntax or structure of the latex file.
                                The returned content should be in the same format as the input latex content.
                                """
        query_content = f"""
                        The latex content of a section of the section :{resume_section} is :```{latex_content}```.
                        The updated content of the section :{resume_section} is :```{updated_content}```.
                        Update the latex content of the section :{resume_section} without touching the formatting, syntax or structure of the latex file.
                        The returned content should be in the same format as the input latex content.
                        """
        update_latex_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=update_latex_system_prompt),
                HumanMessage(content=query_content)
            ]
        )
        update_latex_llm_chain = update_latex_prompt | update_latex_llm | StrOutputParser()

        updated_latex_content = update_latex_llm_chain.invoke({"resume_section": resume_section, "latex_content": latex_content, "updated_content": updated_content})

        return updated_latex_content

    #  function to update the cover letter using the resume content, project content and the job description
    def update_cover_letter_llm_f(self, resume_content:str, 
                                    project_content:str, 
                                    job_description:str, 
                                    original_cover_letter:str) -> str:

        """
        This function updates the cover letter based on the 
        resume content, project content and the job description.

        Args:
            resume_content (str): The content of the resume.
            project_content (str): The content of the project.
            job_description (str): The description of the job.
            original_cover_letter (str): The original cover letter.

        Returns:
            str: The updated cover letter.
        

        """
        
        update_cover_letter_llm = ChatOpenAI(
                    api_key="ollama",
                    model= self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.5,
                    stream_usage=True,
                )
        update_cover_letter_system_prompt = """
                                You are an expert in updating the cover letter based on the resume content, project content and the job description.
                                You are given the resume content, project content and the job description.
                                The users cover letter is provided, it is in markdown format.
                                Instructions:
                                1. Your job is to update the cover letter based on the resume content, project content and the job description.
                                2. The length should not exceed 1 page.
                                3. Do not add any new infomation not present in the resume content, project content and job description
                                4. Base your updates to the cover letter based on the key requirements of the job description.
                                5. The cover letter should pass the ATS check and should be optimized for job success rate.
                                6. The returned content should be in the same format as the input cover letter content.
                                
                                """
        query_content = f"""
                        The resume content is:```{resume_content}```.
                        The project content is:```{project_content}```.
                        The job description is:```{job_description}```.
                        My cover letter is:```{original_cover_letter}```.
                        Update the cover letter based on the resume content, project content and the job description.
                        The returned content should be in the same format as the input cover letter content.
                        """
        update_cover_letter_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=update_cover_letter_system_prompt),
                HumanMessage(content=query_content)
            ]
        )
        update_cover_letter_llm_chain = update_cover_letter_prompt | update_cover_letter_llm | StrOutputParser()

        updated_cover_letter = update_cover_letter_llm_chain.invoke({"resume_content": resume_content, "project_content": project_content, "job_description": job_description, "original_cover_letter": original_cover_letter})
        # print(f"the updated cover letter in the node is {updated_cover_letter}")
        return updated_cover_letter

    def router_llm_f(self, query: str)-> RouteQuery:
        """
        This function routes the user query to the appropriate node.
        
        Args:
            query (str): The user query.

        Returns:
            RouteQuery: The route query.
        """
        router_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0,
                )
            
        structured_llm_router = router_llm.with_structured_output(RouteQuery)

        system = '''
                    You are an expert at routing a user question to either "update documents" tool or use internal knowledge.
                    The update_documents tool is for updating the user resume and cover letter when the user provides a valid URL of the job description.
                    Follow these rules when choosing the tool to use:
                    - If the user query is related to a job application, a valid URL has to be provided. If no URL respond with "None".
                    - If the user query is related to the user's resume, respond with "update_documents".
                    - if the question is general and not related to the user's resume or job application, respond with "internal_knowledge".
                    Respond with "update_documents" or "internal_knowledge" or "None" only.
                    '''

        route_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "{query}"),
            ]
        )

        question_router = route_prompt | structured_llm_router

        route = question_router.invoke(
            {"query": query}
        )

        return route

if __name__ == "__main__":
    llm_config = OllamaConfig()
    llm = OllamaClient(llm_config)
    ans = llm.chat_llm_f("Hello, how are you")
    print(ans)