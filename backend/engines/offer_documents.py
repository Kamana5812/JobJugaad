"""Private retained PDF revisions with human review and explicit offer transitions.

Format checks do not establish authenticity or constitute malware scanning. Bytes
are immutable through this API; replacement creates a new retained revision.
"""
import hashlib
import json
import unicodedata
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update, func, text

from engines import offers
from engines.document_pdf import MAX_BYTES, MAX_PAGES, validate_document_pdf
from models import Offer, OfferDocument, OfferDocumentEvent, OfferEvent
from schemas import (OfferDocumentResponse, OfferDocumentLimits, OfferDocumentList,
    OfferDocumentMutation, OfferDocumentEventResponse, OfferDocumentEventList)

MAX_FILES = 10
MAX_OFFER_BYTES = 10 * 1024 * 1024
METHOD = ("Private PDF files retained in this college's database. Format checks do not verify authenticity; "
    "an administrator records each human review and then separately records the offer stages. "
    "Replacement keeps the previous bytes and history. No email or SMS is sent.")


def scoped_offer(session, user, offer_id, *, lock=False):
    query = offers.offer_rows(session, user).where(Offer.id == offer_id)
    if lock:
        # The router may have authorized this row before bounded PDF processing.
        # Refresh after taking the lock so a concurrent stage change is not stale.
        query = query.with_for_update(of=Offer).execution_options(populate_existing=True)
    row = session.scalar(query)
    if row is None:
        raise HTTPException(404, "Offer not found.")
    return row


def was_issued(session, college, offer):
    if offer.offer_letter_status == "issued":
        return True
    return session.scalar(select(OfferEvent.id).where(OfferEvent.college_id == college,
        OfferEvent.offer_id == offer.id, OfferEvent.action == "offer_letter_status:issued").limit(1)) is not None


def file_scope(session, user, offer):
    scope = [OfferDocument.college_id == user.college_id, OfferDocument.offer_id == offer.id]
    # Draft terms remain private even from the recipient until explicit issuance.
    # A later withdrawal must not erase the student's access to issued history.
    if user.role == "student" and not was_issued(session, user.college_id, offer):
        scope.append(OfferDocument.kind == "supporting_document")
    return scope


def document_for(session, user, offer, document_id):
    row = session.scalar(select(OfferDocument).where(*file_scope(session, user, offer),
        OfferDocument.id == document_id))
    if row is None:
        raise HTTPException(404, "Document not found.")
    return row


def metadata(row):
    return OfferDocumentResponse.model_validate(row, from_attributes=True)


def stored_usage(session, college, offer_id):
    return session.execute(select(func.count(), func.coalesce(func.sum(OfferDocument.size_bytes), 0))
        .select_from(OfferDocument).where(OfferDocument.college_id == college,
            OfferDocument.offer_id == offer_id)).one()


def listing(session, user, offer_id, offset=0, limit=20):
    offer = scoped_offer(session, user, offer_id)
    scope = file_scope(session, user, offer)
    total, size = session.execute(select(func.count(), func.coalesce(func.sum(OfferDocument.size_bytes), 0))
        .select_from(OfferDocument).where(*scope)).one()
    rows = session.scalars(select(OfferDocument).where(*scope)
        .order_by(OfferDocument.id.desc()).offset(offset).limit(limit)).all()
    explanation = METHOD + " Limits count retained revisions, including replaced files."
    if user.role == "student" and not was_issued(session, user.college_id, offer):
        explanation += " Draft offer-letter metadata and bytes are private until issuance; the usage shown includes your accessible files only."
    return OfferDocumentList(items=[metadata(row) for row in rows], total=total,
        offset=offset, limit=limit, offer_version=offer.version,
        limits=OfferDocumentLimits(max_bytes=MAX_BYTES, max_pages=MAX_PAGES,
            max_files=MAX_FILES, max_offer_bytes=MAX_OFFER_BYTES,
            stored_files=total, stored_bytes=size), explanation=explanation)


def normalized_filename(filename):
    # Browser paths are untrusted display data, never storage paths or headers.
    basename = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    basename = "".join(char for char in basename if not unicodedata.category(char).startswith("C")).strip()
    if not basename.lower().endswith(".pdf"):
        raise HTTPException(422, "Choose a file with a .pdf filename.")
    if len(basename) > 255:
        raise HTTPException(422, "Use a PDF filename of at most 255 characters.")
    return basename


