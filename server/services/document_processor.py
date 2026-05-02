import fitz  # PyMuPDF
from docx import Document
import io

def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from uploaded file bytes based on file type.
    Supports PDF, DOCX, and TXT files.
    """
    file_extension = filename.lower().split('.')[-1]

    if file_extension == 'pdf':
        return extract_text_from_pdf(file_bytes)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_bytes)
    elif file_extension == 'txt':
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    doc = Document(io.BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from TXT by decoding bytes."""
    return file_bytes.decode('utf-8')

def chunk_text(text: str, chunk_size: int = 250, overlap: int = 50) -> list[str]:
    """
    Split text into chunks with overlap.
    - Split by words
    - Maintain overlap between chunks
    - Remove empty chunks
    - Return list of strings
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = words[start:end]
        if chunk:  # Only add non-empty chunks
            chunks.append(' '.join(chunk))
        start = end - overlap
        if start <= 0:  # Prevent infinite loop
            break

    return chunks