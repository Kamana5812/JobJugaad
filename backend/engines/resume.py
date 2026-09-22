"""PDF text extraction only; no model, automatic skill inference, or score from prose."""
import io
import multiprocessing
from fastapi import HTTPException
import pdfplumber

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 20
MAX_CHARACTERS = 200_000

def _extract(content, channel):
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if len(pdf.pages) > MAX_PAGES:
                channel.send((False, "Please upload a PDF with at most 20 pages."))
                return
            parts, length = [], 0
            for page in pdf.pages:
                part = page.extract_text() or ""
                length += len(part)
                if length > MAX_CHARACTERS:
                    channel.send((False, "The PDF contains too much text; please use a shorter resume."))
                    return
                parts.append(part)
        result = "\n\n".join(parts).strip().replace("\x00", "")
        channel.send((bool(result), result or "No readable text found. Upload a text-based PDF; scanned images need OCR elsewhere."))
    except Exception:
        channel.send((False, "This PDF could not be read. Check that it is valid and not password-protected."))
    finally:
        channel.close()

def extract_resume(content: bytes):
    if not content.startswith(b"%PDF-"):
        raise HTTPException(422, "Please upload a valid PDF file.")
    # A separate process bounds parser time and releases its memory on completion.
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    worker = context.Process(target=_extract, args=(content, child), daemon=True)
    worker.start()
    child.close()
    try:
        if not parent.poll(20):
            raise HTTPException(422, "This PDF took too long to read; please upload a simpler file.")
        try:
            success, result = parent.recv()
        except EOFError:
            raise HTTPException(422, "This PDF could not be read. Please try a simpler file.") from None
        if not success:
            raise HTTPException(422, result)
        return result
    finally:
        parent.close()
        worker.join(timeout=1)
        if worker.is_alive():
            worker.terminate()
            worker.join()
