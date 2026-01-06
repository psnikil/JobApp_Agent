'''
Docstring for utils.latex_helper
This file contains the helper functions to post process the latex content post LLM generation.

'''
import re


# ---------- Sanitizer: escape LaTeX special chars safely ----------
class Latex_helper:

    def __init__(self):
        
        self._LATEX_SPECIALS = {
            '%': r'\%',
            '&': r'\&',
            '_': r'\_',
            '#': r'\#',
            '$': r'\$',
        }

        self._FORBIDDEN_PATTERNS = [
            r'\\begin\{document\}',
            r'\\end\{document\}',
            r'\\usepackage',
        ]


    def normalize_whitespace(self,latex: str) -> str:
        # Remove tabs
        latex = latex.replace('\t', ' ')
        
        # Collapse multiple spaces
        latex = re.sub(r' {2,}', ' ', latex)

        # Remove newlines directly inside braces: { foo\nbar } → { foo bar }
        latex = re.sub(r'\{([^{}]*?)\n([^{}]*?)\}', r'{\1 \2}', latex)

        # Remove newline after LaTeX commands: \item\n Text → \item Text
        latex = re.sub(r'(\\[a-zA-Z]+\*?)\s*\n\s*', r'\1 ', latex)

        return latex


    def remove_literal_python_escapes(self, latex: str):
        """
        Remove occurrences of literal backslash-n, backslash-t, etc.
        Only single-letter escape sequences typical from Python repr are targeted.
        """
        # Note: we replace them with a single space to avoid concatenating words
        return re.sub(r'\\[n]', ' ', latex)

    def escape_text_specials(self,latex: str) -> str:
        result = []
        i = 0
        while i < len(latex):
            ch = latex[i]

            # Already escaped
            if ch == '\\':
                result.append(ch)
                if i + 1 < len(latex):
                    result.append(latex[i + 1])
                    i += 2
                else:
                    i += 1
                continue

            # Escape special chars
            if ch in self._LATEX_SPECIALS:
                result.append(self._LATEX_SPECIALS[ch])
            else:
                result.append(ch)

            i += 1

        return ''.join(result) 
    
    def braces_balanced(self, latex: str) -> bool:
        stack = 0
        for ch in latex:
            if ch == '{':
                stack += 1
            elif ch == '}':
                stack -= 1
                if stack < 0:
                    return False
        return stack == 0
    
    def has_forbidden_patterns(self,latex: str) -> bool:
        return any(re.search(p, latex) for p in self._FORBIDDEN_PATTERNS)
    
    def latex_static_sanitize(self, latex: str) -> str:
        latex = self.normalize_whitespace(latex)
        latex = self.remove_literal_python_escapes(latex)
        latex = self.escape_text_specials(latex)

        if not self.braces_balanced(latex):
            print("Unbalanced braces in LaTeX")
            # raise ValueError("Unbalanced braces in LaTeX")

        if self.has_forbidden_patterns(latex):
            print("Forbidden LaTeX structure detected")
            # raise ValueError("Forbidden LaTeX structure detected")

        return latex



import re
import uuid

# ---------------------- Config ----------------------
PROTECT_ENVIRONMENTS = ("verbatim", "lstlisting", "minted")
PROTECT_COMMANDS_SINGLE_BRACE = ("url",)                 # \url{...}
PROTECT_COMMANDS_DOUBLE_BRACE = ("href",)               # \href{...}{...}
# ----------------------------------------------------

def _mk_token() -> str:
    return f"__LATEX_PROTECT_{uuid.uuid4().hex}__"

def _extract_protected_regions(text: str):
    """
    Finds and replaces protected regions (verbatim-like envs and url/href contents)
    with placeholders. Returns (new_text, mapping) where mapping[token] = original_content.
    """
    mapping = {}

    # 1) protect environments: \begin{env} ... \end{env}
    for env in PROTECT_ENVIRONMENTS:
        # non-greedy capture up to matching \end{env}
        pattern = re.compile(rf'\\begin\{{{re.escape(env)}\}}(.*?)\\end\{{{re.escape(env)}\}}', re.DOTALL)
        while True:
            m = pattern.search(text)
            if not m:
                break
            token = _mk_token()
            content = m.group(0)
            mapping[token] = content
            text = text[:m.start()] + token + text[m.end():]

    # 2) protect \url{...} (single argument)
    for cmd in PROTECT_COMMANDS_SINGLE_BRACE:
        pattern = re.compile(rf'\\{re.escape(cmd)}\{{(.*?)\}}', re.DOTALL)
        while True:
            m = pattern.search(text)
            if not m:
                break
            token = _mk_token()
            mapping[token] = m.group(0)   # preserve full \url{...}
            text = text[:m.start()] + token + text[m.end():]

    # 3) protect \href{...}{...} (two args) - keep entire \href{...}{...}
    for cmd in PROTECT_COMMANDS_DOUBLE_BRACE:
        pattern = re.compile(rf'\\{re.escape(cmd)}\{{(.*?)\}}\{{(.*?)\}}', re.DOTALL)
        while True:
            m = pattern.search(text)
            if not m:
                break
            token = _mk_token()
            mapping[token] = m.group(0)
            text = text[:m.start()] + token + text[m.end():]

    return text, mapping

