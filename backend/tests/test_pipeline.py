"""Real PDF/FAISS/chain wiring with deterministic local model substitutes."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake import FakeListLLM


class LocalEmbeddings(Embeddings):
    # A constant vector intentionally tests storage/wiring, not retrieval quality.
    def embed_documents(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [1.0, 0.0, 0.0]


class PipelineBaselineTests(unittest.TestCase):
    def test_synthetic_pdf_ingest_query_and_cold_cache_reload(self):
        backend = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location("baseline_pipeline", backend / "rag_pipeline.py")
        pipeline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pipeline)
        with tempfile.TemporaryDirectory(prefix="financial-rag-index-") as directory:
            pipeline.VECTOR_DIR = directory
            pipeline.VECTOR_INDEX = str(Path(directory) / "index.faiss")
            pipeline.embeddings = LocalEmbeddings()
            pipeline.llm = FakeListLLM(responses=["USD 120 million."])
            self.assertFalse(pipeline.get_status())
            result = pipeline.ingest_pdf(str(backend / "tests/fixtures/synthetic-financial.pdf"))
            self.assertEqual(result["status"], "ingested")
            self.assertEqual(result["file"], "synthetic-financial.pdf")
            self.assertGreater(result["chunks"], 0)
            self.assertEqual(pipeline.ask_rag("FY2025 revenue?"), "USD 120 million.")
            pipeline._vectorstore = None
            self.assertTrue(pipeline.get_status())
            documents = pipeline._vectorstore.similarity_search("FY2025 revenue?", k=1)
            self.assertIn("USD 120 million", documents[0].page_content)
            self.assertEqual(documents[0].metadata["page"], 0)
            self.assertEqual(pipeline.ask_rag("FY2025 revenue?"), "USD 120 million.")


if __name__ == "__main__":
    unittest.main()
