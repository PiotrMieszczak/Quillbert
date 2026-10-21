"""Bake-off for the Research chat model, over the real client and the real prompt.

    python -m evals.run --env ../.env --out /some/dir \
        google/gemini-3.5-flash-lite@google-vertex/global@minimal \
        anthropic/claude-haiku-5.5@amazon-bedrock@minimal

Each candidate is `model@endpoint-tag@reasoning-effort` (`none` sends no effort).
A candidate is skipped unless OpenRouter's live zero-retention list names that exact
pair (ADR-0019). The corpus is invented, so no campaign text leaves the machine. Not
part of pytest: it spends money.
"""

import argparse
import json
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import httpx
from app.adapters.llm.openrouter import OpenRouterChat
from app.adapters.llm.prompts import research
from app.domain.assistant import Message, Mode, Role
from app.ports.llm import LLMError, Usage, source_labels
from dotenv import dotenv_values

from evals.cases import CASES, Case
from evals.corpus import hits

ZDR_LIST = "https://openrouter.ai/api/v1/endpoints/zdr"
NOW = datetime(2026, 10, 21, tzinfo=UTC)
CITE = re.compile(r"\[(S\d+(?:[,\s]+S\d+)*)\]")
GAP = re.compile(
    r"not (cover|include|mention|specif|provide|say|state|contain|address)|"
    r"no (information|mention|details?)|do(es)? not|doesn't|don't|isn't|aren't|"
    r"nothing|cannot|can't",
    re.I,
)
CONFLICT = re.compile(
    r"conflict|disagree|contradict|differ|inconsisten|discrepan", re.I
)
MARKDOWN = re.compile(r"(?m)^\s{0,3}(#{1,6}\s|[-*•]\s|\d+[.)]\s)|\*\*|^\s*\|.*\|")


def _messages(case: Case) -> list[Message]:
    turns = [*case.history, ("user", case.question)]
    return [
        Message(n, 1, Role(role), text, NOW, Mode.RESEARCH)
        for n, (role, text) in enumerate(turns, 1)
    ]


def score(case: Case, reply: str, completion_tokens: int | None, max_tokens: int):
    labels = set(source_labels(hits(*case.hits)))
    cited = {s for group in CITE.findall(reply) for s in re.findall(r"S\d+", group)}
    refused = reply.strip().strip("\"'“”") == research.REFUSAL
    problems = []
    if case.refuse:
        if not refused:
            # Starting with the sentence is safe (nothing invented), only wordy.
            problems.append(
                "refusal plus extra text"
                if reply.strip().startswith(research.REFUSAL)
                else "answered instead of refusing"
            )
    else:
        if refused:
            problems.append("false refusal")
        for alternatives in case.facts:
            if not any(re.search(a, reply, re.I) for a in alternatives):
                problems.append(f"missing fact {alternatives[0]!r}")
        for label in case.cites:
            if label not in cited:
                problems.append(f"did not cite {label}")
        if case.gap and not GAP.search(reply):
            problems.append("did not say what is uncovered")
        if case.conflict and not CONFLICT.search(reply):
            problems.append("did not flag the conflict")
    for pattern in case.forbidden:
        if re.search(pattern, reply, re.I):
            problems.append(f"forbidden {pattern!r}")
    return {
        "problems": problems,
        "passed": not problems,
        "refused": refused,
        "bad_cites": sorted(cited - labels),
        "markdown": bool(MARKDOWN.search(reply)),
        "truncated": completion_tokens is not None and completion_tokens >= max_tokens,
    }


def run_candidate(
    key: str,
    model: str,
    tag: str,
    effort: str | None,
    reps: int,
    cases: list[Case],
    max_tokens: int,
):
    chat = OpenRouterChat(
        api_key=key,
        model=model,
        provider=tag,
        max_tokens=max_tokens,
        client=httpx.Client(timeout=httpx.Timeout(90, connect=10)),
        allowed=frozenset({tag}),
        reasoning_effort=effort,
    )
    rows = []
    for case in cases:
        for rep in range(reps):
            started = time.monotonic()
            first = None
            text: list[str] = []
            usage = None
            error = None
            try:
                for item in chat.stream(
                    mode=Mode.RESEARCH, history=_messages(case), hits=hits(*case.hits)
                ):
                    if isinstance(item, Usage):
                        usage = item
                    else:
                        first = first or time.monotonic()
                        text.append(item)
            except LLMError as exc:
                error = str(exc)
            reply = "".join(text)
            tokens = usage.completion_tokens if usage else None
            rows.append(
                {
                    "model": model,
                    "tag": tag,
                    "effort": effort,
                    "case": case.id,
                    "kind": case.kind,
                    "rep": rep,
                    "reply": reply,
                    "error": error,
                    "ttft_ms": None
                    if first is None
                    else round((first - started) * 1000),
                    "duration_ms": round((time.monotonic() - started) * 1000),
                    "prompt_tokens": usage.prompt_tokens if usage else None,
                    "completion_tokens": tokens,
                    "cost_usd": usage.cost_usd if usage else None,
                    "served_by": usage.model if usage else None,
                    **(
                        score(case, reply, tokens, max_tokens)
                        if error is None
                        else {"passed": False, "problems": [f"error: {error}"]}
                    ),
                }
            )
    return rows


