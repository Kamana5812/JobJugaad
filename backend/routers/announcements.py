"""Administrator-reviewed, tenant-scoped in-app drive communication."""
from fastapi import APIRouter, Depends, Query
from auth import admin_session
from engines import announcements
from schemas import (AnnouncementInput, AnnouncementPublishInput, AnnouncementOptions,
    AnnouncementPreviewResponse, AnnouncementResponse, AnnouncementList, AnnouncementRecipientList)

router = APIRouter(prefix="/admin/announcements", tags=["Drive announcements"])

@router.get("/options", response_model=AnnouncementOptions)
def options(context=Depends(admin_session)):
    return announcements.options(*context)

@router.post("/preview", response_model=AnnouncementPreviewResponse)
def preview(payload: AnnouncementInput, context=Depends(admin_session)):
    return announcements.preview(*context, payload)

@router.post("", response_model=AnnouncementResponse, status_code=201)
def publish(payload: AnnouncementPublishInput, context=Depends(admin_session)):
    return announcements.publish(*context, payload)

@router.get("", response_model=AnnouncementList)
def listing(offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50), context=Depends(admin_session)):
    return announcements.listing(*context, offset, limit)

@router.get("/{announcement_id}/recipients", response_model=AnnouncementRecipientList)
def recipients(announcement_id: int, offset: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=50), context=Depends(admin_session)):
    return announcements.recipients(*context, announcement_id, offset, limit)
