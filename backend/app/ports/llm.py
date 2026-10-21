from collections.abc import Generator, Sequence
from dataclasses import dataclass
from typing import Protocol

from app.domain.assistant import Message, Mode
from app.ports.search import Hit


class LLMError(Exception):
    """The provider failed or refused the call. The turn ends without a reply."""


@dataclass(frozen=True)
class Usage:
    """What the provider reported for one call. The last item a stream yields."""

    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float | None


@dataclass(frozen=True)
class Profile:
    """The parts of a mode's prompt the use case records or returns itself."""

    prompt_id: str
    version: str
    refusal: str


def source_labels(hits: Sequence[Hit]) -> dict[str, Hit]:
    """The ids the model is shown, S1.. in rank order. The map stays on the server."""
    return {f"S{n}": hit for n, hit in enumerate(hits, 1)}


class LLMProvider(Protocol):
    """The Gateway boundary (BND-002, ADR-0006). Adapters live in app.adapters.llm."""

    def profile(self, mode: Mode) -> Profile: ...

    def stream(
        self, *, mode: Mode, history: Sequence[Message], hits: Sequence[Hit]
    ) -> Generator[str | Usage, None, None]:
        """Yield text deltas, then one Usage. Prompting and grounding belong to the
        adapter; `history` ends with the question. Raises LLMError. Closing the
        generator abandons the upstream call."""
        ...
