"""Error codes, the ApiError exception and response-envelope helpers."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Fixed error codes used by the frontend (see docs/API.md, "Error codes").
VALIDATION_ERROR = "VALIDATION_ERROR"
UNAUTHORIZED = "UNAUTHORIZED"
FORBIDDEN = "FORBIDDEN"
NOT_FOUND = "NOT_FOUND"
METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
CONFLICT = "CONFLICT"
INTERNAL_ERROR = "INTERNAL_ERROR"


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str,
                 details: list | None = None, headers: dict | None = None):
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def error_body(code: str, message: str, details: list | None = None) -> dict:
    error = {"code": code, "message": message}
    if details:  # details appear only for validation errors
        error["details"] = details
    return {"success": False, "error": error}


def ok(message: str, data, status: int = 200, meta: dict | None = None) -> JSONResponse:
    body = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return JSONResponse(body, status_code=status)


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        return JSONResponse(error_body(exc.code, exc.message, exc.details),
                            status_code=exc.status, headers=exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            code, msg = NOT_FOUND, "The requested endpoint does not exist."
        elif exc.status_code == 405:
            code, msg = METHOD_NOT_ALLOWED, "This HTTP method is not supported for this endpoint."
        else:
            code, msg = INTERNAL_ERROR, "The request could not be processed."
        return JSONResponse(error_body(code, msg), status_code=exc.status_code,
                            headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "request",
                    "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(error_body(
            VALIDATION_ERROR, "The request contains invalid or missing fields.", details),
            status_code=400)

    @app.exception_handler(Exception)
    async def unexpected(_: Request, __: Exception):
        # Never leak stack traces or internals to the client.
        return JSONResponse(error_body(INTERNAL_ERROR, "An unexpected server error occurred."),
                            status_code=500)
