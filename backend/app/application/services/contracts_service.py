from app.application.container import ProviderContainer


class ContractsService:
    def __init__(self, container: ProviderContainer) -> None:
        self._container = container

    def readiness_snapshot(self) -> dict[str, object]:
        parser_mime_types = sorted(self._container.parsers_by_mime.keys())
        return {
            "ready": bool(parser_mime_types),
            "providers": {
                "llm": self._container.llm_provider.provider_name,
                "embedding": self._container.embedding_provider.provider_name,
                "vector_store": self._container.vector_store.provider_name,
                "reranker": self._container.reranker.provider_name,
                "document_access_policy": self._container.document_access_policy.provider_name,
            },
            "supported_document_mime_types": parser_mime_types,
        }
