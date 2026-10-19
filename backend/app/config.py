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

    # OpenRouter key (OPEN_ROUTER_API_KEY). Unset: a fake embedder, no network.
    open_router_api_key: str | None = None

    # The one embedding model for every user and campaign (ADR-0021). Changing it is a
    # re-embed migration, not a setting: the startup check refuses a mismatch.
    embedding_model: str = "google/gemini-embedding-2"

    # OpenRouter endpoint tag; must be a zero-retention one. google-vertex/eu is
    # nearest the Supabase region.
    embedding_provider: str = "google-vertex/eu"

    # Run the ingestion worker inside the API process (INGESTION_WORKER).
    ingestion_worker: bool = True

    # Tesseract language data for scanned pages; both must be installed.
    ocr_languages: str = "eng+pol"
