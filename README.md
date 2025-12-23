# Job Application Agent

**An intelligent, automated agent designed to streamline the job application process.**

The Job Application Agent leverages the power of Large Language Models (LLMs) to assist users in managing their job applications. It intelligently routes user queries, updates resumes and cover letters based on specific job descriptions, and manages the compilation of LaTeX resumes into PDFs.

## 🚀 Features

*   **Intelligent Query Routing**: automatically determines if a user wants to chat, update their resume, or extract information, routing to the appropriate tool using LangGraph.
*   **Resume Customization**: Takes a base LaTeX resume (local or from Overleaf) and tailors it to a specific job description.
*   **Job Description Scraping**: Extracts job description text directly from provided URLs (e.g., BambooHR, etc.).
*   **Project Summarization**: Reads local project `README.md` files to extract key technical details and achievements for inclusion in the resume.
*   **Cover Letter Generation**: Generates or updates cover letters to match the resume and job description, optimizing for ATS (Applicant Tracking Systems).
*   **PDF Generation**: Automatically compiles the updated LaTeX resume into a ready-to-send PDF.
*   **Conversational Interface**: Includes a chat capability for general queries and assistance.

## 🛠️ Tech Stack

*   **Core Framework**: [LangChain](https://python.langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/)
*   **LLMs**: Ollama (compatible with OpenAI API format), supporting models like `gpt-oss`.
*   **Resume Handling**: LaTeX, Overleaf API (`pyoverleaf`), `pdflatex`.
*   **Document Processing**: `BeautifulSoup4`, `pypandoc`, `MarkItDown`.
*   **Environment**: Python, Jupyter Notebook (currently).

## 📋 Prerequisites

Before running the agent, ensure you have the following installed:

*   **Python 3.10+**
*   **Ollama**: Installed and running locally (default url: `http://localhost:11434`).
*   **LaTeX Distribution**: `pdflatex` must be installed on your system (e.g., TeX Live) for PDF generation.
*   **Poppler**: For PDF processing (if required).
*  **Playright** has to be installed. After installing playright from pip, run: ``` python3 -m playright ```p

## ⚙️ Configuration

The project uses a `.env` file for configuration. Create a `.env` file in the root directory with the following variables:

```bash
# Path to your local resume.tex file
RESUME_PATH=/path/to/your/resume.tex

# Path to your projects directory containing READMEs
PROJECTS_PATH=/path/to/your/projects

# Path to your base cover letter
COVER_LETTER_PATH=/path/to/your/cover_letter.docx

# Overleaf Credentials (if fetching from Overleaf)
DATA_FOLDER=/path.to/data/folder

# Ollama model name
OLLAMA_MODEL="Model_name"
```

## 🏃 Usage

Currently, the project is structured as a Jupyter Notebook (`JobApp_Agent.ipynb`).

1.  Start your local Ollama instance.
2.  Open `JobApp_Agent.ipynb` in Jupyter Lab or VS Code.
3.  Run the cells to initialize the agent specific components (GraphState, Tools, Nodes).
4.  Invoke the graph with a user query:

```python
# Example usage in the notebook
response = app.invoke({"query": "I want to apply for this job: https://example.com/job/123"})
```

## 🏗️ Proposed Architecture

The project is evolving towards a modular, multi-file structure to ensure scalability and maintainability. Each component will be encapsulated in atomic classes.

### Module Structure

We aim to refactor the monolithic notebook into the following atomic packages:

*   **`graph/`**: application logic.
    *   `Agent`: Manages the LangGraph workflow and state.
    *   `Router`: Decides the path of execution (Chat vs. Application).
*   **`utils/`**: Specialized utilities.
    *   `ResumeParser`: Handles LaTeX parsing and section extraction.
    *   `Reader`: Class to read data
    *   `web_crawler`: Extracts job description from url
*   **`services/`**: External integrators.
    *   `LLMService`: Unified interface for Ollama/OpenAI.

## 🗺️ Roadmap

*   [ ] **Update the we scraper tool**: MModify the web scarper tool to extract the JD more accurately and efficiently .
*   [ ] **Support for multiple models**: Add support for the use of different models for different tasks
*   [ ] **Update the workflow**: update the flow such that an orchestrator agent can dynamically choose the required tools/state the agent should visit 