def request_hash(payload, kind, filename, digest):
    # Version is deliberately excluded: a lost-response retry can arrive after
    # this upload or a later human action has advanced the offer's version.
    data = dict(kind=kind, filename=filename, sha256=digest, label=payload.label,
        reason=payload.reason, replaces_document_id=payload.replaces_document_id)
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def event(session, user, document, action, reason):
    session.add(OfferDocumentEvent(college_id=user.college_id, offer_id=document.offer_id,
        document_id=document.id, actor_user_id=user.id, action=action, reason=reason))


def mutation_response(session, user, offer, document):
    return OfferDocumentMutation(offer=offers.responses(session, user.college_id, [offer], user=user)[0],
        document=metadata(document))


def prior_upload(session, user, offer, payload, content_hash):
    previous = session.scalar(select(OfferDocument).where(OfferDocument.college_id == user.college_id,
        OfferDocument.idempotency_key == str(payload.idempotency_key)))
    if previous is not None and (previous.offer_id != offer.id or previous.uploaded_by != user.id or
            previous.request_hash != content_hash):
        raise HTTPException(409, "This upload key was already used for a different request. Refresh and start a new upload.")
    return previous


def upload(session, user, offer_id, payload, content, filename, kind):
    if ((user.role == "admin" and kind != "offer_letter") or
            (user.role == "student" and kind != "supporting_document") or
            user.role not in ("admin", "student")):
        raise HTTPException(403, "Students upload supporting documents; administrators upload offer letters.")
    filename = normalized_filename(filename)
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Upload one PDF of at most 2 MiB.")
    if not content:
        raise HTTPException(422, "The PDF is empty.")
    digest = hashlib.sha256(content).hexdigest()
    content_hash = request_hash(payload, kind, filename, digest)
    offer = scoped_offer(session, user, offer_id)
    previous = prior_upload(session, user, offer, payload, content_hash)
    if previous is not None:
        return mutation_response(session, user, offer, previous)
    offers.check_version(offer, payload.version)
    # Bounded structural inspection runs outside database write locks. The
    # following locked checks must all run again after this potentially slow step.
    page_count = validate_document_pdf(content)
    # The per-college lock serializes UUID uniqueness across different offers;
    # the offer row lock also serializes quotas, reviews and existing stage writes.
    session.execute(text("SELECT pg_advisory_xact_lock(20260404, :college)"), {"college": user.college_id})
    offer = scoped_offer(session, user, offer_id, lock=True)
    previous = prior_upload(session, user, offer, payload, content_hash)
    if previous is not None:
        return mutation_response(session, user, offer, previous)
    offers.check_version(offer, payload.version)
    if kind == "offer_letter":
        if offer.offer_letter_status != "draft":
            raise HTTPException(409, "An issued offer letter cannot be replaced. Contact the placement cell about any change to its terms.")
    elif (offer.offer_letter_status != "issued" or
            offer.documents_status not in ("pending", "changes_requested")):
        raise HTTPException(409, "Upload supporting files after letter issuance and before submission, or after the administrator requests corrections.")
    count, used_bytes = stored_usage(session, user.college_id, offer.id)
    if count >= MAX_FILES or used_bytes + len(content) > MAX_OFFER_BYTES:
        raise HTTPException(413, "This offer has reached its retained-file limit (10 files or 10 MiB). Replaced revisions also count; contact the placement cell.")
    source = None
    if payload.replaces_document_id is not None:
        source = document_for(session, user, offer, payload.replaces_document_id)
        if not source.is_active or source.kind != kind:
            raise HTTPException(409, "Replace an active document of the same kind from this offer.")
    if kind == "offer_letter":
        active_letter = session.scalar(select(OfferDocument.id).where(OfferDocument.college_id == user.college_id,
            OfferDocument.offer_id == offer.id, OfferDocument.kind == "offer_letter", OfferDocument.is_active.is_(True)))
        if active_letter is not None and (source is None or source.id != active_letter):
            raise HTTPException(409, "This offer already has an active letter. Choose that letter for replacement while the offer is still a draft.")
    if source is not None:
        session.execute(update(OfferDocument).where(OfferDocument.college_id == user.college_id,
            OfferDocument.offer_id == offer.id, OfferDocument.id == source.id,
            OfferDocument.is_active.is_(True)).values(is_active=False))
    document = OfferDocument(college_id=user.college_id, offer_id=offer.id, kind=kind,
        label=payload.label, original_filename=filename, size_bytes=len(content), sha256=digest,
        page_count=page_count, content=content, uploaded_by=user.id,
        uploaded_offer_version=offer.version + 1, supersedes_document_id=source.id if source else None,
        idempotency_key=str(payload.idempotency_key), request_hash=content_hash)
    session.add(document)
    session.flush()
    event(session, user, document, "document_uploaded", payload.reason)
    if source is not None:
        event(session, user, source, "document_superseded", f"Replaced by document #{document.id}. {payload.reason}")
    # A file upload records evidence only. The five lifecycle stages are unchanged.
    offer_response = offers.save_change(session, user, offer, {}, "document_uploaded", payload.reason,
        notify_owner=kind != "offer_letter")
    return OfferDocumentMutation(offer=offer_response, document=metadata(document))