def _restore_protected_regions(text: str, mapping: dict):
    # Reverse replace tokens with original content
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text

def _preserve_backslash_backslash(text: str):
    """Replace sequences of '\\\\' (LaTeX linebreak macros) with a token to avoid collapsing them."""
    token = _mk_token()
    # replace escaped linebreaks like '\\\\' possibly followed by whitespace/newline
    new_text = re.sub(r'(\\\\)(\s*\n\s*|\s+)?', token, text)
    return new_text, token

def _restore_backslash_backslash(text: str, token: str):
    return text.replace(token, '\\\\')  # restore as literal '\\\\'

def _remove_literal_python_escapes(text: str):
    """
    Remove occurrences of literal backslash-n, backslash-t, etc.
    Only single-letter escape sequences typical from Python repr are targeted.
    """
    # Note: we replace them with a single space to avoid concatenating words
    return re.sub(r'\\[nrvf]', ' ', text)

def _collapse_whitespace(text: str):
    # collapse any whitespace sequence (space, newline, tab) to a single space
    return re.sub(r'\s+', ' ', text).strip()

def _escape_latex_specials(text: str):
    """
    Escape LaTeX special characters in text areas.
    We use negative lookbehind to avoid touching already-escaped sequences like '\%'.
    We intentionally avoid escaping braces { } because they are structural.
    """
    # Order matters (escape % first)
    text = re.sub(r'(?<!\\)%', r'\%', text)
    text = re.sub(r'(?<!\\)&', r'\&', text)
    text = re.sub(r'(?<!\\)_', r'\_', text)
    text = re.sub(r'(?<!\\)\$', r'\$', text)
    text = re.sub(r'(?<!\\)#', r'\#', text)
    # Replace literal ~ and ^ with safe textual macros (if not already escaped)
    text = re.sub(r'(?<!\\)~', r'\textasciitilde{}', text)
    text = re.sub(r'(?<!\\)\^', r'\textasciicircum{}', text)
    return text

def _check_brace_balance(text: str):
    stack = 0
    for ch in text:
        if ch == '{':
            stack += 1
        elif ch == '}':
            stack -= 1
            if stack < 0:
                return False
    return stack == 0

# ---------------------- Public API ----------------------
def sanitize_latex_block(latex_block: str) -> str:
    """
    Sanitize a block of LaTeX generated by a model so that:
    - python escape sequences like '\\n', '\\t' are removed
    - accidental newlines / tabs / excessive whitespace are normalized
    - LaTeX special characters are escaped in textual regions
    - verbatim-like regions and urls/hrefs are preserved untouched
    - '\\\\' (linebreak macros) are preserved
    Returns sanitized LaTeX string. Raises ValueError if structural checks fail.
    """
    if latex_block is None:
        return latex_block

    # normalize line endings
    s = latex_block.replace('\r\n', '\n').replace('\r', '\n')

    # remove literal python-style escapes like '\n', '\t' (backslash + single letter)
    s = _remove_literal_python_escapes(s)

    # Extract and protect verbatim-like and url/href regions
    s, protected_map = _extract_protected_regions(s)

    # Protect '\\' linebreak macros (so whitespace collapse won't remove them)
    s, br_token = _preserve_backslash_backslash(s)

    # Collapse whitespace to single spaces (this removes unintended newlines)
    s = _collapse_whitespace(s)

    # Escape LaTeX specials globally (safe now because protected regions removed)
    s = _escape_latex_specials(s)

    # Restore '\\\\' back
    s = _restore_backslash_backslash(s, br_token)

    # Restore protected regions
    s = _restore_protected_regions(s, protected_map)

    # Final structural check: brace balance
    if not _check_brace_balance(s):
        # If braces are unbalanced, it's safer to raise and let calling code re-run / log / fallback
        raise ValueError("Sanitizer detected unbalanced braces in LaTeX after sanitization.")

    return s

# ---------------------- Example usage ----------------------
if __name__ == "__main__":
    sample = r"""
\begin{twocolentry}{\n 2023 - Present\n}\textbf{Software Engineer}, Multimatic Electronic System -- Cambridge,GB\end{twocolentry}\\

\vspace{0.10 cm}
\begin{onecolentry}
\begin{highlights}
\begin{twocolentry}{\n\n}
\textbf{Wingman: Local LLM RAG agent}\end{twocolentry}
\vspace{0.10 cm}
\begin{onecolentry}
\begin{highlights}
\item Built a full-stack, locally running ChatGPT-like app that lets you chat with open-source LLMs (via Ollama) on your own machine using Next.js, TailwindCSS, Python, FastAPI, TypeScript, Ollama, and RAG. 
\item Designed for privacy, extensibility, and developer friendliness, supporting future RAG agents and DB support. \n
\end{highlights}
\end{onecolentry}
\vspace{0.2 cm}
"""
    print("===== BEFORE =====")
    print(sample)
    print("\n===== AFTER SANITIZE =====")
    print(sanitize_latex_block(sample))

