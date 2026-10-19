"""Baseline HTTP contracts. No LangChain imports, network calls, or real corpus writes."""

import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class APIContractTests(unittest.TestCase):
    def setUp(self):
        pipeline = types.ModuleType("rag_pipeline")
        pipeline.ingest_pdf = Mock()
        pipeline.ask_rag = Mock(return_value="Synthetic answer")
        pipeline.get_status = Mock(return_value=False)
        spec = importlib.util.spec_from_file_location(
            "baseline_app", Path(__file__).resolve().parents[1] / "app.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"rag_pipeline": pipeline}):
            spec.loader.exec_module(self.module)
        self.pipeline = pipeline
        temporary = tempfile.TemporaryDirectory(prefix="financial-rag-api-")
        self.addCleanup(temporary.cleanup)
        self.module.UPLOAD_DIR = temporary.name
        self.module.app.config.update(TESTING=True)
        self.client = self.module.app.test_client()

    def test_health_reports_empty_and_ready_states(self):
        for ready in (False, True):
            with self.subTest(ready=ready):
                self.pipeline.get_status.return_value = ready
                response = self.client.get("/health")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json, {"status": "ok", "vectorstore_ready": ready})

    def test_ingest_missing_file(self):
        response = self.client.post("/ingest")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "No file part"})
        self.pipeline.ingest_pdf.assert_not_called()

    def test_ingest_empty_filename(self):
        response = self.client.post(
            "/ingest", data={"file": (io.BytesIO(b""), "")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Empty filename"})
        self.pipeline.ingest_pdf.assert_not_called()

    def test_ingest_saves_fixture_and_returns_pipeline_result(self):
        fixture = Path(__file__).parent / "fixtures" / "synthetic-financial.pdf"
        result = {"status": "ingested", "chunks": 1, "file": fixture.name}
        self.pipeline.ingest_pdf.return_value = result
        with fixture.open("rb") as source:
            response = self.client.post("/ingest", data={"file": (source, fixture.name)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, result)
        saved = Path(self.module.UPLOAD_DIR) / fixture.name
        self.assertEqual(saved.read_bytes(), fixture.read_bytes())
        self.pipeline.ingest_pdf.assert_called_once_with(str(saved))

    def test_chat_trims_query_and_returns_answer(self):
        response = self.client.post("/chat", json={"query": "  revenue?  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"answer": "Synthetic answer"})
        self.pipeline.ask_rag.assert_called_once_with("revenue?")

    def test_chat_missing_or_blank_query(self):
        for payload in ({}, {"query": ""}, {"query": " \n "}):
            with self.subTest(payload=payload):
                response = self.client.post("/chat", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json, {"error": "Missing query"})
        self.pipeline.ask_rag.assert_not_called()

    def test_chat_invalid_json(self):
        response = self.client.post("/chat", data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "Missing query"})

    def test_chat_empty_index_error(self):
        message = "Vector store is empty. Ingest a PDF first."
        self.pipeline.ask_rag.side_effect = ValueError(message)
        response = self.client.post("/chat", json={"query": "Revenue?"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": message})

    def test_chat_wrong_types_currently_return_500(self):
        # Characterization only: Phase 1 should change this to a 4xx contract.
        self.module.app.config["TESTING"] = False
        with patch.object(self.module.app.logger, "error"):
            for payload in ({"query": 123}, {"query": None}, ["query"]):
                with self.subTest(payload=payload):
                    response = self.client.post("/chat", json=payload)
                    self.assertEqual(response.status_code, 500)
                    self.assertEqual(response.mimetype, "text/html")
        self.pipeline.ask_rag.assert_not_called()

    def test_ingest_parser_failure_currently_returns_500(self):
        self.module.app.config["TESTING"] = False
        self.pipeline.ingest_pdf.side_effect = RuntimeError("synthetic parser failure")
        with patch.object(self.module.app.logger, "error"):
            response = self.client.post(
                "/ingest", data={"file": (io.BytesIO(b"not a PDF"), "invalid.pdf")}
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "text/html")

    def test_model_failure_currently_returns_500(self):
        self.module.app.config["TESTING"] = False
        self.pipeline.ask_rag.side_effect = RuntimeError("synthetic model failure")
        with patch.object(self.module.app.logger, "error"):
            response = self.client.post("/chat", json={"query": "Revenue?"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "text/html")


if __name__ == "__main__":
    unittest.main()
