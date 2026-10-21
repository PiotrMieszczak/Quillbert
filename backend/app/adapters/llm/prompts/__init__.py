from app.adapters.llm.prompts import research
from app.domain.assistant import Mode
from app.ports.llm import Profile


def profile(mode: Mode) -> Profile:
    if mode is not Mode.RESEARCH:
        raise ValueError(f"no prompt for mode {mode!r} yet")
    return Profile(research.PROMPT_ID, research.VERSION, research.REFUSAL)


__all__ = ["profile", "research"]
