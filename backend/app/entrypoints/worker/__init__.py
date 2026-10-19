"""The background ingestion runner: claims queued documents one at a time."""

import logging
import threading

from app.application.documents import IngestDocument, IngestOutcome
from app.ports.repositories import DocumentRepo

logger = logging.getLogger(__name__)

IDLE_SECONDS = 2.0
# Backoff while the embedder or the database is down: 30 s doubling to 15 min.
_BACKOFF_START = 30.0
_BACKOFF_MAX = 900.0


class IngestionWorker:
    """Runs IngestDocument on a daemon thread until stopped.

    shortcut: one worker thread inside the API process, and start() requeues every
    `processing` document, which is only safe with a single process. Before running
    more than one replica, move this to its own process with a claim lease.
    """

    def __init__(self, ingest: IngestDocument, repo: DocumentRepo) -> None:
        self._ingest = ingest
        self._repo = repo
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="ingestion", daemon=True)

    def start(self) -> None:
        requeued = self._repo.requeue_processing()
        if requeued:
            logger.warning("requeued %d interrupted document(s)", requeued)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        self._thread.join(timeout)

    def _run(self) -> None:
        backoff = _BACKOFF_START
        while not self._stop.is_set():
            try:
                outcome = self._ingest.execute()
            except Exception:
                logger.exception("ingestion worker error; backing off %.0fs", backoff)
                outcome = IngestOutcome.DEFERRED
            if outcome is IngestOutcome.DONE:
                backoff = _BACKOFF_START
            elif outcome is IngestOutcome.IDLE:
                self._stop.wait(IDLE_SECONDS)
            else:
                self._stop.wait(backoff)
                backoff = min(backoff * 2, _BACKOFF_MAX)
