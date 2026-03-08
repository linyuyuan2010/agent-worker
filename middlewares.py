from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import config

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # if request.headers.get("X-ASAuth") not in config.ASAuth_TOKENS:
        #     return JSONResponse(
        #         status_code=status.HTTP_403_FORBIDDEN, 
        #         content={"success": False, "result": "auth fail"}
        #    )
        
        response = await call_next(request)
        return response