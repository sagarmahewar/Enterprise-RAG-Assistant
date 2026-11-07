from dataclasses import dataclass
from functools import lru_cache

from app.core.settings import Settings, settings
from app.domain.contracts import (
    DocumentAccessPolicy,
    DocumentParser,
    EmbeddingProvider,
    LLMProvider,
    Reranker,
    VectorStore,
)
from app.infrastructure.providers.fake import (
    FakeEmbeddingProvider,
    FakeLLMProvider,
    FakeReranker,
    FakeVectorStore,
)
from app.infrastructure.providers.groq import GroqEmbeddingProvider, GroqLLMProvider
from app.infrastructure.providers.ollama import OllamaEmbeddingProvider, OllamaLLMProvider
from app.infrastructure.providers.openai import OpenAIEmbeddingProvider
from app.infrastructure.providers.parsers import (
    DocxDocumentParser,
    PdfDocumentParser,
    TextDocumentParser,
)
from app.infrastructure.providers.qdrant import QdrantVectorStore
from app.infrastructure.providers.security import (
    AllowAllDocumentAccessPolicy,
    HeaderAllowlistDocumentAccessPolicy,
)


@dataclass(frozen=True)
class ProviderContainer:
    llm_provider: LLMProvider
    embedding_provider: EmbeddingProvider
    vector_store: VectorStore
    reranker: Reranker
    document_access_policy: DocumentAccessPolicy
    parsers_by_mime: dict[str, DocumentParser]

    def parser_for_mime(self, mime_type: str) -> DocumentParser | None:
        return self.parsers_by_mime.get(mime_type)


def _build_parser_registry(parsers: list[DocumentParser]) -> dict[str, DocumentParser]:
    registry: dict[str, DocumentParser] = {}
    for parser in parsers:
        for mime_type in parser.supported_mime_types():
            registry[mime_type] = parser
    return registry


def _build_llm_provider(current_settings: Settings) -> LLMProvider:
    if current_settings.llm_provider_backend == "ollama":
        return OllamaLLMProvider(
            base_url=current_settings.ollama_base_url,
            model_name=current_settings.ollama_llm_model,
            timeout_seconds=current_settings.ollama_request_timeout_seconds,
        )
    if current_settings.llm_provider_backend == "local-fake-llm":
        return FakeLLMProvider(provider_name=current_settings.llm_provider_backend)
    if current_settings.llm_provider_backend == "groq":
        if not current_settings.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set when LLM_PROVIDER_BACKEND=groq")
        return GroqLLMProvider(
            base_url=current_settings.groq_base_url,
            api_key=current_settings.groq_api_key,
            model_name=current_settings.groq_llm_model,
            timeout_seconds=current_settings.groq_request_timeout_seconds,
            temperature=current_settings.groq_temperature,
            max_tokens=current_settings.groq_max_tokens,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER_BACKEND: {current_settings.llm_provider_backend}")


def _build_embedding_provider(current_settings: Settings) -> EmbeddingProvider:
    if current_settings.embedding_provider_backend == "ollama":
        return OllamaEmbeddingProvider(
            base_url=current_settings.ollama_base_url,
            model_name=current_settings.ollama_embedding_model,
            timeout_seconds=current_settings.ollama_request_timeout_seconds,
        )
    if current_settings.embedding_provider_backend == "local-fake-embeddings":
        return FakeEmbeddingProvider(provider_name=current_settings.embedding_provider_backend)
    if current_settings.embedding_provider_backend == "groq":
        if not current_settings.groq_api_key:
            raise ValueError("GROQ_API_KEY must be set when EMBEDDING_PROVIDER_BACKEND=groq")
        return GroqEmbeddingProvider(
            base_url=current_settings.groq_base_url,
            api_key=current_settings.groq_api_key,
            model_name=current_settings.groq_embedding_model,
            timeout_seconds=current_settings.groq_request_timeout_seconds,
        )
    if current_settings.embedding_provider_backend == "openai":
        if not current_settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set when EMBEDDING_PROVIDER_BACKEND=openai")
        return OpenAIEmbeddingProvider(
            base_url=current_settings.openai_base_url,
            api_key=current_settings.openai_api_key,
            model_name=current_settings.openai_embedding_model,
            timeout_seconds=current_settings.openai_request_timeout_seconds,
        )
    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER_BACKEND: {current_settings.embedding_provider_backend}"
    )


def _build_vector_store(current_settings: Settings) -> VectorStore:
    if current_settings.vector_store_backend == "local-fake-vector-store":
        return FakeVectorStore(provider_name=current_settings.vector_store_backend)
    if current_settings.vector_store_backend == "qdrant":
        return QdrantVectorStore(
            base_url=current_settings.qdrant_url,
            api_key=current_settings.qdrant_api_key or None,
            collection_name=current_settings.qdrant_collection_name,
            timeout_seconds=current_settings.qdrant_timeout_seconds,
        )
    raise ValueError(f"Unsupported VECTOR_STORE_BACKEND: {current_settings.vector_store_backend}")


def _build_reranker(current_settings: Settings) -> Reranker:
    if current_settings.reranker_backend == "local-fake-reranker":
        return FakeReranker(provider_name=current_settings.reranker_backend)
    raise ValueError(f"Unsupported RERANKER_BACKEND: {current_settings.reranker_backend}")


def _build_document_access_policy(current_settings: Settings) -> DocumentAccessPolicy:
    if current_settings.document_access_policy_backend == "allow-all":
        return AllowAllDocumentAccessPolicy()
    if current_settings.document_access_policy_backend == "header-allowlist":
        return HeaderAllowlistDocumentAccessPolicy()
    raise ValueError(
        "Unsupported DOCUMENT_ACCESS_POLICY_BACKEND: "
        f"{current_settings.document_access_policy_backend}"
    )


def build_container(current_settings: Settings) -> ProviderContainer:
    llm_provider = _build_llm_provider(current_settings)
    embedding_provider = _build_embedding_provider(current_settings)
    vector_store = _build_vector_store(current_settings)
    reranker = _build_reranker(current_settings)
    document_access_policy = _build_document_access_policy(current_settings)
    parser_registry = _build_parser_registry(
        [
            TextDocumentParser(),
            DocxDocumentParser(),
            PdfDocumentParser(),
        ]
    )

    return ProviderContainer(
        llm_provider=llm_provider,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        reranker=reranker,
        document_access_policy=document_access_policy,
        parsers_by_mime=parser_registry,
    )


@lru_cache(maxsize=1)
def get_container() -> ProviderContainer:
    return build_container(settings)
