from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
import os


"""
Make all functions to be able o be used a tools for LLMs orchestrator   
"""


# TODO: make a general class for config of LLM , then make two classes that inherit the llm class
#  One should be a stochastic generator, and the other the deterministic generator
# this is to split 'nodes' from 'routers'

# Get the ollama model from the .env file
# DEFAULT MODEL REQUIRES A 16GB GPU OR 16GB OF RAM
ollama_model  = os.getenv('OLLAMA_MODEL', 'gpt-oss')

class OllamaConfig(BaseSettings):
    model: str = ollama_model
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
        * update_documents
        * transcription
    """

    Tool_use: Literal["update_documents", "internal_knowledge", "None","Transcription"] = Field(
        ...,
        description="Given a user prompt choose to route it to job description or overleaf resume, transcription or use the LLMs internal knowledge.",
    )
        

class OllamaClient:
    def __init__(self, config: OllamaConfig):
        self.config = config

        # TODO: understand if config llm them modify for each function or config llm for each function


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
                        You are an helpful and knowledgeable assistant. Help the user by answer their questions.
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
            You are an project summarisation agent

            Your task is summarise the given README.md file of a project.
            The summary should include any relevant information which can be used to update a resume.
            The summary should retain all the key information present in README

            You are given the project name along with the README.md file for the project

            DO NOT ADD ANY ADDITONAL EXLPANATION OR COMMENTARY


            For example, the summary should contain:
            - The tech stack (frameworks, platforms, libraries, systems.)
            - The project description (What the project is about)
            - The project objectives (What the project has achieved)
            - The project challenges&solutions (What the project solves)
            '''
        
        query_content = f"""
            PROJECT NAME:
            <<<
            {project_name}
            >>>

            PROJECT README:
            <<<
            {content}
            >>>

            Create a summary for the above project following the system instructions
            """
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
                            resume_content:str,
                            resume_section:str) -> str:

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
        # adding padding so the output limit is not an hard restriction
        tokens = int(tokens*1.15)
        update_resume_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.5,
                    stream_usage=True,
                )
        # creating a conditional system prompt as smaller models struggle with a generic system prompt
        if resume_section.lower() == 'summary':
            update_resume_system_prompt = f"""
            You are a resume content optimization agent.

            Your task is to UPDATE the content of GIVEN resume section so it best matches
            a given set of job description keywords, using ONLY information from:
            - the current resume section content
            - the provided project summaries
            - the job description keywords

            You must NOT invent new experience, skills, tools, or projects.

            You must follow this process internally:
            Step 1: Update the content based on the technologies from 
            the project summaries and job description keywords.

            Step 2: Rewrite ALL retained content aggressively to:
            - maximize alignment with job description keywords
            - use ATS-friendly terminology
            - clearly emphasize impact and responsibilities
            - MAINTAIN THE FORMAT TO THE SAME AS THE INPUT RESUME SECTION

            CONTENT BUDGET RULE:
            - Do NOT increase the length of the section over {resume_content_len} characters.

            Rules:
            - MAINTAIN THE FORMATTING OF THE INPUT RESUME SECTION.

            Output ONLY the updated resume section content.
            Do NOT include explanations or commentary.

            """
        elif resume_section.lower() == 'skills and certificates':
            update_resume_system_prompt = f"""
            You are a resume content optimization agent.

            Your task is to UPDATE the content of GIVEN resume section so it best matches
            a given set of job description keywords, using ONLY information from:
            - the current resume section content
            - the provided project summaries
            - the job description keywords

            You must NOT invent new experience, skills, tools, or projects.

            You must follow this process internally:
            Step 1: Add skills from the project summaries and job description keywords.
            
            Step 2: Rewrite ALL retained content aggressively to:
            - maximize alignment with job description keywords
            - use ATS-friendly terminology
            - MAINTAIN THE FORMAT TO THE SAME AS THE INPUT RESUME SECTION

            CONTENT BUDGET RULE:
            - Do NOT increase the length of the section over {resume_content_len} characters.
            - Prefer replacement or removal over addition.

            Rules:
            - Do NOT add new sections.
            - Do NOT include information not grounded in the inputs.
            - MAINTAIN THE FORMATTING OF THE INPUT RESUME SECTION.

            Output ONLY the updated resume section content.
            Do NOT include explanations or commentary.


            """
        elif resume_section.lower() == 'experience':
            update_resume_system_prompt = f"""
            You are a resume content optimization agent.

            Your task is to UPDATE the content of GIVEN resume section so it best matches
            a given set of job description keywords, using ONLY information from:
            - the current resume section content
            - the provided project summaries
            - the job description keywords

            You must NOT invent new experience, skills, tools, or projects.

            You must follow this process internally:

            Step 1: Identify which bullets in the resume section
            are weakly relevant or irrelevant to the job description keywords.
            Remove the irrelevant bullets.

            Step 2: Rewrite ALL retained content aggressively to:
            - maximize alignment with job description keywords
            - use ATS-friendly terminology
            - clearly emphasize impact and responsibilitie
            - MAINTAIN THE FORMAT TO THE SAME AS THE INPUT RESUME SECTION

            CONTENT BUDGET RULE:
            - Do NOT increase the length of the section over {resume_content_len} characters.
            - Prefer replacement or removal over addition.

            Rules:
            - Do NOT add new sections.
            - Deleting bullets is allowed and encouraged when irrelevant.
            - Do NOT include information not grounded in the inputs.
            - MAINTAIN THE FORMATTING OF THE INPUT RESUME SECTION.

            Output ONLY the updated resume section content.
            Do NOT include explanations or commentary.
            """
        elif resume_section.lower() == 'projects':
            update_resume_system_prompt = f"""
            You are a resume content optimization agent.

            Your task is to UPDATE the content of GIVEN resume section so it best matches
            a given set of job description keywords, using ONLY information from:
            - the current resume section content
            - the provided project summaries
            - the job description keywords

            You must NOT invent new experience, skills, tools, or projects.

            PROJECT SELECTION POLICY:
            - The projects currently present in the resume section are the INITIAL selection.
            - The provided project summaries represent CANDIDATE replacement projects.
            - Prefer REPLACING weaker resume projects with stronger, more relevant projects.
            - Do NOT simply add more projects.
            - Do NOT include the same project more than once.

            You must follow this process internally: 

            Step 1: Identify which bullets or projects in the current resume section
            are weakly relevant or irrelevant to the job description keywords.

            Step 2: Identify which projects from the project summaries are strongly
            relevant to the job description keywords.

            Step 3: If a project from the summaries is more relevant than an existing
            resume project, REPLACE the weaker resume project with the stronger one.

            Step 4: Rewrite ALL retained content aggressively to:
            - maximize alignment with job description keywords
            - use ATS-friendly terminology
            - clearly emphasize impact and responsibilities
            - MAINTAIN THE FORMAT TO THE SAME AS THE INPUT RESUME SECTION

            CONTENT BUDGET RULE:
            - Do NOT increase the length of the section over {resume_content_len} characters.
            - Prefer replacement or removal over addition.

            Rules:
            - Do NOT change the section name.
            - Do NOT add new sections.
            - Deleting projects is allowed and encouraged when irrelevant.
            - Do NOT include information not grounded in the inputs.
            - MAINTAIN THE FORMATTING OF THE INPUT RESUME SECTION.

            Output ONLY the updated resume section content.
            Do NOT include explanations or commentary.
            """
        else:
            print(f'ERROR: SHOULD NOT HAVE REACHED HERE!!!!!!!!!. the section is {resume_section}')
            update_resume_system_prompt = f"""
            You are a resume content optimization agent.

            Your task is to UPDATE the content of ONE resume section so it best matches
            a given set of job description keywords, using ONLY information from:
            - the current resume section
            - the provided project summaries
            - the job description keywords

            You must NOT invent new experience, skills, tools, or projects.

            You are the ONLY agent responsible for deciding:
            - which bullets to keep
            - which bullets to modify
            - which bullets to delete
            - which projects to include or exclude

            You must follow this process internally:

            Step 1: For the given resume section, identify all bullets or items that are
            SUPPORTED by the job description keywords using:
            - existing resume content, OR
            - the project summaries

            Step 2: Rank all supported bullets or projects by relevance to the job description.

            Step 3: Rewrite the section by:
            - keeping and improving the MOST relevant bullets
            - removing bullets that are weakly relevant or irrelevant
            - selecting ONLY the most relevant projects from the project summaries
            - updating bullet wording to use ATS-friendly keywords

            CONTENT BUDGET RULE:
            - This resume must fit on ONE PAGE.
            - Prefer REMOVING lower-priority bullets or projects over adding new ones.
            - Do NOT expand the section significantly beyond its original length.

            Rules:
            - Do NOT change the section name.
            - Do NOT add new sections.
            - Do NOT include information not grounded in the inputs.
            - Deleting bullets is allowed and encouraged when they are irrelevant.
            - Adding projects is allowed ONLY if they replace less relevant content.

            Output ONLY the updated resume section content.
            Do NOT include explanations or commentary.
            """
        
        query_content = f"""
            JOB DESCRIPTION KEYWORDS:
            <<<
            {jd_content}
            >>>

            PROJECT SUMMARIES (candidate replacement projects):
            <<<
            {project_content}
            >>>

            CURRENT RESUME SECTION ({resume_section}):
            <<<
            {resume_content}
            >>>

            TASK:
            Update the resume section following the system instructions.
            Return ONLY the updated resume section content.
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
    
    # fucntion to extract the key words from the job description for resume updating
    # TODO: change the return type to be a certain class
    def jd_key_words_resume_llm_f(self,job_description:str) -> str:
        """
        This fucntion extracts the key words from the job description for resume updating

        Args:
            job_description(str): The extracted job description

        Returns:
            str: The key words from job_description
        """

        extract_key_words_llm = ChatOpenAI(
            api_key="ollama",
            model=self.config.model,
            base_url=self.config.api_url,
            temperature=0.0,
            stream_usage=True,
        )

        extract_key_words_system_prompt = """
            You are an ATS keyword extraction agent.

            Your task is to analyze a job description and extract all keywords, skills,
            and requirements that an Applicant Tracking System (ATS) would use to
            screen resumes.

            You must extract information ONLY from the job description.
            Do NOT infer, add, or guess missing requirements.

            Follow these rules:
            - Use exact wording from the job description when possible.
            - Normalize minor variations (e.g., "Python programming" → "Python").
            - Do NOT include explanations or commentary.
            - If a category is not present, return an empty list.

            Return the output in the following JSON format:

            {
            "job_title": string,
            "hard_skills": [string],
            "soft_skills": [string],
            "tools_and_technologies": [string],
            "responsibilities": [string],
            "required_qualifications": [string],
            "preferred_qualifications": [string],
            "keywords": [string]
            }

            Definitions:
            - hard_skills: measurable technical abilities (e.g., Python, SQL, ML).
            - soft_skills: communication, leadership, collaboration, etc.
            - tools_and_technologies: frameworks, platforms, libraries, systems.
            - responsibilities: job duties written as short action phrases.
            - required_qualifications: mandatory education, experience, or skills.
            - preferred_qualifications: nice-to-have skills or experience.
            - keywords: important ATS terms not covered above (domain terms, role terms).

            Output ONLY valid JSON.
            """
        
        query_content = f"""
            JOB DESCRIPTION:
            <<<
            {job_description}
            >>>

            Extract ATS-relevant keywords and requirements following the system instructions.

            """
        
        extract_key_words_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=extract_key_words_system_prompt),
                HumanMessage(content=query_content)
            ]
        )
        extract_key_words_llm_chain = extract_key_words_prompt | extract_key_words_llm | StrOutputParser()

        extract_key_words = extract_key_words_llm_chain.invoke({"resume_content": job_description})

        return extract_key_words


    def jd_key_words_cl_llm_f(self,job_description:str) -> str:
        """
        This fucntion extracts the key words from the job description for cover letter updating

        Args:
            job_description(str): The extracted job description

        Returns:
            str: The key words from job_description
        """

        extract_key_words_llm = ChatOpenAI(
            api_key="ollama",
            model=self.config.model,
            base_url=self.config.api_url,
            temperature=0.0,
            stream_usage=True,
        )

        extract_key_words_system_prompt = """
            You are a cover letter focus extraction agent.

            Your task is to identify the MOST IMPORTANT job requirements
            for writing a persuasive, role-specific cover letter.

            You are given structured ATS keyword output extracted from a job description.

            Select ONLY the most relevant items for a cover letter narrative.

            Follow these rules:
            - Choose at most 3–5 core skills or themes.
            - Choose at most 1–2 key responsibilities.
            - Prefer requirements that define the role’s core value.
            - Ignore boilerplate, generic soft skills, and minor tools.

            Return the output in the following JSON format:

            {
            "job_title": string,
            "core_skills": [string],
            "key_responsibilities": [string],
            "role_focus": string
            }

            Definitions:
            - core_skills: the most important skills that define success in the role
            - key_responsibilities: primary duties the role is judged on
            - role_focus: a short phrase summarizing what the role is about

            Output ONLY valid JSON.
            """
        
        query_content = f"""
            JOB DESCRIPTION:
            <<<
            {job_description}
            >>>

            Extract cover letter relevant keywords and focus following the system instructions.

            """
        
        extract_key_words_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=extract_key_words_system_prompt),
                HumanMessage(content=query_content)
            ]
        )
        extract_key_words_llm_chain = extract_key_words_prompt | extract_key_words_llm | StrOutputParser()

        extract_key_words = extract_key_words_llm_chain.invoke({"resume_content": job_description})

        return extract_key_words

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
            The format returned should have header for each section of the resume followed by the content of the section.
            Do not include any formatting or structure or latex syntax of the resume in the returned content.
            """
        query_content = f"""
            The resume is:```{resume_content}```.
            Extract the content of the resume and return only the content as string.
            The format returned should have header for each section of the resume followed by the content of the section.
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

    # function to update the content of latex code without touching the syntax, formatting, etc
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
        # approx number of tokens
        tokens = int(len(latex_content) / 4.0)
        # adding padding so the output limit is not an hard restriction
        tokens = int(tokens*1.20)
        update_latex_llm = ChatOpenAI(
                    api_key="ollama",
                    model=self.config.model,
                    base_url=self.config.api_url,
                    temperature=0.0,
                    max_completion_tokens=tokens,
                )
        resume_section, updated_content = updated_section_content
        update_latex_system_prompt = """
            You are a LaTeX content replacement agent.

            Your task is to update ONLY the textual content inside an existing LaTeX resume section,
            while preserving the original structure, formatting, and layout.

            You are given a section of the users resume in latex.
            You are given the updated content of the same section in plain text OR markdown format.
            You are given structural contraints derived from original latex content.

            STRICT RULES:
            - DO NOT MODIFY THE FORMATTING OR SYNTAX OR STRUCTURE OF THE LATEX
            - If the provided section contains name, email, phone number, linkedin profile link, etc which are unlikely to change, DO NOT MODIFY.
            - Do NOT include explanations or commentary.

            Output ONLY the updated latex
            """
        query_content = f"""
            RESUME SECTION:{resume_section}
            
            STRUCTURAL CONSTRAINTS:
            - Target length: approximately {latex_content_len} characters

            ORGINAL LATEX CONTENT CONTENT OF THE SECTION:{latex_content}
            
            UPDATED CONTENT OF THE SECTION:{updated_content}
            
            TASK:
            Replace the content of the latex code following the system instructions.
            Return ONLY the updated latex content.
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
            You are a cover letter optimization agent.

            Your task is to REWRITE an existing cover letter so it best matches
            a given set of job description keywords, while preserving the overall
            tone and structure of the original letter.

            Use ONLY information from:
            - the provided resume content
            - the provided project summaries
            - the provided job description keywords
            - the original cover letter

            You must NOT invent new experience, skills, tools, or projects.

            You must follow this process internally:

            Step 1: Identify the core role requirements and keywords from the job description.

            Step 2: Identify the MOST relevant skills and experiences from the resume
            that support those requirements.

            Step 3: Select AT MOST one or two highly relevant projects (only if they
            strengthen the narrative) and integrate them naturally as evidence.

            Step 4: Rewrite the cover letter to:
            - clearly explain why the candidate is a strong fit for the role
            - use ATS-friendly terminology from the job description
            - emphasize relevance over completeness
            - remain concise and persuasive

            CONTENT RULES:
            - The rewritten letter must not exceed the length of the original cover letter.
            - Prefer clarity and relevance over listing many skills.
            - Do NOT turn the cover letter into a resume-style summary.

            COMPANY-SPECIFIC CONTENT:
            - If the original cover letter mentions a specific company or role,
            generalize or adapt it to match the provided job description.
            - Do NOT hallucinate company-specific details not present in the inputs.

            FORMAT RULES:
            - Preserve the overall format and paragraph structure of the original letter.
            - Do NOT include explanations or commentary.

            Output ONLY the rewritten cover letter.
            """
        query_content = f"""
                        RESUME CONTENT:
                        <<<
                        {resume_content}
                        >>>

                        PROJECT SUMMARIES:
                        <<<
                        {project_content}
                        >>>

                        JOB DESCRIPTION KEY WORDS:
                        <<<
                        {job_description}
                        >>>

                        ORIGINAL COVER LETTER:
                        <<<
                        {original_cover_letter}
                        >>>

                        TASK:
                        rewrite the cover letter following the system instructions.
                        return ONLY the rewritten cover letter. 
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
                    You are an expert at routing a user question to either "update documents" tool, "transcription" tool or use internal knowledge.
                    The update_documents tool is for updating the user resume and cover letter when the user provides a valid URL of the job description.
                    The transcription tool is for transcribing a video file  ans answering the user query based on the transcription.
                    Follow these rules when choosing the tool to use:
                    - If the user query is related to a job application, a valid URL has to be provided. If no URL respond with "None".
                    - If the user query is related to the user's resume, respond with "update_documents".
                    - if the question is general and not related to the user's resume or job application, respond with "internal_knowledge".
                    - if the question is requires transcription of video file  respond with "transcription".
                    Respond with "update_documents" or "internal_knowledge" or "None" or "transcription" only.
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

    def transcript_llm_f(self, query: str, transcript: str)-> str:
        """
        This function uses LLM to generate a response to the user query based on the video transcript.

        Args:
            query (str): The user query.
            transcript (str): The transcript of the conversation.

        Returns:
            str: The response to the user query.
        """

        transcript_llm = ChatOpenAI(
                api_key="ollama",
                model= self.config.model,
                base_url=self.config.api_url,
                temperature=0.5,
                stream_usage=True,
            )

        transcript_system_prompt = f"""
        You are an expert at generating a response to a user query based on the video transcript.
        The video transcript is: {transcript}
        The user query is: {query}
        Generate a response to the user query based on the video transcript.
        """
        transcript_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=transcript_system_prompt),
                HumanMessage(content=query)
            ]
        )
        transcript_llm_chain = transcript_prompt | transcript_llm | StrOutputParser()
        transcript = transcript_llm_chain.invoke({"query": query, "transcript": transcript})
        return transcript

        
if __name__ == "__main__":
    # to check if the ollama model is configured correctly
    llm_config = OllamaConfig()
    llm = OllamaClient(llm_config)
    ans = llm.chat_llm_f("Hello, how are you")
    print(ans)