def _med(values):
    values = [v for v in values if v is not None]
    return round(statistics.median(values)) if values else None


def report(rows: list[dict]) -> str:
    out = ["# Research chat bake-off", "", f"{len(rows)} calls.", ""]
    models = list(dict.fromkeys((r["model"], r["tag"], r["effort"]) for r in rows))
    head = (
        "| model @ endpoint | pass | answer | partial/conflict | absent | injection "
        "| polish/followup | false refusal | answered-not-refused | refusal+extra "
        "| bad cite "
        "| markdown | truncated | errors | ttft ms (med) | total ms (med) "
        "| out tok (avg) | $ total |"
    )
    out += [head, "|" + "---|" * 18]
    for model, tag, effort in models:
        mine = [
            r
            for r in rows
            if (r["model"], r["tag"], r["effort"]) == (model, tag, effort)
        ]

        def rate(kinds, mine=mine):
            sub = [r for r in mine if r["kind"] in kinds]
            return f"{sum(r['passed'] for r in sub)}/{len(sub)}"

        ok = [r for r in mine if not r["error"]]
        tokens = [r["completion_tokens"] for r in ok if r["completion_tokens"]]
        cost = sum(r["cost_usd"] or 0 for r in mine)
        cells = [
            f"{model} @ {tag} ({effort or '-'})",
            rate({r["kind"] for r in mine}),
            rate({"answer"}),
            rate({"partial", "conflict"}),
            rate({"absent"}),
            rate({"injection"}),
            rate({"polish", "followup"}),
            sum(1 for r in ok if r["refused"] and "false refusal" in r["problems"]),
            sum(1 for r in ok if "answered instead of refusing" in r["problems"]),
            sum(1 for r in ok if "refusal plus extra text" in r["problems"]),
            sum(1 for r in ok if r["bad_cites"]),
            sum(1 for r in ok if r["markdown"]),
            sum(1 for r in ok if r["truncated"]),
            sum(1 for r in mine if r["error"]),
            _med(r["ttft_ms"] for r in ok),
            _med(r["duration_ms"] for r in ok),
            round(sum(tokens) / len(tokens)) if tokens else None,
            f"{cost:.4f}",
        ]
        out.append("| " + " | ".join(str(c) for c in cells) + " |")
    out += ["", "## Failures", ""]
    for r in rows:
        if not r["passed"]:
            out.append(f"- `{r['model']}` **{r['case']}** #{r['rep']}: {r['problems']}")
    out += ["", "## Replies", ""]
    for case in CASES:
        mine = [r for r in rows if r["case"] == case.id]
        if not mine:
            continue
        out += [f"### {case.id} ({case.kind}): {case.question}", ""]
        for r in mine:
            mark = "ok" if r["passed"] else "FAIL"
            out.append(
                f"- `{r['model']}` #{r['rep']} [{mark}] {r['reply'] or r['error']!r}"
            )
        out.append("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "candidates", nargs="+", help="model@endpoint-tag[@reasoning-effort|none]"
    )
    parser.add_argument("--env", required=True, help=".env holding OPEN_ROUTER_API_KEY")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--reps", type=int, default=2)
    parser.add_argument("--only", help="comma-separated case ids")
    parser.add_argument("--max-tokens", type=int, default=700)
    args = parser.parse_args()

    key = dotenv_values(args.env).get("OPEN_ROUTER_API_KEY")
    if not key:
        raise SystemExit(f"OPEN_ROUTER_API_KEY is empty in {args.env}")
    listed = {
        (e["model_id"], e["tag"])
        for e in httpx.get(ZDR_LIST, timeout=30).json()["data"]
    }
    cases = [c for c in CASES if not args.only or c.id in args.only.split(",")]
    wanted = []
    for spec in args.candidates:
        model, tag, *effort = spec.split("@")
        if (model, tag) not in listed:
            print(f"skip {spec}: not on the live ZDR list")
            continue
        level = effort[0] if effort else "low"
        wanted.append((model, tag, None if level == "none" else level))

    with ThreadPoolExecutor(len(wanted)) as pool:
        futures = [
            pool.submit(run_candidate, key, m, t, e, args.reps, cases, args.max_tokens)
            for m, t, e in wanted
        ]
        rows = [row for future in futures for row in future.result()]

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    )
    (args.out / "report.md").write_text(report(rows))
    print(report(rows).split("## Failures")[0])


if __name__ == "__main__":
    main()
