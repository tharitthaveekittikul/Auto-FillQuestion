import re

def clean_text(text):
    # Replace multiple newlines with a single newline
    text = re.sub(r'\n+', '\n', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Ensure proper spacing after periods
    text = re.sub(r'\.\s*', '. ', text)
    return text.strip()