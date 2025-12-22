
import json

import re
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright

class web_crawler:
    def __init__(self,url:str):
        self.url = url
    def extract_body_content(self):
        """
        Extracts job description from various ATS platforms or falls back to generic scraping.
        Supported: BambooHR, Greenhouse, Lever, and Generic.
        
        Args:
            url (str): The URL of the webpage to scrape.
            
        Returns:
            str: The text content of the body, or an error message if extraction fails.
        """

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            print(f"Processing URL: {self.url}")

            # 1. BambooHR Handler
            if "bamboohr.com" in self.url and "/careers/" in self.url:
                print("Detected BambooHR URL")
                clean_url = self.url.split("?")[0].rstrip("/")
                if not clean_url.endswith("/detail"):
                    api_url = f"{clean_url}/detail"
                else:
                    api_url = clean_url
                
                headers["Accept"] = "application/json"
                print(f"API URL: {api_url}")
                try:
                    print("Fetching API content...")
                    resp = requests.get(api_url, headers=headers)
                    if resp.status_code == 200:
                        print("API request successful.")
                        data = resp.json()
                        desc = data.get("result", {}).get("jobOpening", {}).get("description")
                        if desc:
                            soup = BeautifulSoup(desc, 'html.parser').get_text(separator='\n', strip=True)
                            return soup
                except Exception as e:
                    print(f"BambooHR API failed: {e}. Falling back to generic scrape.")

            # Fetch page for other handlers / fallback
            print("Fetching page content...")
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # 2. Greenhouse Handler
            if "greenhouse.io" in self.url:
                print("Detected Greenhouse URL")
                content_div = soup.find('div', id='content') or soup.find('div', id='main')
                if content_div:
                    return content_div.get_text(separator='\n', strip=True)

            # 3. Lever Handler
            if "lever.co" in url:
                print("Detected Lever URL")
                # Lever often works well with generic body scrape if cleaned properly
                # But we can look for specific containers if needed e.g. .section-wrapper
                pass

            # 4. Generic Fallback
            print("Using generic fallback with cleanup")
            
            # Remove noise
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe", "svg", "button", "input"]):
                tag.decompose()
            
            # Try to find main content container
            main = soup.find('main') or soup.find('article') or soup.body or soup
            
            text = main.get_text(separator='\n', strip=True)
            # Clean excessive newlines
            return re.sub(r'\n{3,}', '\n\n', text)

        except Exception as e:
            return f"Error extracting content: {e}"
        
