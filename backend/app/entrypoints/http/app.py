from fastapi import FastAPI

from app.entrypoints.http.errors import register_error_handlers
from app.entrypoints.http.routers.assistant import router as assistant_router


def create_http_app() -> FastAPI:
    app = FastAPI(title="Quillbert")
    register_error_handlers(app)
    app.include_router(assistant_router)
    return app
