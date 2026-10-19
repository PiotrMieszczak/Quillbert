from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlalchemy.tables import EmbeddingSpaceRow


def check_embedding_space(
    sessions: sessionmaker[Session], model: str, dimensions: int
) -> None:
    """Refuse to embed with a model other than the one that produced the stored vectors
    (ADR-0021 decision 2): vectors from two models are not comparable."""
    with sessions() as session:
        row = session.scalars(select(EmbeddingSpaceRow)).one()
    if (row.model, row.dimensions) != (model, dimensions):
        raise RuntimeError(
            f"Stored embeddings come from {row.model} ({row.dimensions} dims) but the "
            f"configured model is {model} ({dimensions} dims). Changing model is a "
            "re-embed migration."
        )