"""
This is a jd extraction class. With user inputted URL, it renders the page to fetch the HTML, then cleans the HTML,
scores each section(this is to dynamically pick the section the JD is likely in) and return the section
with the highest
"""
class extract_jd:
    def __init__(self) -> None:
        # the html tags to remove while parsing
        self.noise_tags = [
                "script", "style", "nav", "footer", "header", "noscript"
            ]
        # the css keywords to remove while parsing
        self.noise_keywords = [
            "nav", "menu", "footer", "header",
            "cookie", "consent", "subscribe",
            "apply", "login", "signup", "share"
        ]

        self.job_keywords = [
            "responsibilities", "requirements", "qualifications",
            "what you will do", "about the role", "job description"
        ]

        self.stop_phrases = [
            "about the company",
            "company overview",
            "similar jobs",
            "recommended jobs",
            "people also viewed",
            "more jobs",
            "explore more roles",
            "other jobs you may be interested in",
        ]

        self.score_len_multiplier = 1/200.0

        self.job_keywords_multiplier = 0.5

        self.list_item_bonus = 0.5

        self.score_threshold = 1.0

        self.fallback1_para = 3

    def fetch_rendered_html(self,url:str) -> str:
        """
        Fetches the fully rendered HTML content of the given URL using 
        playright to handle the JS rendering.
        """

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page =  browser.new_page()

                page.goto(url, timeout=30000)
                page.wait_for_selector("body")
                page.wait_for_timeout(2000)  # allow for JS to settle

                html = page.content()
                browser.close()
                return html
        except Exception as e:
            print('Error fetching rendered HTML:', e)
            return f"the error in fetching the rendered html is {e}"
        
    def clean_html(self, html: str) -> BeautifulSoup:
        """
        Cleans the html content by removing the html tags and css keywords

        Args:
        html (str): The html content to be cleaned
        
        Returns:
            BeautifulSoup: The cleaned html content
        """

        soup = BeautifulSoup(html, 'html.parser')

        # Remove the obvious noise tags
        for tag in self.noise_tags:
            for el in soup.find_all(tag):
                el.decompose()
        
        # Remove elements with CSS class names/id names
        for el in soup.find_all(True):
            if el.name:
                classes = " ".join(el.get("class", []))
                element_id = el.get("id", "")
                text = f"{classes} {element_id}".lower()


            if any(keyword in text for keyword in self.noise_keywords):
                el.decompose()
            
        return soup
    
    def extract_sections(self,soup: BeautifulSoup) -> list:
        """
        Extracts sections from the cleaned html content

        Args:
            soup (BeautifulSoup): The cleaned html
        Returns:
            list: A list of dictionaries with section titles and their content
        """

        sections = []

        for tag in soup.find_all(["article", "main", "section", "div"]):
            text = tag.get_text(separator=' ', strip=True)

            # ignore sections that are too short
            if len(text.split()) < 50:
                continue

            sections.append({
                "element": tag,
                "text": text
            })

        return sections
    
    def score_section(self, section: dict) -> float:
        """
        Scores the sections based on the presence of job-related keywords

        Args:
            section (dict): A section dict with their text content
        Returns:
            list: A list of sections with their scores
        """
        text = section["text"].lower()
        words = text.split()

        score = 0.0

        # length score
        score += min(len(words)*self.score_len_multiplier,1.0)

        # keyword score
        keyword_hits = sum(1 for keyword in self.job_keywords if keyword in text)
        score += (keyword_hits * self.job_keywords_multiplier)  # each keyword adds 0.5 to the score


        if section['element'].find_all("li"):
            score += self.list_item_bonus  # bonus for having list items

        return score
    # TODO: define the fallback strat to be a class of str options
    def pick_best_section(self, sections:list, fallback_strat:str|None = None) -> tuple:
        """
        Picks the best section for the URL based on the scores of each section 

        Args:
            sections (list): A list of dictionaries with section titles and their content
            fallback_strat (str): Fallback strategy to follow

        Returns:
            dict|None: The best section dictionary or None if no sections found
        """

        if not sections:
            return (0,None)
        
        scored  = [
            (self.score_section(section), section) for section in sections
        ]

        scored.sort(key=lambda x: x[0], reverse=True)
        print("the number of sections scored are ", len(scored))
        # print(f"the scored sections are {scored}")

        if fallback_strat == None:
            return scored[0]
        elif fallback_strat == 'Merge_Sections':
            combined_section = ""
            for i in range(self.fallback1_para):
                combined_section = combined_section + scored[i][1]
                return (self.score_section(combined_section), combined_section)
        elif fallback_strat == 'Keyword_Window':
            pass

        return scored[0]

    def split_into_paragraphs(self, element) -> list[str]:
        """
        This function splits the give text into paragraphs
        
        Args:
            element:  elements of the HTML page

        Returns:
            List(str): This is the list of paragraphs
        """
        paragraphs = []

        for child in element.find_all(["p", "li", "div"], recursive=True):
            text = child.get_text(strip=True)
            if len(text.split()) >= 5:  # ignore tiny noise
                paragraphs.append(text)

        return paragraphs
    
    def trim_by_stop_phrases(self,paragraphs: list[str]) -> list[str]:
        """
        This function trims the paragraphs based on the stop phrases
        
        Args:
            paragraphs(List(str)):  List of the paragraphs

        Returns:
            List(str): This is the list of trimmed paragraphs
        """

        trimmed = []
        c = 0

        for para in paragraphs:
                para_lower = para.lower()

                for stop in self.stop_phrases:
                    idx = para_lower.find(stop)
                    if idx != -1:
                        # Keep text BEFORE the stop phrase
                        trimmed_text = para[:idx].strip()
                        if trimmed_text:
                            trimmed.append(trimmed_text)
                        return trimmed  # stop completely

                trimmed.append(para)            
        c+=1
        print(f'the number of paras appended in stop phrases is : {c}')
        return trimmed

    def trim_by_density(self,paragraphs: list[str], window: int = 3) -> list[str]:
        """
        This function trims the paragraphs based on their deist
        
        Args:
            paragraphs(List(str)):  List of the paragraphs

        Returns:
            List(str): This is the list of trimmed paragraphs        """
        c = 0
        if len(paragraphs) < window + 1:
            return paragraphs

        trimmed = []
        recent_lengths = []

        for para in paragraphs:
            word_count = len(para.split())
            recent_lengths.append(word_count)

            if len(recent_lengths) > window:
                recent_lengths.pop(0)
                avg = sum(recent_lengths) / window

                # Detect sudden density collapse
                if word_count < 0.4 * avg:
                    continue

            trimmed.append(para)
            c+=1
        print(f'the number of paras appended in density is : {c}')

        return trimmed

    def trim_job_description(self,element) -> str:
        """
        This function trims the job description
        
        Args:
            element:  elements of the HTML page

        Returns:
            str: The trimmed job description
        """

        paragraphs = self.split_into_paragraphs(element)
        print(f'the length of paragraph after splitting is {len(paragraphs)}')

        paragraphs = self.trim_by_stop_phrases(paragraphs)
        print(f'the length of paragraph after trimming by stop words is {len(paragraphs)}')
        paragraphs = self.trim_by_density(paragraphs)
        print(f'the length of paragraph after splitting by density is {len(paragraphs)}')

        return "\n\n".join(paragraphs)


    def run_extraction(self,url:str) -> dict:
        """
        This function runs the jd extraction pipeline 

        Args:
            url(str): URL of the JD 

        Return:
            extracted_jd(dict): dict containing the extracted JD and confidence
        """

        html = self.fetch_rendered_html(url)
        print(f'the len of the HTML is {len(html)}')
        soup = self.clean_html(html)
        sections = self.extract_sections(soup)
        print(f'the number of sections are: {len(sections)}')
        best_score, best_content = self.pick_best_section(sections)
        print(f'the best score is {best_score}')

        # fallback if the score is too low
        if best_score < self.score_threshold:
            # checking if best content is not None
            if best_content:
                print(f"going into fallback - Merge Sections")
                # fallback best scores and content
                best_score, best_content = self.pick_best_section(sections,'Merge_Sections')
            # TODO: Add error handling if there is no content

        job_text = self.trim_job_description(best_content["element"])
        print(len(job_text))
        
        return {
            "job_description": job_text if job_text else "",
            "confidence": 0.0 if not best_score else min(1.0, (best_score / 3)),
            "source_url": url
        }


