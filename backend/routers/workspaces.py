from fastapi import APIRouter, Depends
from auth import authenticated_session
from schemas import WorkspaceList, WorkspaceRequestInput, WorkspaceSwitchInput, TokenResponse
from engines import recruiter_workspaces

router = APIRouter(prefix='/recruiter/workspaces', tags=['Recruiter workspaces'])

@router.get('', response_model=WorkspaceList)
def list_workspaces(context=Depends(authenticated_session)):
    return recruiter_workspaces.list_workspaces(context)

@router.post('', response_model=WorkspaceList, status_code=201)
def request_workspace(payload: WorkspaceRequestInput, context=Depends(authenticated_session)):
    recruiter_workspaces.request_workspace(context, payload)
    return recruiter_workspaces.list_workspaces(context)

@router.post('/switch', response_model=TokenResponse)
def switch_workspace(payload: WorkspaceSwitchInput, context=Depends(authenticated_session)):
    return recruiter_workspaces.switch_workspace(context, payload.college_id)
