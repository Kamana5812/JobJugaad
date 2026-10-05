"""Explicit operator maintenance gate for a database cutover; disabled by default."""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class MigrationMaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Block every data route, including GET routes that may refresh cached
        # calculations. Operator SQL backup uses a separate private connection.
        if os.environ.get('MIGRATION_MAINTENANCE') == 'yes' and request.url.path != '/health':
            return JSONResponse(status_code=503, headers={'Retry-After': '60'},
                content={'detail': 'JobJugaad is temporarily unavailable for scheduled maintenance. Please try again shortly.'})
        return await call_next(request)
