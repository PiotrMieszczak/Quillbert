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

    # Chunks the Research mode is shown per question.
    retrieval_top_k: int = 6

    # Cosine similarity a chunk must reach to count as a vector match; below it a
    # question has no result and Research refuses (AC-003). Untuned: set it from
    # real queries, not from the test vectors.
    retrieval_floor: float = 0.5

    # The chat model for Research answers (ADR-0019). Must be served zero-retention by
    # `chat_provider`; the Gateway refuses a provider outside its allowlist.
    chat_model: str = "google/gemini-3.5-flash-lite"

    # OpenRouter endpoint tag for chat. global was the cheapest and fastest of the
    # zero-retention ones measured; eu serves flash-lite too, at +10% and no better.
    chat_provider: str = "google-vertex/global"

    # How hard the model thinks before it answers: "minimal", "low", "medium" or "high".
    # Empty sends nothing. Some endpoints reject "none" ("reasoning is mandatory").
    chat_reasoning_effort: str = "low"

    # Cap on the reply, in tokens. Research answers are short paragraphs.
    chat_max_tokens: int = 700

    # Most recent messages replayed to the model, the new question included.
    history_messages: int = 6