def review(session, user, offer_id, document_id, payload):
    if user.role != "admin":
        raise HTTPException(403, "Only placement administrators record document reviews.")
    offer = scoped_offer(session, user, offer_id, lock=True)
    offers.check_version(offer, payload.version)
    document = document_for(session, user, offer, document_id)
    if not document.is_active or document.review_status != "pending":
        raise HTTPException(409, "Review only a pending active file. A completed review remains in history; request corrections and upload a new revision instead.")
    if document.kind == "offer_letter":
        valid = offer.offer_letter_status == "draft"
    else:
        valid = offer.offer_letter_status == "issued" and offer.documents_status == "submitted"
    if not valid:
        raise HTTPException(409, "Review a draft offer letter before issuance, or review supporting documents after the student records submission.")
    session.execute(update(OfferDocument).where(OfferDocument.college_id == user.college_id,
        OfferDocument.offer_id == offer.id, OfferDocument.id == document.id,
        OfferDocument.is_active.is_(True), OfferDocument.review_status == "pending")
        .values(review_status=payload.review_status, reviewed_by=user.id,
            reviewed_at=datetime.now(timezone.utc), review_reason=payload.reason))
    event(session, user, document, "document_reviewed", f"Human review recorded as {payload.review_status}. {payload.reason}")
    # Reviewing an individual file does not verify the overall offer or issue a letter.
    offer_response = offers.save_change(session, user, offer, {}, "document_reviewed", payload.reason,
        notify_owner=document.kind != "offer_letter")
    return OfferDocumentMutation(offer=offer_response, document=metadata(document))


def download(session, user, offer_id, document_id):
    offer = scoped_offer(session, user, offer_id)
    document = document_for(session, user, offer, document_id)
    # Explicitly scope the bytea read instead of relying on an ORM lazy-load by ID.
    content = session.scalar(select(OfferDocument.content).where(OfferDocument.college_id == user.college_id,
        OfferDocument.offer_id == offer.id, OfferDocument.id == document.id))
    event(session, user, document, "download_requested",
        "Authenticated file download requested; this is not proof that the file was saved or read.")
    session.flush()
    return content, f"offer-document-{document.id}.pdf"


def events(session, user, offer_id, document_id, offset=0, limit=20):
    offer = scoped_offer(session, user, offer_id)
    document = document_for(session, user, offer, document_id)
    scope = (OfferDocumentEvent.college_id == user.college_id,
        OfferDocumentEvent.offer_id == offer.id, OfferDocumentEvent.document_id == document.id)
    total = session.scalar(select(func.count()).select_from(OfferDocumentEvent).where(*scope))
    rows = session.scalars(select(OfferDocumentEvent).where(*scope)
        .order_by(OfferDocumentEvent.id.desc()).offset(offset).limit(limit)).all()
    return OfferDocumentEventList(items=[OfferDocumentEventResponse.model_validate(row, from_attributes=True) for row in rows],
        total=total, offset=offset, limit=limit,
        explanation="Retained human file actions. A download request is an access audit, not proof that the file was saved or read. Reviews are recorded declarations, not automatic certification.")
