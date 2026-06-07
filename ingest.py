import os
import pdfplumber
from config import DOCS_PATH


def _load_pdf_text(filepath):
    """Extract all page text from a PDF as a single string."""
    with pdfplumber.open(filepath) as pdf:
        pages = []
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
    return "\n\n".join(pages).strip()


def _load_text_file(filepath):
    """Read a plain text file and return its contents."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_documents():
    """Load all .pdf student loan articles from the docs folder."""
    documents = []
    for filename in sorted(os.listdir(DOCS_PATH)):
        filepath = os.path.join(DOCS_PATH, filename)
        if filename.lower().endswith(".pdf"):
            text = _load_pdf_text(filepath)
        elif filename.lower().endswith(".txt"):
            text = _load_text_file(filepath)
        else:
            continue

        if not text:
            continue

        article_name = os.path.splitext(filename)[0].replace("_", " ").title()
        documents.append({
            "student_loan_article": article_name,
            "filename": filename,
            "text": text,
        })
    print(f"Loaded {len(documents)} student loan article document(s): {[d['student_loan_article'] for d in documents]}")
    return documents


def chunk_document(text, article_name):
    """
    Split a student loan article into chunks ready for embedding.

    Strategy: word-based sliding window with overlap.
      - chunk_size = 150 words: smaller chunks that may improve precision for tight policy comparisons.
      - overlap = 40 words: preserves continuity across chunk boundaries while keeping chunks compact.
      - min_length = 50 words: filters out very short fragments that add noise.

    Returns a list of dicts, each with:
      - "text"                 : the chunk text (str)
      - "student_loan_article" : the article name (str)
      - "chunk_id"             : a unique identifier, e.g. "student_loan_article_0" (str)
    """
    chunk_size = 150
    overlap = 40
    min_length = 50

    words = text.split()
    if not words:
        return []

    chunks = []
    prefix = article_name.lower().replace(" ", "_")
    counter = 0

    step = chunk_size - overlap
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words).strip()

        if len(chunk_words) >= min_length:
            chunks.append({
                "text": chunk_text,
                "student_loan_article": article_name,
                "chunk_id": f"{prefix}_{counter}",
            })
            counter += 1

        start += step

    return chunks
