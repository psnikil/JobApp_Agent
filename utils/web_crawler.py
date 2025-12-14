
import json
import requests
import re
from bs4 import BeautifulSoup

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