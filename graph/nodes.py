from typing import List, TypedDict
from dotenv import load_dotenv
import os
import ast
import re
import json
# import llm client
from services.ollama_client import OllamaClient, OllamaConfig
from typing import List  
from pydantic import BaseModel
from typing import TypedDict

from utils.reader import Reader
from utils.web_crawler import web_crawler,extract_jd
from utils.resume_parser import ResumeParser
from utils.latex_helper import Latex_helper

from markitdown import MarkItDown
from Markdown2docx import Markdown2docx
import pypandoc
from utils.asr import Asr


class GraphState(TypedDict):
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
    resume_content: str|dict
    jd_content: str
    project_content: str
    cover_letter_content: str
    jd_key_words:str
    Tool_Used: List[str]

# # debug variable
# state = GraphState()

class Nodes:
    def __init__(self, state: GraphState):
        self.state = state
        config = OllamaConfig()
        # can create multiple instances for difference LLMs
        self.llm = OllamaClient(config)
        self.asr = Asr()
        

    def chat(self,state:GraphState) -> GraphState: # maybe look into if we need to pass state as an argument
        """
        Normal chat will llm based on the question

        Args:
        state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        """

        print("---LLM CHAT---")
        question = state["query"]

        answer = self.llm.chat_llm_f(question)
        state["generation"] = answer
        print(f'the answer is {answer}')
        self.state = state

        return state

    async def get_data(self,state:GraphState) -> GraphState:
        """
        This function is similar to an init function for the data.
        aka fetch the required data from the user's query.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        
        """
        print("---GET DATA---")

        query = state["query"]
        # have to use these as helper functions/ aka tools
        resume_content = Reader.get_resume()
        state['resume_content'] = resume_content
        state['jd_content'] = await Reader.extract_jd(query)
        self.state = state
        return state

    def summarise_projects(self,state:GraphState) -> GraphState:
        """
        This functions reads the README.md files from the user defined projects folder in .env
        The README.md in the highest level is read and update the state 

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates project

        """
        
        print("---SUMMARISE PROJECTS---")
        load_dotenv()
        projects_path = os.getenv('PROJECTS_PATH', 'projects')
        print(f"Projects path is : {projects_path}")
        project_data = Reader.read_readme(projects_path)
        print(f"Project data: {project_data}")
        # state['project_content'] = project_data

        summarized_content = {}
        for project in project_data:
            if project_data[project] == "No README.md" or not project_data[project]:
                print(f"No README.md found for {project} \n ")
                continue
                
            else:
                summary = self.llm.summaries_readme_llm_f(project_data[project],project)
                # print(f'the state after summary is {state["generation"]}')
                json_summary = summary.model_dump()
                content = ''
                for key,value in json_summary.items():
                    content+= f'{key}: {value} \n'
                summarized_content[project] = content

        # TODO: check if the dict is empty , otherwise say "No project data found"
        state["project_content"] = json.dumps(summarized_content, ensure_ascii=False, indent=2)
        print(f'The leght of summarised projects is {len(summarized_content)}')
        self.state = state
        return state
        
    def extract_jd_keywords_resume(self,state:GraphState) -> GraphState:
        """
        This fucntion extracts all the key words from the full job description for the resume

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates resume
        """

        print("---UPDATE JD KEY WORDS RESUME---")

        # This is the full JD
        jd_content = state['jd_content']
        jd_key_words = self.llm.jd_key_words_resume_llm_f(jd_content)
        state['jd_key_words'] = jd_key_words.model_dump_json()
        print(f'the jd key words for resume are: \n {jd_key_words}')
        self.state = state
        return state
    
    def extract_jd_keywords_cl(self,state:GraphState) -> GraphState:
        """
        This fucntion extracts all the key words from the full job description for the cover letter

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates resume
        """

        print("---UPDATE JD KEY WORDS CL---")

        # This is the full JD
        jd_content = state['jd_content']
        jd_key_words = self.llm.jd_key_words_cl_llm_f(jd_content)
        state['jd_key_words'] = jd_key_words.model_dump_json()
        print(f'the jd key words for cl are: \n {jd_key_words}')
        self.state = state
        return state




    def update_resume(self,state:GraphState) -> GraphState:
        """
        This function updates the resume based on the retrieved old resume, jd and projects

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates resume
        """

        print("---UPDATE RESUME---")
        load_dotenv()

        # Check if the active folder and resume.tex file is specified in .env
        resume_path = os.getenv('RESUME_PATH', './data/resume.tex')

        parser = ResumeParser()
        old_resume = self.state['resume_content']#parser.parse(resume_path)
        # old_resume = state['resume_content']
        jd_key_words = self.state['jd_key_words']
        project_summaries = self.state['project_content']

        print(f'the old resume is: \n {old_resume}')
        # print(f'the jd content is: \n {jd_content}')
        # print(f'the project content is: \n {project_content}')

        updated_resume = {}

        for resume_section, section_content in old_resume.items():
            # this is to ignore the header/Education section as this shouldnt be changed
            if resume_section == 'Header' or resume_section == 'Education':
                updated_resume[resume_section] = section_content
            else:
                response = self.llm.update_resume_llm_f(jd_key_words, project_summaries, section_content,resume_section)
                updated_resume[resume_section] = response.updated_content

        print(f'the updated resume is: \n {updated_resume}')
        state['generation'] = json.dumps(updated_resume, ensure_ascii=False, indent=2)
        state['resume_content'] = updated_resume
        self.state = state
        return state


    def update_latex(self,state:GraphState)-> GraphState:
        """
        This function creates the latex file based on the updated resume
        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates resume
        """

        print("---UPDATE LATEX---")
        load_dotenv()

        # Check if the active folder and resume.tex file is specified in .env
        resume_path = os.getenv('RESUME_PATH', 'resume.tex')

        resume_content = state['resume_content']
        if type(resume_content) == 'str':
            print("resume is a string")
            # coverting a json str back to dict
            resume_dict = json.loads(resume_content)
        else:
            print("resume is a dict")
            resume_dict = resume_content

        parser = ResumeParser()
        parser.parse(resume_path)

        
        # ignore the header and education section for latex update
        for section, content in resume_dict.items():
            if section == 'Header' or section == 'Education':
                print(f"Skipping section {section} for latex update")
                continue
            section_latex = parser.get_section_latex(section, resume_path)
            llm_response = self.llm.update_latex_llm_f(section_latex, (section, content))
            updated_section_latex = llm_response.latex
            print(f'the raw updated section {section} is {updated_section_latex} \n')
            # TODO: add static checks for escape sequences in the updated latex code
            sanitizer = Latex_helper()
            sanitized_latex = sanitizer.latex_static_sanitize(updated_section_latex)
            print(f'the sanitized updated section {section} is {sanitized_latex} \n')
            parser.update_section(section, sanitized_latex, True)
            
        
        parser.save("./data/resume_updated.tex")

        try:
            parser.generate_pdf("./data")
            print("SUCCESS: PDF generated.")
        except Exception as e:
            print(f"PDF Generation failed (expected if pdflatex missing): {e}")

        self.state = state
        return state

    def update_cover_letter(self,state:GraphState)-> GraphState:
        """
        This function updates the cover letter based on the updated resume content, job description and projects
        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates cover letter
        """

        print("---UPDATE COVER LETTER---")
        resume_content = state['resume_content']
        jd_key_words = state['jd_key_words']
        project_content = state['project_content']

        # read the cover letter docx file from the user defined cover letter path in .env
        cover_letter_path = os.getenv('COVER_LETTER_PATH', 'cover_letter.docx')
        md = MarkItDown()
        # get only the text content to type check is works
        cover_letter = (md.convert(cover_letter_path)).text_content
        print(f'the cover letter is: \n {cover_letter}')
        print(f"the len of resume content is: {len(resume_content)}")
        print(f"the len of project content is: {len(project_content)}")
        print(f"the len of jd content is: {len(jd_key_words)} and the jd content is: \n {jd_key_words}")
        updated_cover_letter = self.llm.update_cover_letter_llm_f(resume_content, project_content,jd_key_words,cover_letter)
        print(f'the updated cover letter is: \n {updated_cover_letter}')
        state['generation'] = updated_cover_letter
        state['cover_letter_content'] = updated_cover_letter

        pypandoc.convert_text(
            updated_cover_letter,
            to="docx",
            format="md",
            outputfile="./data/updated_cover_letter.docx"
            )

        self.state = state
        return state

    def transcription_task(self,state:GraphState)-> GraphState:
        """
        This fucntion transcribes given video and performs the user defined task
        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates resume

        """
        print("---TRANSCRIPTION TASK---")
        load_dotenv()
        video_path = os.getenv('VIDEO_PATH', 'video.mp4')
        query = state['query']
        audio_file = self.asr.extract_audio_ffmpeg(video_path)
        transcription = self.asr.transcribe(audio_file)
        print(f'The transcription is: \n {transcription["text"]}')
        answer = self.llm.transcript_llm_f(query, transcription['text'])
        state['generation'] = answer
        print(f'The answer through the transcription node is: \n {answer}')

        return state
        






    

        

