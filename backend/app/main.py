import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.exceptions import AppError
from app.observability import logger, record_request
from app.routers import lines, realtime, stops, system


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
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
    application.add_middleware(GZipMiddleware, minimum_size=1_000)
    application.include_router(system.router)
    application.include_router(lines.router)
    application.include_router(stops.router)
    application.include_router(realtime.router)

    @application.middleware("http")
    async def add_request_id(request: Request, call_next):
        started_at = perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise
        response.headers["X-Request-ID"] = request_id
        duration_ms = (perf_counter() - started_at) * 1_000
        response.headers["Server-Timing"] = f"app;dur={duration_ms:.2f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self)"
        matched_route = request.scope.get("route")
        metric_path = getattr(matched_route, "path", request.url.path)
        record_request(request.method, metric_path, response.status_code)
        logger.info(
            "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
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

    @application.exception_handler(SQLAlchemyError)
    async def handle_database_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
        logger.exception("database_unavailable request_id=%s", request.state.request_id)
        return _error_response(
            request,
            status_code=503,
            code="database_unavailable",
            message="Os dados em tempo real estao temporariamente indisponiveis.",
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
