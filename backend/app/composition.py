"""The only module that names both sides of a port."""

import logging
from dataclasses import dataclass

from fastapi import FastAPI

from app.adapters.auth.deny_all import DenyAllVerifier
from app.adapters.auth.supabase_jwt import SupabaseJwtVerifier
from app.adapters.clock.system import SystemClock
from app.adapters.llm.fake import FakeLLM
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.sqlalchemy.engine import create_session_factory
from app.adapters.persistence.sqlalchemy.repositories import SqlConversationRepo
from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.config import Settings
from app.entrypoints.http.app import create_http_app
from app.ports.auth import TokenVerifier
from app.ports.clock import Clock
from app.ports.llm import LLMProvider
from app.ports.repositories import ConversationRepo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UseCases:
    start_conversation: StartConversation
    run_turn: RunAssistantTurn
    list_messages: ListMessages
    token_verifier: TokenVerifier


def _conversation_repo(settings: Settings) -> ConversationRepo:
    if settings.database_url is None:
        logger.warning("DATABASE_URL is not set; conversations are kept in memory.")
        return InMemoryConversationRepo()
    return SqlConversationRepo(create_session_factory(settings.database_url))


def _token_verifier(settings: Settings) -> TokenVerifier:
    if not settings.supabase_url:
        logger.error("SUPABASE_URL is not set; authenticated routes will return 401.")
        return DenyAllVerifier()
    return SupabaseJwtVerifier(settings.supabase_url)


def build_use_cases(
    *,
    repo: ConversationRepo | None = None,
    llm: LLMProvider | None = None,
    clock: Clock | None = None,
    verifier: TokenVerifier | None = None,
) -> UseCases:
    settings = Settings()
    conversations = repo or _conversation_repo(settings)
    provider = llm or FakeLLM()
    time = clock or SystemClock()
    return UseCases(
        start_conversation=StartConversation(conversations, time),
        run_turn=RunAssistantTurn(conversations, provider, time),
        list_messages=ListMessages(conversations),
        token_verifier=verifier or _token_verifier(settings),
    )


def build_app(use_cases: UseCases | None = None) -> FastAPI:
    cases = use_cases or build_use_cases()
    app = create_http_app(api_docs=Settings().enable_api_docs)
    app.state.start_conversation = cases.start_conversation
    app.state.run_turn = cases.run_turn
    app.state.list_messages = cases.list_messages
    app.state.token_verifier = cases.token_verifier
    return app
