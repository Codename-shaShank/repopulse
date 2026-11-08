import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import analytics, exports, repositories
from app.core.config import get_settings
from app.core.errors import AppError, RateLimitedError
from app.core.logging import configure_logging
from app.db.session import engine
from app.schemas.analytics import HealthStatus

logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=API_VERSION,
        description=(
            "Track public GitHub repositories, store metric snapshots over time, "
            "and export the history as CSV for analysis."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {}
        if isinstance(exc, RateLimitedError) and exc.reset_at:
            headers["X-RateLimit-Reset-At"] = exc.reset_at
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": type(exc).__name__},
            headers=headers,
        )

    @app.get("/health", response_model=HealthStatus, tags=["health"])
    def health() -> HealthStatus:
        database = "ok"
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            # Never surface the connection string or driver internals here.
            logger.exception("Database health check failed")
            database = "unavailable"
        return HealthStatus(
            status="ok" if database == "ok" else "degraded",
            database=database,
            version=API_VERSION,
        )

    app.include_router(repositories.router, prefix=settings.api_v1_prefix)
    app.include_router(analytics.router, prefix=settings.api_v1_prefix)
    app.include_router(exports.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
