"""The only module that names both sides of a port."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from app.adapters.auth.deny_all import DenyAllVerifier
from app.adapters.auth.supabase_jwt import SupabaseJwtVerifier
from app.adapters.clock.system import SystemClock
from app.adapters.extraction import FileExtractor, TesseractOcr
from app.adapters.files import LocalDiskFileStore
from app.adapters.llm.fake import FakeLLM
from app.adapters.llm.fake_embedder import FakeEmbedder
from app.adapters.llm.openrouter import OpenRouterChat
from app.adapters.llm.openrouter_embedder import OpenRouterEmbedder
from app.adapters.persistence.memory.campaigns import InMemoryCampaignRepo
from app.adapters.persistence.memory.chunk_search import InMemoryChunkSearch
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.adapters.persistence.sqlalchemy.embedding_space import check_embedding_space
from app.adapters.persistence.sqlalchemy.engine import create_session_factory
from app.adapters.persistence.sqlalchemy.repositories import (
    SqlCampaignRepo,
    SqlChunkSearch,
    SqlConversationRepo,
    SqlDocumentRepo,
)
from app.application.assistant import (
    ListConversations,
    ListMessages,
    RunAssistantTurn,
    StartConversation,
)
from app.application.campaigns import (
    CreateCampaign,
    GetCampaign,
    GetCampaignImage,
    ListCampaigns,
    ListSystems,
    SetCampaignImage,
)
from app.application.documents import (
    DeleteDocument,
    GetDocument,
    IngestDocument,
    ListDocuments,
    UploadDocument,
)
from app.config import Settings
from app.entrypoints.http.app import create_http_app
from app.entrypoints.worker import IngestionWorker
from app.ports.auth import TokenVerifier
from app.ports.clock import Clock
from app.ports.embeddings import Embedder
from app.ports.extraction import TextExtractor
from app.ports.files import FileStore
from app.ports.llm import LLMProvider
from app.ports.repositories import CampaignRepo, ConversationRepo, DocumentRepo
from app.ports.search import ChunkSearch

logger = logging.getLogger(__name__)

# A banner is shown at card size; nothing needs more than this.
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class UseCases:
    list_systems: ListSystems
    list_campaigns: ListCampaigns
    create_campaign: CreateCampaign
    get_campaign: GetCampaign
    set_campaign_image: SetCampaignImage
    get_campaign_image: GetCampaignImage
    start_conversation: StartConversation
    run_turn: RunAssistantTurn
    list_conversations: ListConversations
    list_messages: ListMessages
    upload_document: UploadDocument
    list_documents: ListDocuments
    get_document: GetDocument
    delete_document: DeleteDocument
    # None when nothing could embed real vectors: uploads then stay queued (#64).
    worker: IngestionWorker | None
    chunk_search: ChunkSearch
    token_verifier: TokenVerifier


# A sqlalchemy sessionmaker; typed Any so sqlalchemy is imported only by its adapter.
def _sessions(settings: Settings) -> Any | None:
    if settings.database_url is None:
        logger.warning(
            "DATABASE_URL is not set; campaigns, conversations and documents are kept "
            "in memory."
        )
        return None
    return create_session_factory(settings.database_url)


def _token_verifier(settings: Settings) -> TokenVerifier:
    if not settings.supabase_url:
        logger.error("SUPABASE_URL is not set; authenticated routes will return 401.")
        return DenyAllVerifier()
    return SupabaseJwtVerifier(settings.supabase_url)


def _embedder(settings: Settings, *, persistent: bool) -> Embedder | None:
    if settings.open_router_api_key:
        return OpenRouterEmbedder(
            api_key=settings.open_router_api_key,
            model=settings.embedding_model,
            provider=settings.embedding_provider,
        )
    if persistent:
        # Fake vectors in a real store would be unsearchable noise that no re-embed
        # could find; better that uploads wait until the key is back.
        logger.error(
            "OPEN_ROUTER_API_KEY is not set; ingestion is off and uploads stay queued."
        )
        return None
    logger.warning("OPEN_ROUTER_API_KEY is not set; embeddings are fake (in memory).")
    # Labelled "fake", never as the real model.
    return FakeEmbedder()


def _llm(settings: Settings) -> LLMProvider:
    if settings.open_router_api_key:
        return OpenRouterChat(
            api_key=settings.open_router_api_key,
            model=settings.chat_model,
            provider=settings.chat_provider,
            max_tokens=settings.chat_max_tokens,
        )
    logger.warning("OPEN_ROUTER_API_KEY is not set; the assistant is a fake model.")
    return FakeLLM()


def _extractor(settings: Settings) -> TextExtractor:
    if not TesseractOcr.available():
        logger.warning(
            "tesseract is not installed; scanned PDFs will wait in awaiting_ocr."
        )
        return FileExtractor(ocr=None)
    return FileExtractor(ocr=TesseractOcr(settings.ocr_languages))


def build_use_cases(
    *,
    repo: ConversationRepo | None = None,
    llm: LLMProvider | None = None,
    clock: Clock | None = None,
    verifier: TokenVerifier | None = None,
    documents: DocumentRepo | None = None,
    files: FileStore | None = None,
    embedder: Embedder | None = None,
    extractor: TextExtractor | None = None,
    campaigns: CampaignRepo | None = None,
) -> UseCases:
    settings = Settings()
    # One engine and pool shared by every SQL repository.
    sessions = None if repo and documents and campaigns else _sessions(settings)
    campaign_repo: CampaignRepo = campaigns or (
        InMemoryCampaignRepo() if sessions is None else SqlCampaignRepo(sessions)
    )
    conversations: ConversationRepo = repo or (
        InMemoryConversationRepo()
        if sessions is None
        else SqlConversationRepo(sessions)
    )
    document_repo: DocumentRepo = documents or (
        InMemoryDocumentRepo() if sessions is None else SqlDocumentRepo(sessions)
    )
    store: FileStore = files or LocalDiskFileStore(Path(settings.file_store_path))
    provider = llm or _llm(settings)
    embed = embedder or _embedder(settings, persistent=sessions is not None)
    if sessions is not None and embed is not None:
        check_embedding_space(sessions, embed.model, embed.dimensions)
    search: ChunkSearch = (
        SqlChunkSearch(sessions, settings.retrieval_floor)
        if sessions is not None
        else InMemoryChunkSearch(document_repo)
    )
    time = clock or SystemClock()
    return UseCases(
        list_systems=ListSystems(campaign_repo),
        list_campaigns=ListCampaigns(campaign_repo),
        create_campaign=CreateCampaign(campaign_repo, time),
        get_campaign=GetCampaign(campaign_repo),
        set_campaign_image=SetCampaignImage(
            store, campaign_repo, max_bytes=MAX_IMAGE_BYTES
        ),
        get_campaign_image=GetCampaignImage(store, campaign_repo),
        start_conversation=StartConversation(conversations, time),
        list_conversations=ListConversations(conversations),
        run_turn=RunAssistantTurn(
            conversations,
            provider,
            time,
            search,
            embed,
            top_k=settings.retrieval_top_k,
            history_messages=settings.history_messages,
        ),
        list_messages=ListMessages(conversations),
        upload_document=UploadDocument(
            store,
            document_repo,
            time,
            max_bytes=settings.max_upload_mb * 1024 * 1024,
        ),
        list_documents=ListDocuments(document_repo),
        get_document=GetDocument(document_repo),
        delete_document=DeleteDocument(store, document_repo),
        worker=None
        if embed is None
        else IngestionWorker(
            IngestDocument(
                store, document_repo, extractor or _extractor(settings), embed
            ),
            document_repo,
        ),
        chunk_search=search,
        token_verifier=verifier or _token_verifier(settings),
    )


def build_app(use_cases: UseCases | None = None) -> FastAPI:
    """The served app. The ingestion worker runs only on this path, the one uvicorn
    takes (no use cases passed in) — never in tests that hand in their own."""
    settings = Settings()
    cases = use_cases or build_use_cases()
    worker = cases.worker if use_cases is None and settings.ingestion_worker else None

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if worker is not None:
            worker.start()
        yield
        if worker is not None:
            worker.stop()

    app = create_http_app(api_docs=settings.enable_api_docs, lifespan=lifespan)
    app.state.list_systems = cases.list_systems
    app.state.list_campaigns = cases.list_campaigns
    app.state.create_campaign = cases.create_campaign
    app.state.get_campaign = cases.get_campaign
    app.state.set_campaign_image = cases.set_campaign_image
    app.state.get_campaign_image = cases.get_campaign_image
    app.state.start_conversation = cases.start_conversation
    app.state.run_turn = cases.run_turn
    app.state.list_conversations = cases.list_conversations
    app.state.list_messages = cases.list_messages
    app.state.upload_document = cases.upload_document
    app.state.list_documents = cases.list_documents
    app.state.get_document = cases.get_document
    app.state.delete_document = cases.delete_document
    app.state.token_verifier = cases.token_verifier
    return app
