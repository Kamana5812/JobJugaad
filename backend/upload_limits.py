"""Bound request bodies before multipart parsing; route authorization still applies."""
import re

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.responses import JSONResponse

from auth import current_identity
from engines.document_pdf import MAX_BYTES

MAX_UPLOAD_BODY_BYTES = MAX_BYTES + 64 * 1024
UPLOAD_PATH = re.compile(r"^/(?:admin/offers/[^/]+|students/[^/]+/offers/[^/]+)/documents/?$")


class DocumentUploadLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope["type"] != "http" or scope["method"] != "POST"
                or not UPLOAD_PATH.fullmatch(scope["path"])):
            return await self.app(scope, receive, send)
        headers = scope.get("headers", [])
        authorization = dict(headers).get(b"authorization", b"").decode("latin-1")
        scheme, _, token = authorization.partition(" ")
        credentials = (HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
                       if scheme.lower() == "bearer" and token else None)
        try:
            identity = current_identity(credentials)
            expected_role = "admin" if scope["path"].startswith("/admin/") else "student"
            if identity["role"] != expected_role:
                raise HTTPException(403, "This role cannot upload these documents.")
        except HTTPException as error:
            return await JSONResponse({"detail": error.detail}, status_code=error.status_code,
                                      headers=error.headers)(scope, receive, send)
        lengths = [value for key, value in headers if key == b"content-length"]
        if len(lengths) > 1 or (lengths and (len(lengths[0]) > 20 or not lengths[0].isdigit())):
            return await JSONResponse({"detail": "Invalid upload request length."}, status_code=400)(scope, receive, send)
        if lengths and int(lengths[0]) > MAX_UPLOAD_BODY_BYTES:
            return await self.too_large(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_UPLOAD_BODY_BYTES:
                return await self.too_large(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, bounded_receive, send)

    @staticmethod
    async def too_large(scope, receive, send):
        await JSONResponse({"detail": "Upload request is too large. Use one PDF of at most 2 MiB and short form fields."},
                           status_code=413)(scope, receive, send)
