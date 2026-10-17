from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime settings, read from the environment."""

    # postgresql+psycopg://user:password@host:5432/dbname. Unset: in-memory storage.
    database_url: str | None = None

    # https://<project-ref>.supabase.co. Unset: every authenticated route returns 401.
    supabase_url: str | None = None

    # Serve Swagger UI (/docs) and ReDoc (/redoc). Off unless set: private in prod.
    enable_api_docs: bool = False

    # Where uploaded files live (the local-disk FileStore). Mount a volume here.
    file_store_path: str = "./data/files"

    # Largest accepted upload, in MB.
    max_upload_mb: int = 200
