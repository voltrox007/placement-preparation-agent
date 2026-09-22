"""Extract text without executing document content or retaining uploaded bytes."""

from io import BytesIO
from pathlib import Path

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 60_000
MAX_PAGES = 30


def extract_document(name: str, content: bytes) -> str:
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Upload must contain between 1 byte and 5 MB")
    suffix = Path(name).suffix.lower()
    if suffix == ".txt":
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Text files must use UTF-8") from exc
    elif suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("The uploaded file is not a PDF")
        from pypdf import PdfReader

        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted or len(reader.pages) > MAX_PAGES:
                raise ValueError("Use an unencrypted PDF with at most 30 pages")
            parts = []
            has_text = False
            total_chars = 0
            for number, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                has_text = has_text or bool(page_text.strip())
                part = f"[Page {number}]\n{page_text}"
                parts.append(part)
                total_chars += len(part)
                if total_chars > MAX_TEXT_CHARS:
                    raise ValueError("Document text exceeds 60,000 characters")
            text = "\n\n".join(parts)
            if not has_text:
                raise ValueError("No readable text found; paste the resume text instead")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("PDF could not be read; paste the resume text instead") from exc
    else:
        raise ValueError("Only PDF and UTF-8 text documents are supported")
    if not text.strip() or len(text) > MAX_TEXT_CHARS:
        raise ValueError("Provide readable text of at most 60,000 characters")
    return text.strip()
