from fastapi import FastAPI

from app.entrypoints.http.errors import register_error_handlers
from app.entrypoints.http.routers.assistant import router as assistant_router


def create_http_app(*, api_docs: bool = False) -> FastAPI:
    app = FastAPI(
        title="Quillbert",
        docs_url="/docs" if api_docs else None,
        redoc_url="/redoc" if api_docs else None,
    )
    register_error_handlers(app)
    app.include_router(assistant_router)
    return app
