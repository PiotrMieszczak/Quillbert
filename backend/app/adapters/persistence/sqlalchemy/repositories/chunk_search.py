from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from app.ports.search import Hit

# Candidates each leg hands to the fusion; k only trims the fused list.
_POOL = 50
_RRF_K = 60

# Both legs are scoped by campaign and INDEXED status. The vector leg orders by the
# bare distance operator, so the planner may use the HNSW index; with the campaign
# filter it usually scans that campaign's chunks exactly, which is cheap at this
# size and never misses a match to approximate recall. The floor trims after the
# limit, which is safe because the rows are already in distance order.
# The campaign's own chunks, plus its owner's library and the vault for the campaign's
# system (ADR-0027). One GM's library never reaches another GM's campaign.
_IN_REACH = """(
    c.campaign_id = :campaign_id
    OR (c.campaign_id IS NULL
        AND (c.owner_id = :owner_id OR c.owner_id IS NULL)
        AND (cardinality(c.systems) = 0 OR :system_id = ANY(c.systems)))
)"""

# The layer a hit comes from, shown beside its citation; none for the campaign's own.
_LAYER = """CASE WHEN c.campaign_id IS NOT NULL THEN NULL
                WHEN c.owner_id IS NOT NULL THEN 'My library'
                ELSE COALESCE(d.attribution, 'Vault') END"""

_SEARCH = text(
    f"""
    WITH keyword AS (
        SELECT id, row_number() OVER (ORDER BY score DESC, id) AS pos
        FROM (
            SELECT c.id, ts_rank_cd(c.tsv, q.query) AS score
            FROM chunk c
            JOIN document d ON d.id = c.document_id
            CROSS JOIN LATERAL (
                SELECT websearch_to_tsquery(CAST(d.language AS regconfig), :text)
                    AS query
            ) q
            WHERE {_IN_REACH} AND d.status = 'indexed'
              AND c.tsv @@ q.query
            ORDER BY score DESC, c.id
            LIMIT :pool
        ) ranked
    ),
    semantic AS (
        SELECT id, row_number() OVER (ORDER BY dist, id) AS pos
        FROM (
            SELECT c.id, c.embedding <=> CAST(:vec AS vector) AS dist
            FROM chunk c
            JOIN document d ON d.id = c.document_id
            WHERE {_IN_REACH} AND d.status = 'indexed'
              AND c.embedding IS NOT NULL
              AND CAST(:vec AS vector) IS NOT NULL
            ORDER BY c.embedding <=> CAST(:vec AS vector)
            LIMIT :pool
        ) nearest
        WHERE dist <= 1 - :floor
    )
    SELECT c.id AS chunk_id, c.document_id, d.filename, c.page_from, c.heading,
           c.content, {_LAYER} AS attribution,
           CAST(COALESCE(1.0 / (:rrf_k + keyword.pos), 0)
                + COALESCE(1.0 / (:rrf_k + semantic.pos), 0)
                AS double precision) AS score
    FROM keyword
    FULL OUTER JOIN semantic ON semantic.id = keyword.id
    JOIN chunk c ON c.id = COALESCE(keyword.id, semantic.id)
    JOIN document d ON d.id = c.document_id
    ORDER BY score DESC, c.id
    LIMIT :k
    """
)


class SqlChunkSearch:
    """ChunkSearch over PostgreSQL: tsvector and pgvector legs, RRF-fused in SQL.

    `floor` is a cosine-similarity floor on the vector leg; the keyword leg admits
    only chunks that match the query. A chunk neither leg admits is never returned.
    """

    def __init__(self, sessions: sessionmaker[Session], floor: float) -> None:
        self._sessions = sessions
        self._floor = floor

    def search(
        self,
        campaign_id: str,
        owner_id: str | None,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        if k < 1 or (not text.strip() and vector is None):
            return []
        params = {
            "campaign_id": campaign_id,
            "owner_id": owner_id,
            "system_id": system_id,
            "text": text,
            "vec": None if vector is None else str(vector),
            "floor": self._floor,
            "pool": _POOL,
            "rrf_k": _RRF_K,
            "k": k,
        }
        with self._sessions() as session:
            return [Hit(**row) for row in session.execute(_SEARCH, params).mappings()]
