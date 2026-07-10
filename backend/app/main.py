from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.exceptions import AppError
from app.routers import lines, stops, system


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API de consulta ao transporte coletivo de Belo Horizonte.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    application.include_router(system.router)
    application.include_router(lines.router)
    application.include_router(stops.router)

    @application.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=error.message,
            details=error.details,
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=422,
            code="validation_error",
            message="Os parâmetros enviados são inválidos.",
            details={"errors": error.errors()},
        )

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        message = str(error.detail)
        if error.status_code == 404:
            message = "Rota não encontrada."
        return _error_response(
            request,
            status_code=error.status_code,
            code="http_error",
            message=message,
        )

    return application


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


app = create_app()
