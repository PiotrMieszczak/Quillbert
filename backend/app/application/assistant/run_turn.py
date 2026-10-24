import logging
import re
import time
from collections.abc import Generator, Iterator
from contextlib import closing
from uuid import uuid4

from app.application.dto import (
    TurnCited,
    TurnDelta,
    TurnEvent,
    TurnFailed,
    TurnFinished,
    TurnSearched,
    TurnStarted,
)
from app.domain.assistant import Citation, Message, Role, Trace
from app.domain.shared import NotFound, ValidationFailed
from app.ports.clock import Clock
from app.ports.embeddings import Embedder, EmbeddingUnavailable
from app.ports.llm import LLMError, LLMProvider, Usage, source_labels
from app.ports.repositories import ConversationRepo
from app.ports.search import ChunkSearch, Hit

logger = logging.getLogger(__name__)

# [S1], [S2] and [S1, S2]; an id the model made up is dropped later.
_CITE = re.compile(r"\[(S\d+(?:[,\s]+S\d+)*)\]")


def _plural(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _ms(start: float, end: float) -> int:
    return round((end - start) * 1000)


class RunAssistantTurn:
    def __init__(
        self,
        repo: ConversationRepo,
        llm: LLMProvider,
        clock: Clock,
        search: ChunkSearch,
        embedder: Embedder | None,
        *,
        top_k: int = 6,
        history_messages: int = 6,
    ) -> None:
        self._repo = repo
        self._llm = llm
        self._clock = clock
        self._search = search
        self._embedder = embedder
        self._top_k = top_k
        self._history_messages = history_messages

    def execute(
        self,
        *,
        campaign_id: str,
        conversation_id: int,
        content: str,
        owner_id: str | None = None,
        system_id: str | None = None,
    ) -> Generator[TurnEvent, None, None]:
        """`owner_id` and `system_id` are the campaign's: they reach the GM's library
        documents for that system (ADR-0027)."""
        text = content.strip()
        if not text:
            raise ValidationFailed("content is required")

        conversation = self._repo.get(conversation_id)
        if conversation is None or conversation.campaign_id != campaign_id:
            raise NotFound("conversation not found")

        self._repo.add_message(
            Message(
                id=self._repo.next_message_id(),
                conversation_id=conversation.id,
                role=Role.USER,
                content=text,
                created_at=self._clock.now(),
                mode=conversation.mode,
            )
        )

        assistant_id = self._repo.next_message_id()
        run_id = uuid4().hex
        yield TurnStarted(
            conversation_id=conversation.id,
            run_id=run_id,
            message_id=assistant_id,
        )

        try:
            yield from self._answer(
                (campaign_id, owner_id, system_id),
                conversation.id,
                assistant_id,
                text,
                run_id,
            )
        except LLMError:
            logger.exception("assistant turn failed at the provider")
            yield TurnFailed("provider_error", "The assistant could not answer.")
        except Exception:
            logger.exception("assistant turn failed")
            yield TurnFailed("internal_error", "The assistant could not answer.")

    def _answer(
        self,
        reach: tuple[str, str | None, str | None],
        conversation_id: int,
        assistant_id: int,
        text: str,
        run_id: str,
    ) -> Iterator[TurnEvent]:
        started = time.monotonic()
        conversation = self._repo.get(conversation_id)
        if conversation is None:
            raise NotFound("conversation not found")
        mode = conversation.mode
        profile = self._llm.profile(mode)
        # Oldest messages drop first; a window must open on a user message.
        history = conversation.messages[-self._history_messages :]
        while history and history[0].role is not Role.USER:
            history = history[1:]

        hits = self._search.search(*reach, text, self._query_vector(text), self._top_k)
        documents = len({hit.document_id for hit in hits})
        searched = (
            f"Searched {_plural(documents, 'document')} · "
            f"{_plural(len(hits), 'passage')}"
        )
        yield TurnSearched(query=text, result=searched)

        usage: Usage | None = None
        first_token: float | None = None
        if not hits:
            reply = profile.refusal
            yield TurnDelta(message_id=assistant_id, text=reply)
        else:
            parts: list[str] = []
            deltas = self._llm.stream(mode=mode, history=history, hits=hits)
            with closing(deltas):
                for item in deltas:
                    if isinstance(item, Usage):
                        usage = item
                        continue
                    if first_token is None:
                        first_token = time.monotonic()
                    parts.append(item)
                    yield TurnDelta(message_id=assistant_id, text=item)
            reply = "".join(parts)
            if not reply.strip():
                raise LLMError("the model returned no text")

        citations = self._citations(reply, hits)
        end = time.monotonic()
        self._repo.add_message(
            Message(
                id=assistant_id,
                conversation_id=conversation_id,
                role=Role.ASSISTANT,
                content=reply,
                created_at=self._clock.now(),
                mode=mode,
                tool_label=searched,
                citations=citations,
                trace=Trace(
                    prompt_id=profile.prompt_id,
                    prompt_version=profile.version,
                    model=usage and usage.model,
                    ttft_ms=None if first_token is None else _ms(started, first_token),
                    duration_ms=_ms(started, end),
                    prompt_tokens=usage and usage.prompt_tokens,
                    completion_tokens=usage and usage.completion_tokens,
                    cost_usd=usage and usage.cost_usd,
                ),
            )
        )
        for citation in citations:
            yield TurnCited(citation)
        yield TurnFinished(
            conversation_id=conversation_id, run_id=run_id, message_id=assistant_id
        )

    def _query_vector(self, text: str) -> list[float] | None:
        if self._embedder is None:
            return None
        try:
            return self._embedder.embed([text], "query")[0]
        except EmbeddingUnavailable:
            # Keyword search alone still answers (ADR-0016).
            logger.warning("query embedding unavailable; searching by keyword only")
            return None

    @staticmethod
    def _citations(reply: str, hits: list[Hit]) -> tuple[Citation, ...]:
        labels = source_labels(hits)
        seen: dict[str, Hit] = {}
        for group in _CITE.findall(reply):
            for label in re.findall(r"S\d+", group):
                if label in labels:
                    seen.setdefault(label, labels[label])
        return tuple(
            Citation(
                label,
                hit.chunk_id,
                hit.document_id,
                hit.filename,
                hit.page_from,
                hit.heading,
                hit.attribution,
            )
            for label, hit in seen.items()
        )
