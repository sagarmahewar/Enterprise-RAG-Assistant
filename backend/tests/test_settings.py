import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_defaults(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            actual = Settings.from_env()
        self.assertEqual(actual.app_name, "Enterprise RAG Assistant API")
        self.assertEqual(actual.app_env, "development")
        self.assertEqual(actual.api_v1_prefix, "/api/v1")
        self.assertEqual(actual.cors_origins, ("http://localhost:5173",))
        self.assertEqual(actual.llm_provider_backend, "ollama")
        self.assertEqual(actual.embedding_provider_backend, "ollama")
        self.assertEqual(actual.vector_store_backend, "local-fake-vector-store")
        self.assertEqual(actual.reranker_backend, "local-fake-reranker")
        self.assertEqual(actual.document_access_policy_backend, "allow-all")
        self.assertEqual(actual.ollama_base_url, "http://localhost:11434")
        self.assertEqual(actual.ollama_llm_model, "qwen2.5:14b")
        self.assertEqual(actual.ollama_embedding_model, "nomic-embed-text")
        self.assertEqual(actual.ollama_request_timeout_seconds, 90)
        self.assertEqual(actual.groq_base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(actual.groq_api_key, "")
        self.assertEqual(actual.groq_llm_model, "llama-3.1-8b-instant")
        self.assertEqual(actual.groq_embedding_model, "nomic-embed-text-v1.5")
        self.assertEqual(actual.groq_temperature, 0.1)
        self.assertEqual(actual.groq_max_tokens, 1024)
        self.assertEqual(actual.groq_request_timeout_seconds, 60)
        self.assertEqual(actual.qdrant_url, "http://localhost:6333")
        self.assertEqual(actual.qdrant_api_key, "")
        self.assertEqual(actual.qdrant_collection_name, "rag_chunks_local")
        self.assertEqual(actual.qdrant_timeout_seconds, 30)
        self.assertEqual(actual.metadata_db_path, Path("data/metadata.db"))
        self.assertEqual(actual.upload_dir, Path("data/uploads"))
        self.assertEqual(actual.max_upload_size_bytes, 10485760)
        self.assertEqual(actual.chunk_size_chars, 1200)
        self.assertEqual(actual.chunk_overlap_chars, 200)
        self.assertEqual(actual.retrieval_semantic_top_k, 12)
        self.assertEqual(actual.retrieval_lexical_top_k, 12)
        self.assertEqual(actual.retrieval_final_top_k, 6)
        self.assertEqual(actual.retrieval_semantic_weight, 0.6)
        self.assertEqual(actual.retrieval_lexical_weight, 0.4)
        self.assertEqual(actual.retrieval_min_citation_confidence_score, 0.35)
        self.assertEqual(actual.qa_min_context_chunks, 1)
        self.assertEqual(actual.qa_min_fused_score, 0.05)

    def test_csv_cors_parsing(self) -> None:
        with patch.dict(
            os.environ,
            {"CORS_ORIGINS": "http://localhost:5173, https://sagarmahewar.github.io"},
            clear=True,
        ):
            actual = Settings.from_env()
        self.assertEqual(
            actual.cors_origins,
            ("http://localhost:5173", "https://sagarmahewar.github.io"),
        )

    def test_invalid_ollama_timeout_raises(self) -> None:
        with patch.dict(
            os.environ,
            {"OLLAMA_REQUEST_TIMEOUT_SECONDS": "0"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_invalid_groq_temperature_raises(self) -> None:
        with patch.dict(
            os.environ,
            {"GROQ_TEMPERATURE": "2.1"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_invalid_chunk_overlap_raises(self) -> None:
        with patch.dict(
            os.environ,
            {
                "CHUNK_SIZE_CHARS": "100",
                "CHUNK_OVERLAP_CHARS": "100",
            },
            clear=True,
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_invalid_retrieval_weight_sum_raises(self) -> None:
        with patch.dict(
            os.environ,
            {
                "RETRIEVAL_SEMANTIC_WEIGHT": "0",
                "RETRIEVAL_LEXICAL_WEIGHT": "0",
            },
            clear=True,
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_invalid_qa_min_fused_score_range_raises(self) -> None:
        with patch.dict(
            os.environ,
            {
                "QA_MIN_FUSED_SCORE": "1.2",
            },
            clear=True,
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()

    def test_invalid_retrieval_citation_confidence_range_raises(self) -> None:
        with patch.dict(
            os.environ,
            {
                "RETRIEVAL_MIN_CITATION_CONFIDENCE_SCORE": "1.4",
            },
            clear=True,
        ):
            with self.assertRaises(ValueError):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
