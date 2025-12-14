# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
import os
from utils.resume_parser import ResumeParser
from utils.web_crawler import web_crawler
import pyoverleaf
import zipfile
import re
import shutil

class Reader:
    def __init__(self):
        # self.file_path = file_path
        pass
    # def read_readme(self):
    #     project_data = {}
    #     if os.path.exists(self.file_path) and os.path.isdir(self.file_path):
    #         try:
    #             for project_name in os.listdir(self.file_path):
    #                 project_dir = os.path.join(self.file_path, project_name)
    #                 if os.path.isdir(project_dir):
    #                     readme_path = os.path.join(project_dir, 'README.md')
    #                     if os.path.exists(readme_path):
    #                         try:
    #                             with open(readme_path, 'r', encoding='utf-8') as f:
    #                                 project_data[project_name] = f.read()
    #                         except IOError as e:
    #                             print(f"Error reading {readme_path}: {e}")
    #                             project_data[project_name] = f"Error reading README.md: {e}"
    #                         except Exception as e:
    #                             print(f"An unexpected error occurred with {readme_path}: {e}")
    #                             project_data[project_name] = f"An unexpected error: {e}"
    #                     else:
    #                         project_data[project_name] = "No README.md"
    #         except OSError as e:
    #             print(f"Error accessing projects directory {self.file_path}: {e}")
    #             return {"error": f"Error accessing projects directory: {e}"}

    #     return project_data

    # Function to get the resume from overleaf or local tex file
    def get_resume():
        """ 
        Get the resume from overleaf using user defined ENV variables or local .tex file.
        If the .tex file does not exist locally, fetch it from Overleaf.

        Returns:
            resume_content(str): The resume content

        """

        load_dotenv()

        # Check if the active folder and resume.tex file is specified in .env
        resume_path = os.getenv('RESUME_PATH', './data/resume.tex')
        print(f"Resume path is : {resume_path}")
        parser = ResumeParser()

        # Check if the resume.tex file exists locally
        if os.path.exists(resume_path):
            print(f"Using local resume from {resume_path}")
            # with open(resume_path, 'r') as file:
            
            resume_content = parser.parse(resume_path)
            print(f"Resume content: {resume_content}")

            return resume_content
        # If the .tex file does not exist locally, fetch it from Overleaf
        else:
            api = pyoverleaf.Api()
            try:
                api.login_from_browser()
                projects = api.get_projects()
                # print(f"projects are : {projects}")
                project_id = projects[0].id
                print(f"Downloading project {project_id}...")
                
                # Download the project as a zip file
                zip_path = "./data/project.zip"
                api.download_project(project_id, zip_path)
                
                # Unzip the downloaded project
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall("./data/temp_unzipped")
                
                # Read the resume.tex file from the unzipped folder
                extracted_resume_path = "./data/temp_unzipped/resume.tex"
                print(f"Extracted resume path: {extracted_resume_path}")
                
                resume_content = parser.parse(extracted_resume_path)
                # Clean up: remove the zip file and temporary unzipped folder
                final_resume_path = './data/resume.tex'
                shutil.move(extracted_resume_path, final_resume_path)
                print(f"Moved resume.tex to {final_resume_path}")
                
                # Clean up: remove the zip file and temporary unzipped folder
                os.remove(zip_path)
                shutil.rmtree("./data/temp_unzipped")
                    
                return resume_content
            
            except Exception as e:
                print(f"An error occurred: {e}")
                # Revert to previous functionality if fetching from Overleaf fails

    def read_readme(path)->dict[str,str]:       
        """
        Read the README.md files from the given directory.

        Args:
            path (str): The path to the directory containing the README.md files.

        Returns:
            dict[str, str]: A dictionary where the keys are the project names and the values are the README.md contents.
        """
        project_data = {}
        if os.path.exists(path) and os.path.isdir(path):
            try:
                for project_name in os.listdir(path):
                    project_dir = os.path.join(path, project_name)
                    if os.path.isdir(project_dir):
                        readme_path = os.path.join(project_dir, 'README.md')
                        if os.path.exists(readme_path):
                            try:
                                with open(readme_path, 'r', encoding='utf-8') as f:
                                    project_data[project_name] = f.read()
                            except IOError as e:
                                print(f"Error reading {readme_path}: {e}")
                                project_data[project_name] = f"Error reading README.md: {e}"
                            except Exception as e:
                                print(f"An unexpected error occurred with {readme_path}: {e}")
                                project_data[project_name] = f"An unexpected error: {e}"
                        else:
                            project_data[project_name] = "No README.md"
            except OSError as e:
                print(f"Error accessing projects directory {path}: {e}")
                return {"error": f"Error accessing projects directory: {e}"}

        return project_data

    def extract_jd(query:str)->str:
        """ 
        Extract the job descrption from the extracted url from the user prompt

        Args:
            query (str): The user query

        Returns:
            jd_content(str): The job description
        """
        question = query
        url_pattern = r'https?://[^\s]+'
        match = re.search(url_pattern, question)
        print(f"URL pattern match is : {match.group(0)}")
        if match:
            url = match.group(0)
            jd_data = web_crawler.extract_body_content(url)
        else:
            url = None

        # url = "https://logically.bamboohr.com/careers/25"
        # print(f"Job description is : {jd_data}")

        

        return jd_data or "No Job description found"




    