if __name__ == "__main__":
    url = "https://save-my-exams.careers.hibob.com/jobs/533866e8-6a9a-4687-9ae4-110c75301e38"
    # url = "https://www.linkedin.com/jobs/view/4343656695/?alternateChannel=search&eBP=CwEAAAGbRhf-831qvZWaFFeXziqsQwm4-bUgRovYTV30Zfu6VsgNjzzv1rc62x_3dDi_7-n47mZ7YYwpnt3HH4v8MCUqwf8uR1bIn8ixbAkR2pKxcsSmOQgHaD9LoHp6WLt2Jz9S2syAgv8GPMbL6JHqamCAHiRjRpiRUNaN-GZL8vnTbV1VU_yFnoiS9UROVlqNec0UFZOSOhdDwP6VQR4Z06HX_8_D5HHlZepWQusr68D6OgXlL2UeanhvCMot6sLTwLnG8kEPUlIA7kpd6SeC8ncUMpgajC7-H3MW-Bna6MGhZBi8R6g-Zw4LCmM3BM3R9BEIUMgOVb_BJJJHjCIiF9bjSfKnA95KtMk0AAu7s4D9aLUhXml2JismjBcAMyRWWuyQjqeVwrGv0Avvn6GrRwxsgeF-lvl-UXB6drgWLFHbO5RMxDhmzIptldTAThAEp85UwLvDaikS76xnyzrMQkuGMEJ7QEVogmWTACai&refId=hwqwjfaI0NF7XnV7JfwQ4A%3D%3D&trackingId=ffTPuqA5O0QZWRMzxtH2Dw%3D%3D&trk=d_flagship3_job_collections_discovery_landing"
    crawler = extract_jd()
    jd = crawler.run_extraction(url)
    print(jd)


