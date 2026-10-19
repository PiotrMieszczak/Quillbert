from fastapi import FastAPI

from app.entrypoints.http.errors import register_error_handlers
from app.entrypoints.http.routers.assistant import router as assistant_router
from app.entrypoints.http.routers.documents import router as documents_router


def create_http_app(*, api_docs: bool = False) -> FastAPI:
    app = FastAPI(
        title="Quillbert",
        docs_url="/docs" if api_docs else None,
        redoc_url="/redoc" if api_docs else None,
    )
    register_error_handlers(app)
    app.include_router(assistant_router)
    app.include_router(documents_router)
    return app
