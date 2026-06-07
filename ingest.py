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


def _parse_pdf_lines(page):
    """Parse PDF page text into lines while preserving bold formatting."""
    chars = sorted(page.chars, key=lambda char: (round(char["top"], 1), char["x0"]))
    lines = []
    current_top = None
    current_chars = []

    for char in chars:
        top = round(char["top"], 1)
        if current_top is None or abs(top - current_top) <= 2.0:
            current_chars.append(char)
            current_top = top if current_top is None else (current_top + top) / 2
        else:
            if current_chars:
                lines.append(current_chars)
            current_chars = [char]
            current_top = top

    if current_chars:
        lines.append(current_chars)

    parsed_lines = []
    for line_chars in lines:
        line_chars.sort(key=lambda c: c["x0"])
        text = "".join(c["text"] for c in line_chars).strip()
        if not text:
            continue

        normalized_text = " ".join(text.split())
        font_names = " ".join(c.get("fontname", "") for c in line_chars).lower()
        is_bold = any(keyword in font_names for keyword in ("bold", "black", "heavy", "demi", "medium"))

        parsed_lines.append({
            "text": normalized_text,
            "is_bold": is_bold,
        })

    return parsed_lines


def _lines_to_sections(lines):
    """Group parsed PDF lines into sections based on bold headers."""
    sections = []
    current_header = None
    current_body = []

    for line in lines:
        is_header = line["is_bold"] and len(line["text"].split()) <= 20

        if is_header:
            if current_header is not None and not current_body:
                current_header = f"{current_header} {line['text']}"
                continue

            if current_header is not None or current_body:
                section_text = "\n".join(current_body).strip()
                if section_text or current_header is not None:
                    sections.append({
                        "header": current_header,
                        "text": section_text,
                    })
            current_header = line["text"]
            current_body = []
        else:
            current_body.append(line["text"])

    if current_header is not None or current_body:
        section_text = "\n".join(current_body).strip()
        sections.append({
            "header": current_header,
            "text": section_text,
        })

    return sections


def _extract_pdf_sections(filepath):
    """Extract PDF sections using bold text headers when available."""
    sections = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            lines = _parse_pdf_lines(page)
            if not lines:
                continue
            page_sections = _lines_to_sections(lines)
            sections.extend(page_sections)

    if not sections:
        full_text = _load_pdf_text(filepath)
        return [{"header": None, "text": full_text}]

    return sections


def load_documents():
    """Load all .pdf and .txt student loan articles from the docs folder."""
    documents = []
    for filename in sorted(os.listdir(DOCS_PATH)):
        filepath = os.path.join(DOCS_PATH, filename)
        if filename.lower().endswith(".pdf"):
            text = _load_pdf_text(filepath)
            sections = _extract_pdf_sections(filepath)
        else:
            continue

        if not text:
            continue

        article_name = os.path.splitext(filename)[0].replace("_", " ").title()
        document = {
            "student_loan_article": article_name,
            "filename": filename,
            "text": text,
        }
        if sections is not None:
            document["sections"] = sections

        documents.append(document)

    print(f"Loaded {len(documents)} student loan article document(s): {[d['student_loan_article'] for d in documents]}")
    return documents


def _chunk_section_text(section_header, section_text, article_name, prefix, counter):
    chunk_size = 180
    overlap = 60
    min_length = 50

    words = section_text.split()
    if not words:
        return []

    def build_text(chunk_words):
        chunk_text = " ".join(chunk_words).strip()
        if section_header:
            return f"{section_header}\n\n{chunk_text}"
        return chunk_text

    chunks = []
    if len(words) <= chunk_size:
        if len(words) >= min_length or section_header:
            chunks.append({
                "text": build_text(words),
                "student_loan_article": article_name,
                "section_header": section_header,
                "chunk_id": f"{prefix}_{counter}",
            })
        return chunks

    step = chunk_size - overlap
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        if len(chunk_words) >= min_length or section_header:
            chunks.append({
                "text": build_text(chunk_words),
                "student_loan_article": article_name,
                "section_header": section_header,
                "chunk_id": f"{prefix}_{counter}",
            })
            counter += 1
        start += step

    return chunks


def chunk_document(doc):
    """
    Split a student loan article into chunks ready for embedding.

    When a PDF document includes bolded section headers, this function
    preserves those sections and chunks each section separately. That lets
    the embedding model focus on meaningful article sections rather than
    arbitrary word windows.
    """
    article_name = doc["student_loan_article"]
    prefix = article_name.lower().replace(" ", "_")
    chunks = []
    counter = 0

    sections = doc.get("sections")
    if sections:
        for section in sections:
            section_header = section.get("header")
            section_text = section.get("text", "").strip()
            if not section_text:
                continue

            section_chunks = _chunk_section_text(
                section_header,
                section_text,
                article_name,
                prefix,
                counter,
            )
            chunks.extend(section_chunks)
            counter += len(section_chunks)
    else:
        chunk_text = doc.get("text", "").strip()
        chunks.extend(_chunk_section_text(None, chunk_text, article_name, prefix, counter))

    return chunks
