from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime settings, read from the environment."""

    # postgresql+psycopg://user:password@host:5432/dbname. Unset: in-memory storage.
    database_url: str | None = None

    # https://<project-ref>.supabase.co. Unset: every authenticated route returns 401.
    supabase_url: str | None = None
