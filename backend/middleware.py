from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class CanonicalPathMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce canonical path rules:
    - No trailing slashes allowed
    - Return 404 if present
    """
    async def dispatch(self, request: Request, call_next):
        # Check if the path ends with a slash (but not the root path '/')
        if request.url.path != '/' and request.url.path.endswith('/'):
            return JSONResponse(
                status_code=404,
                content={"error": "not_found"}
            )

        response = await call_next(request)
        return response