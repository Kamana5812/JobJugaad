"""Role-scoped private offer files; no public object URLs or inline rendering."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError

from auth import admin_session, student_session, owned_student
from engines import offer_documents
from engines.document_pdf import MAX_BYTES
from schemas import (OfferDocumentUpload, OfferDocumentReview, OfferDocumentList,
    OfferDocumentMutation, OfferDocumentEventList)

router = APIRouter(tags=["Offer documents"])


def upload_payload(version, label, reason, idempotency_key, replaces_document_id):
    try:
        return OfferDocumentUpload(version=version, label=label, reason=reason,
            idempotency_key=idempotency_key, replaces_document_id=replaces_document_id)
    except ValidationError:
        raise HTTPException(422, "Use a label of 3–160 characters and a reason of 10–1000 characters without null characters, a valid upload key and the current offer version.") from None


def file_content(file):
    try:
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(422, "Upload a PDF file; other file formats are not supported.")
        content = file.file.read(MAX_BYTES + 1)
    finally:
        file.file.close()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Upload one PDF of at most 2 MiB.")
    return content


def student_offer(context, student_id, offer_id):
    session, user = context
    student = owned_student(session, user, student_id)
    offer = offer_documents.scoped_offer(session, user, offer_id)
    if offer.student_id != student.id:
        raise HTTPException(404, "Offer not found.")
    return session, user


def attachment(context, offer_id, document_id):
    content, filename = offer_documents.download(*context, offer_id, document_id)
    return Response(content=content, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "private, no-store, max-age=0",
        "Pragma": "no-cache", "Expires": "0",
        "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"})


@router.get("/admin/offers/{offer_id}/documents", response_model=OfferDocumentList)
def admin_documents(offer_id: int, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50),
        context=Depends(admin_session)):
    return offer_documents.listing(*context, offer_id, offset, limit)


@router.post("/admin/offers/{offer_id}/documents", response_model=OfferDocumentMutation, status_code=201)
def admin_upload(offer_id: int, file: UploadFile = File(...), version: int = Form(..., ge=1),
        label: str = Form(..., min_length=3, max_length=160), reason: str = Form(..., min_length=10, max_length=1000),
        idempotency_key: UUID = Form(...), replaces_document_id: int | None = Form(None, gt=0),
        kind: Literal["offer_letter"] = Form("offer_letter"), context=Depends(admin_session)):
    session, user = context
    offer_documents.scoped_offer(session, user, offer_id)
    payload = upload_payload(version, label, reason, idempotency_key, replaces_document_id)
    content = file_content(file)
    return offer_documents.upload(session, user, offer_id, payload, content, file.filename, "offer_letter")


@router.get("/admin/offers/{offer_id}/documents/{document_id}/download", response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "Private PDF attachment; download request audited."}})
def admin_download(offer_id: int, document_id: int, context=Depends(admin_session)):
    return attachment(context, offer_id, document_id)


@router.get("/admin/offers/{offer_id}/documents/{document_id}/events", response_model=OfferDocumentEventList)
def admin_events(offer_id: int, document_id: int, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50),
        context=Depends(admin_session)):
    return offer_documents.events(*context, offer_id, document_id, offset, limit)


@router.post("/admin/offers/{offer_id}/documents/{document_id}/review", response_model=OfferDocumentMutation)
def admin_review(offer_id: int, document_id: int, payload: OfferDocumentReview, context=Depends(admin_session)):
    return offer_documents.review(*context, offer_id, document_id, payload)


@router.get("/students/{student_id}/offers/{offer_id}/documents", response_model=OfferDocumentList)
def student_documents(student_id: int, offer_id: int, offset: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=50), context=Depends(student_session)):
    return offer_documents.listing(*student_offer(context, student_id, offer_id), offer_id, offset, limit)


@router.post("/students/{student_id}/offers/{offer_id}/documents", response_model=OfferDocumentMutation, status_code=201)
def student_upload(student_id: int, offer_id: int, file: UploadFile = File(...), version: int = Form(..., ge=1),
        label: str = Form(..., min_length=3, max_length=160), reason: str = Form(..., min_length=10, max_length=1000),
        idempotency_key: UUID = Form(...), replaces_document_id: int | None = Form(None, gt=0),
        kind: Literal["supporting_document"] | None = Form(None), context=Depends(student_session)):
    session, user = student_offer(context, student_id, offer_id)
    payload = upload_payload(version, label, reason, idempotency_key, replaces_document_id)
    content = file_content(file)
    return offer_documents.upload(session, user, offer_id, payload, content, file.filename, "supporting_document")


@router.get("/students/{student_id}/offers/{offer_id}/documents/{document_id}/download", response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "Owned PDF attachment; download request audited."}})
def student_download(student_id: int, offer_id: int, document_id: int, context=Depends(student_session)):
    return attachment(student_offer(context, student_id, offer_id), offer_id, document_id)


@router.get("/students/{student_id}/offers/{offer_id}/documents/{document_id}/events", response_model=OfferDocumentEventList)
def student_events(student_id: int, offer_id: int, document_id: int, offset: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=50), context=Depends(student_session)):
    return offer_documents.events(*student_offer(context, student_id, offer_id), offer_id, document_id, offset, limit)
