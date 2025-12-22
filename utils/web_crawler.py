
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

        self.score_len_multiplier = 1/200.0

        self.job_keywords_multiplier = 0.5

        self.list_item_bonus = 0.5

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
        score += keyword_hits * self.job_keywords_multiplier  # each keyword adds 0.5 to the score


        if section['element'].find_all("li"):
            score += self.list_item_bonus  # bonus for having list items

        return score

    def pick_best_section(self, sections:list) -> dict|None:
        """
        Picks the best section for the URL based on the scores of each section 

        Args:
            sections (list): A list of dictionaries with section titles and their content

        Returns:
            dict|None: The best section dictionary or None if no sections found
        """

        if not sections:
            return None
        
        scored  = [
            (self.score_section(section), section) for section in sections
        ]

        scored.sort(key=lambda x: x[0], reverse=True)
        print("the number of sections scored are ", len(scored))
        return scored[0][1]

    def run_extraction(self,url:str) -> dict:
        html = self.fetch_rendered_html(url)
        print(f'the len of the HTML is {len(html)}')
        soup = self.clean_html(html)
        sections = self.extract_sections(soup)
        best = self.pick_best_section(sections)

        return {
            "job_description": best["text"] if best else "",
            "confidence": 0.0 if not best else min(1.0, self.score_section(best) / 3),
            "source_url": url
        }


if __name__ == "__main__":
    url = "https://save-my-exams.careers.hibob.com/jobs/533866e8-6a9a-4687-9ae4-110c75301e38"
    crawler = extract_jd()
    jd = crawler.run_extraction(url)
    print(jd)


