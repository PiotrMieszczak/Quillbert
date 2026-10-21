from collections.abc import Generator, Sequence
from dataclasses import dataclass

from app.adapters.llm.prompts import profile, research
from app.domain.assistant import Message, Mode
from app.ports.llm import Profile, Usage
from app.ports.search import Hit


@dataclass(frozen=True)
class Call:
    mode: Mode
    messages: list[dict[str, str]]


class FakeLLM:
    """Deterministic Gateway adapter. No network, no SDK.

    Runs the real `compose` and keeps what it built, so a test can read the prompt.
    """

    def __init__(self) -> None:
        self.calls: list[Call] = []

    def profile(self, mode: Mode) -> Profile:
        return profile(mode)

    def stream(
        self, *, mode: Mode, history: Sequence[Message], hits: Sequence[Hit]
    ) -> Generator[str | Usage, None, None]:
        if mode is not Mode.RESEARCH:
            raise ValueError("fake LLM only serves research mode")
        messages, _ = research.compose(history, hits)
        self.calls.append(Call(mode, messages))
        yield "Scripted reply from your sources "
        yield "[S1]."
        yield Usage("fake", 10, 5, 0.0)
