"""Account controls available before college approval; staff review uses admin authorization."""
from fastapi import APIRouter, Depends
from auth import authenticated_session, admin_session
from engines import privacy
from schemas import DataRequestInput, DataRequestReview, DataRequestResponse, AccountExportResponse
router=APIRouter(tags=['Account data'])

@router.get('/account/export',response_model=AccountExportResponse)
def export(context=Depends(authenticated_session)):
    return privacy.export_account(*context)

@router.get('/account/data-requests',response_model=list[DataRequestResponse])
def own_requests(context=Depends(authenticated_session)):
    return privacy.requests(*context)

@router.post('/account/data-requests',response_model=DataRequestResponse,status_code=201)
def request(payload:DataRequestInput,context=Depends(authenticated_session)):
    return privacy.create(*context,payload)

@router.post('/account/data-requests/{request_id}/withdraw',response_model=DataRequestResponse)
def withdraw(request_id:int,context=Depends(authenticated_session)):
    return privacy.withdraw(*context,request_id)

@router.get('/admin/data-requests',response_model=list[DataRequestResponse])
def review_queue(context=Depends(admin_session)):
    return privacy.requests(*context,admin=True)

@router.post('/admin/data-requests/{request_id}/review',response_model=DataRequestResponse)
def review(request_id:int,payload:DataRequestReview,context=Depends(admin_session)):
    return privacy.review(*context,request_id,payload)
