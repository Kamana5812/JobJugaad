"""Every feed/read query is scoped to the authenticated recipient and college."""
from fastapi import APIRouter, Depends, Query
from auth import authenticated_session
from engines import notifications
from schemas import NotificationFeed, NotificationResponse
router=APIRouter(prefix="/notifications",tags=["Simulated notifications"])

@router.get("",response_model=NotificationFeed)
def feed(offset:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=50),context=Depends(authenticated_session)):
    return notifications.feed(*context,offset,limit)

@router.put("/{notification_id}/read",response_model=NotificationResponse)
def mark_read(notification_id:int,context=Depends(authenticated_session)):
    return notifications.mark_read(*context,notification_id)
