"""
Document reader tool.
Extracts clean text from uploaded PDF and TXT files.
Uses PyMuPDF (fitz) for PDF extraction.
Called in main.py before the graph runs — not an agent tool.
"""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text from uploaded file bytes.
    Supports PDF and TXT formats.

    Args:
        file_bytes: Raw bytes of the uploaded file
        filename: Original filename — used to detect format

    Returns:
        Extracted text string, or error message if extraction fails
    """
    filename_lower = filename.lower()

    if filename_lower.endswith(".txt"):
        return _extract_txt(file_bytes)
    elif filename_lower.endswith(".pdf"):
        return _extract_pdf(file_bytes)
    else:
        return f"Unsupported file format: {filename}. Please upload a PDF or TXT file."


def _extract_txt(file_bytes: bytes) -> str:
    """Decodes TXT file bytes to string."""
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("latin-1").strip()
        except Exception as e:
            return f"Could not read text file: {str(e)}"


def _extract_pdf(file_bytes: bytes) -> str:
    """Extracts text from PDF bytes using PyMuPDF (fitz)."""
    try:
        import fitz

        text_parts = []
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page in doc:
            text = page.get_text().strip()
            if text:
                text_parts.append(text)

        doc.close()

        if not text_parts:
            return "Could not extract text from this PDF. It may be scanned or image-based."

        return "\n\n".join(text_parts)

    except ImportError:
        return "PDF support requires PyMuPDF. Run: pip install pymupdf"
    except Exception as e:
        return f"Could not read PDF: {str(e)}"
