"""Bounded PDF format checks; not malware scanning or document certification."""
import io
import multiprocessing
from engines.pdf_budget import PARSER_SLOTS

from fastapi import HTTPException

MAX_BYTES = 2 * 1024 * 1024
MAX_PAGES = 20
MAX_OBJECTS = 10_000
PARSER_SECONDS = 12
BLOCKED_KEYS = {"JavaScript", "JS", "AA", "OpenAction", "EmbeddedFiles", "EF", "XFA", "RichMedia"}
BLOCKED_ACTIONS = {"JavaScript", "Launch", "SubmitForm", "ImportData", "GoToR", "GoToE", "Rendition", "Movie", "Sound"}


class DocumentFormatError(ValueError):
    """Safe, deliberately written user-facing rejection."""


def _resource_bounds():
    try:
        import resource
    except ImportError:  # Windows still enforces the parent process wall-time limit.
        return
    for resource_id, wanted in ((resource.RLIMIT_AS, 256 * 1024 * 1024), (resource.RLIMIT_CPU, 10)):
        _, hard = resource.getrlimit(resource_id)
        bound = wanted if hard == resource.RLIM_INFINITY else min(hard, wanted)
        resource.setrlimit(resource_id, (bound, bound))


def _inspect_objects(document):
    from pdfminer.pdfparser import PDFObjRef
    from pdfminer.pdftypes import PDFStream
    from pdfminer.psparser import PSLiteral

    refs, containers = set(), set()
    inspected = 0

    def name(value):
        return value.name if isinstance(value, PSLiteral) else value

    def visit(value):
        nonlocal inspected
        inspected += 1
        if inspected > MAX_OBJECTS:
            raise DocumentFormatError("This PDF is too complex; please export a simpler PDF.")
        if isinstance(value, PDFObjRef):
            if value.objid not in refs:
                refs.add(value.objid)
                visit(value.resolve())
        elif isinstance(value, PDFStream):
            visit(value.attrs)  # Do not decode image or text streams for file storage.
        elif isinstance(value, (dict, list, tuple)):
            if id(value) in containers:
                return
            containers.add(id(value))
            if isinstance(value, dict):
                keys = {name(key) for key in value}
                action = name(value.get("S"))
                if (keys & BLOCKED_KEYS or (isinstance(action, str) and action in BLOCKED_ACTIONS)
                        or name(value.get("Type")) == "EmbeddedFile"):
                    raise DocumentFormatError("PDF scripts, actions and embedded attachments are not supported. Export a plain PDF.")
                for child in value.values():
                    visit(child)
            else:
                for child in value:
                    visit(child)

    visit(document.catalog)
    objects = set()
    for xref in document.xrefs:
        for object_id in xref.get_objids():
            objects.add(object_id)
            if len(objects) > MAX_OBJECTS:
                raise DocumentFormatError("This PDF is too complex; please export a simpler PDF.")
            if object_id not in refs:
                refs.add(object_id)
                visit(document.getobj(object_id))


def _validate(content, channel):
    try:
        _resource_bounds()
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            if pdf.doc.encryption is not None:
                raise DocumentFormatError("Password-protected PDFs are not supported. Upload an unencrypted PDF.")
            page_count = len(pdf.pages)
            if not 1 <= page_count <= MAX_PAGES:
                raise DocumentFormatError("Upload a PDF containing between 1 and 20 pages.")
            _inspect_objects(pdf.doc)
        channel.send((True, page_count))
    except DocumentFormatError as error:
        channel.send((False, str(error)))
    except Exception:
        channel.send((False, "This PDF could not be read safely. Export a plain PDF and try again."))
    finally:
        channel.close()


def validate_document_pdf(content: bytes) -> int:
    if not PARSER_SLOTS.acquire(timeout=2):
        raise HTTPException(503, 'PDF processing is busy. Please try again shortly.', headers={'Retry-After': '3'})
    try:
        return _validate_bounded(content)
    finally:
        PARSER_SLOTS.release()


def _validate_bounded(content: bytes) -> int:
    """Validate format in a disposable process, accepting scanned PDFs without OCR."""
    if not content:
        raise HTTPException(422, "The PDF is empty.")
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Upload one PDF of at most 2 MiB.")
    if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-1024:]:
        raise HTTPException(422, "Upload a complete PDF file with a valid PDF header and ending.")
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    worker = context.Process(target=_validate, args=(content, child), daemon=True)
    try:
        try:
            worker.start()
        except (OSError, RuntimeError):
            raise HTTPException(503, "PDF checking is temporarily unavailable. Please try again.") from None
        child.close()
        if not parent.poll(PARSER_SECONDS):
            raise HTTPException(422, "This PDF took too long to check. Please export a simpler PDF.")
        try:
            valid, result = parent.recv()
        except EOFError:
            raise HTTPException(422, "This PDF exceeded safe processing limits. Please export a simpler PDF.") from None
        if not valid:
            raise HTTPException(422, result)
        return int(result)
    finally:
        parent.close()
        child.close()
        if worker.pid is not None:
            worker.join(timeout=0.2)
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=1)
            if worker.is_alive():
                worker.kill()
                worker.join(timeout=1)
