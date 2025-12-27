"""
This is a helper module to parse the latex resume to return content, replace latex code, clean text, 
"""

import re
import os
import subprocess
import shutil

class ResumeParser:
    def __init__(self):
        self.raw_content = ""
        self.sections_metadata = {} # Stores {section_name: {'start': int, 'end': int, 'raw': str}}

    def _extract_sections_metadata(self, content: str) -> dict:
        """
        Scans the provided content for sections and returns metadata.
        Returns: {section_name: {'start': int, 'end': int, 'raw': str}}
        """
        # Finds sections, ignoring comments (though filtering comments in regex is handled by logic)
        # Re-use _find_sections internal logic but adapted for arbitrary content string?
        # self._find_sections used self.raw_content. Let's make a static helper or just use local 'content'.
        
        section_iter = re.finditer(r'\\section\{([^}]+)\}', content)
        sections_found = []
        for match in section_iter:
            # Check if commented out
            start_pos = match.start()
            line_start = content.rfind('\n', 0, start_pos) + 1
            line_prefix = content[line_start:start_pos]
            
            if '%' in line_prefix:
                if not re.search(r'\\%', line_prefix): 
                     continue

            sections_found.append({
                'title': match.group(1),
                'start_header': match.start(),
                'end_header': match.end()
            })
            
        metadata = {}
        
        # Header
        if sections_found:
            header_end = sections_found[0]['start_header']
            header_raw = content[:header_end]
            doc_start = re.search(r'\\begin\{document\}', header_raw)
            if doc_start:
                header_content_start = doc_start.end()
                metadata['Header'] = {
                    'start': header_content_start,
                    'end': header_end,
                    'raw': header_raw[header_content_start:]
                }

        # Sections
        for i, sec in enumerate(sections_found):
            title = sec['title']
            start_content = sec['end_header']
            
            if i < len(sections_found) - 1:
                end_content = sections_found[i+1]['start_header']
            else:
                end_content = len(content)
                end_doc = re.search(r'\\end\{document\}', content[start_content:])
                if end_doc:
                    end_content = start_content + end_doc.start()
            
            raw_section_content = content[start_content:end_content]
            
            metadata[title] = {
                'start': start_content,
                'end': end_content,
                'raw': raw_section_content
            }
        return metadata

    def parse(self, file_path: str) -> dict:
        """
        Parses the LaTeX resume file and returns a dictionary where keys are 
        section names and values are the cleaned text content.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            self.raw_content = f.read()

        # Extract metadata from the loaded content
        self.sections_metadata = self._extract_sections_metadata(self.raw_content)
        
        cleaned_sections = {}
        for title, meta in self.sections_metadata.items():
            cleaned_sections[title] = self._clean_text(meta['raw'])

        return cleaned_sections
    
    def get_section_latex(self, section_name: str, file_path: str = None) -> str:
        """
        Returns the raw LaTeX code for a specific section.
        If file_path is provided, reads from that file instead of internal buffer.
        """
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # temporary extract
            temp_meta = self._extract_sections_metadata(content)
            if section_name not in temp_meta:
                 raise KeyError(f"Section '{section_name}' not found in {file_path}")
            return temp_meta[section_name]['raw']
        else:
            # Use internal buffer
            if not self.sections_metadata:
                 raise RuntimeError("No content loaded. Call parse() first or provide file_path.")
            if section_name not in self.sections_metadata:
                 raise KeyError(f"Section '{section_name}' not found in loaded content.")
            return self.sections_metadata[section_name]['raw']

    def update_section(self, section_name: str, new_content: str, is_latex: bool = False):
        """
        Updates the content of a specific section in the internal buffer.
        
        Args:
            section_name: The title of the section to update.
            new_content: The new text or LaTeX content.
            is_latex: If True, treats new_content as raw LaTeX (does not escape).
                      If False, escapes special characters and attempts to wrap in
                      default environments (like onecolentry) if appropriate.
        """
        if section_name not in self.sections_metadata:
            raise KeyError(f"Section '{section_name}' not found.")
            
        meta = self.sections_metadata[section_name]
        original_raw = meta['raw']
        
        if is_latex:
            # If providing raw LaTeX, we assume the user provides the *complete* 
            # section body, including necessary environments.
            # We treat it as a direct replacement.
            new_section_raw = f"\n{new_content}\n"
        else:
            # Escape new content for LaTeX
            escaped_new_content = self._escape_text(new_content)
            
            # Heuristic: Find if wrapped in onecolentry or similar
            if r'\begin{onecolentry}' in original_raw:
                 # Reconstruct simple wrapper
                new_section_raw = f"\n\n\\begin{{onecolentry}}\n{{\n{escaped_new_content}\n}}\n\\end{{onecolentry}}\n\n"
            else:
                new_section_raw = f"\n{escaped_new_content}\n"

        # Update self.raw_content
        # Same strategy: lazy update via string concatenation
        prefix = self.raw_content[:meta['start']]
        suffix = self.raw_content[meta['end']:]
        
        self.raw_content = prefix + new_section_raw + suffix
        
        # Re-parse to update metadata indices
        self._refresh_metadata()

    def _refresh_metadata(self):
        self.sections_metadata = self._extract_sections_metadata(self.raw_content)


    def save(self, file_path: str):
        """
        Saves the current (modified) raw content to a file.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.raw_content)

    def generate_pdf(self, output_dir: str = "."):
        """
        Compiles the current content to PDF.
        Requires pdflatex installed.
        """
        # Save to a temp file or the target file name?
        # The user said "The updated latex file should be compiled".
        # We assume the user saved it already? Or we save to a temporary name.
        # Let's save to a temporary .tex file in the output dir to compile.
        
        if not shutil.which('pdflatex'):
            raise EnvironmentError("pdflatex not found. Please install TeX Live or similar.")
            
        # We'll save as 'resume_updated.tex' temporarily
        tex_file = os.path.join(output_dir, "resume_updated.tex")
        self.save(tex_file)
        
        # Run pdflatex
        # pdflatex usually outputs to the same directory
        try:
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', 'resume_updated.tex'],
                cwd=output_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            # Check log?
            raise RuntimeError(f"PDF generation failed: {e.stdout.decode() if e.stdout else ''} {e.stderr.decode() if e.stderr else ''}")
        
    def _escape_text(self, text: str) -> str:
        """
        Escapes special LaTeX characters.
        """
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }
        # Use regex to replace to avoid double replacing logic if not careful
        # Iterating char by char or using regex sub with callback
        return "".join(replacements.get(c, c) for c in text)


    def _clean_text(self, text: str) -> str:
        """
        Removes LaTeX formatting to produce clean text.
        """
        # Remove comments
        text = re.sub(r'(?<!\\)%.*', '', text)
        
        # 0. Basic whitespace cleanup (handled at end too)
        
        # 1. Handle common environments that wrap text we want to keep
        # Remove \begin{...} and \end{...}
        text = re.sub(r'\\begin\{[^}]+\}(\{[^}]+\})*', ' ', text) 
        text = re.sub(r'\\end\{[^}]+\}', ' ', text)

        # 2. Handle specific commands
        text = re.sub(r'\\href\{[^}]+\}\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\\hrefWithoutArrow\{[^}]+\}\{([^}]+)\}', r'\1', text)
        
        # 3. Lists
        text = re.sub(r'\\item', '\n• ', text)

        # 4. Unwrap simple commands: \textbf{...}, \textit{...}
        clean_wrappers = [r'\\textbf', r'\\textit', r'\\small', r'\\large', r'\\mbox', r'\\emph']
        for cmd in clean_wrappers:
            # Loop to handle nested/multiple occurrences
            while re.search(cmd + r'\{', text):
                text = re.sub(cmd + r'\{([^}]*)\}', r'\1', text)

        # 5. Remove layout/spacing commands entirely
        layout_cmds = [
            r'\\vspace\{[^}]+\}', 
            r'\\hspace\{[^}]+\}', 
            r'\\setlength\{[^}]+\}\{[^}]+\}',
            r'\\fontsize\{[^}]+\}\{[^}]+\}\\selectfont',
            r'\\kern [0-9.]+\s*pt',
            r'\\kern [0-9.]+\s*cm',
            r'\\raggedright',
            r'\\raggedleft',
            r'\\centering',
            r'\\linespread\{[^}]+\}',
            r'\\par',
            r'\\hfill',
            r'\\break',
            r'\\newline',
            r'\\selectfont',
            r'\\normalsize',
            r'\\unskip',
            r'\\cleaders.*',
            r'\\ignorespaces',
            r'\\columnbreak',
            r'\\definecolor\{[^}]+\}\{[^}]+\}'
        ]
        for pattern in layout_cmds:
            text = re.sub(pattern, ' ', text)
            
        # 5b. Remove \input or \newcommand formatting definitions
        # Handle multiline \newcommand
        text = re.sub(r'\\newcommand\{[^}]+\}(\[[^\]]+\])?\{[^\}]*\}', '', text, flags=re.DOTALL) 
        
        # Handle \newsavebox\Name (no braces) and \newsavebox{\Name}
        text = re.sub(r'\\newsavebox(\{|\\)[^}a-zA-Z]*[a-zA-Z]+(\}|)?', '', text)
        
        # Handle \sbox\Name{...} or \sbox{\Name}{...}
        # Easier to just remove lines starting with \sbox or \newsavebox if possible? 
        # But we are in a text blob.
        # \sbox followed by token or brace, then another token or brace.
        # Let's try to target specific pattern seen: \sbox\ANDbox{$|$}
        text = re.sub(r'\\sbox\\[a-zA-Z]+(?=\{|\$)[^}]*\}?', '', text)
        
        # Remove \AND which is a custom command used as separator
        text = text.replace(r'\AND', '|')

        # 6. Remove remaining braces {} and $ $ for math logic if they are just wrapping textry
        # Example: { content } -> content
        # We need to be careful not to remove needed braces, but usually at this stage (plain text), braces are artifacts.
        # We'll remove braces that enclose the whole block or start/end.
        # Simple approach: Remove { and } if they are not part of a word? 
        # Actually, for resuming parsing, just removing all { and } is often safe if we've handled commands.
        text = text.replace('{', '').replace('}', '')

        # 7. Convert \\ to newline
        text = text.replace(r'\\', '\n')

        # 8. Special characters
        text = text.replace(r'\&', '&')
        text = text.replace(r'\$', '$')
        text = text.replace(r'\%', '%')
        text = text.replace(r'\_', '_')
        
        # 9. Cleanup multiple spaces/newlines
        lines = [line.strip() for line in text.split('\n')]
        # Filter empty lines
        text = '\n'.join([l for l in lines if l])
        
        return text
