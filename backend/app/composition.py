"""The only module that names both sides of a port."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from app.adapters.auth.deny_all import DenyAllVerifier
from app.adapters.auth.supabase_jwt import SupabaseJwtVerifier
from app.adapters.clock.system import SystemClock
from app.adapters.files import LocalDiskFileStore
from app.adapters.llm.fake import FakeLLM
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.adapters.persistence.sqlalchemy.engine import create_session_factory
from app.adapters.persistence.sqlalchemy.repositories import (
    SqlConversationRepo,
    SqlDocumentRepo,
)
from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.application.documents import GetDocument, ListDocuments, UploadDocument
from app.config import Settings
from app.entrypoints.http.app import create_http_app
from app.ports.auth import TokenVerifier
from app.ports.clock import Clock
from app.ports.files import FileStore
from app.ports.llm import LLMProvider
from app.ports.repositories import ConversationRepo, DocumentRepo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UseCases:
    start_conversation: StartConversation
    run_turn: RunAssistantTurn
    list_messages: ListMessages
    upload_document: UploadDocument
    list_documents: ListDocuments
    get_document: GetDocument
    token_verifier: TokenVerifier


# A sqlalchemy sessionmaker; typed Any so sqlalchemy is imported only by its adapter.
def _sessions(settings: Settings) -> Any | None:
    if settings.database_url is None:
        logger.warning(
            "DATABASE_URL is not set; conversations and documents are kept in memory."
        )
        return None
    return create_session_factory(settings.database_url)


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
    documents: DocumentRepo | None = None,
    files: FileStore | None = None,
) -> UseCases:
    settings = Settings()
    # One engine and pool shared by every SQL repository.
    sessions = None if repo and documents else _sessions(settings)
    conversations: ConversationRepo = repo or (
        InMemoryConversationRepo()
        if sessions is None
        else SqlConversationRepo(sessions)
    )
    document_repo: DocumentRepo = documents or (
        InMemoryDocumentRepo() if sessions is None else SqlDocumentRepo(sessions)
    )
    store: FileStore = files or LocalDiskFileStore(Path(settings.file_store_path))
    provider = llm or FakeLLM()
    time = clock or SystemClock()
    return UseCases(
        start_conversation=StartConversation(conversations, time),
        run_turn=RunAssistantTurn(conversations, provider, time),
        list_messages=ListMessages(conversations),
        upload_document=UploadDocument(
            store,
            document_repo,
            time,
            max_bytes=settings.max_upload_mb * 1024 * 1024,
        ),
        list_documents=ListDocuments(document_repo),
        get_document=GetDocument(document_repo),
        token_verifier=verifier or _token_verifier(settings),
    )


def build_app(use_cases: UseCases | None = None) -> FastAPI:
    cases = use_cases or build_use_cases()
    app = create_http_app(api_docs=Settings().enable_api_docs)
    app.state.start_conversation = cases.start_conversation
    app.state.run_turn = cases.run_turn
    app.state.list_messages = cases.list_messages
    app.state.upload_document = cases.upload_document
    app.state.list_documents = cases.list_documents
    app.state.get_document = cases.get_document
    app.state.token_verifier = cases.token_verifier
    return app
