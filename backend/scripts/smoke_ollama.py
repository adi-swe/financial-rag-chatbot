"""Explicit real-model ingest/chat/restart smoke test. Never pulls models.

Run from the repository root with the backend virtual environment:
    python backend/scripts/smoke_ollama.py --run
"""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen

BACKEND = Path(__file__).resolve().parents[1]
QUERY = "What was Example Holdings revenue in FY2025? State the number in digits and the units."


def worker(stage, sandbox):
    # Only our two copied application modules are imported, so their __file__
    # based upload/index paths resolve inside this disposable directory.
    sys.path.insert(0, str(sandbox))
    from app import app

    app.config.update(TESTING=True)
    client = app.test_client()
    initial = client.get("/health")
    assert initial.status_code == 200, initial.status_code
    assert initial.json["vectorstore_ready"] == (stage == "reload"), initial.json
    if stage == "ingest":
        fixture = BACKEND / "tests" / "fixtures" / "synthetic-financial.pdf"
        with fixture.open("rb") as source:
            response = client.post("/ingest", data={"file": (source, fixture.name)})
        assert response.status_code == 200, (response.status_code, response.get_data(as_text=True))
        assert response.json["chunks"] > 0, response.json
        assert response.json["status"] == "ingested", response.json
        assert (sandbox / "vectorstore" / "index.faiss").is_file()
        assert (sandbox / "vectorstore" / "index.pkl").is_file()
    response = client.post("/chat", json={"query": QUERY})
    assert response.status_code == 200, (response.status_code, response.get_data(as_text=True))
    answer = response.json.get("answer", "")
    assert isinstance(answer, str) and answer.strip(), response.json
    assert "120" in answer, f"Expected synthetic revenue 120 in answer: {answer!r}"
    assert client.get("/health").json["vectorstore_ready"] is True
    print(json.dumps({"stage": stage, "answer": answer, "status": "passed"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Allow calls to configured Ollama; no model downloads")
    parser.add_argument("--timeout", type=int, default=180, help="Maximum seconds per application process")
    parser.add_argument("--worker", choices=("ingest", "reload"), help=argparse.SUPPRESS)
    parser.add_argument("--sandbox", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return 0
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if args.worker:
        if not args.sandbox:
            parser.error("internal worker requires --sandbox")
        worker(args.worker, args.sandbox)
        return 0

    report = {"python": platform.python_version(), "platform": platform.platform(), "status": "failed"}
    try:
        report["dependencies"] = {
            package: importlib.metadata.version(package)
            for package in ("flask", "langchain", "langchain-community", "pypdf", "faiss-cpu", "numpy", "requests")
        }
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        report["ollama_url"] = base
        with urlopen(base + "/api/version", timeout=5) as response:
            report["ollama_server"] = json.load(response)["version"]
        with urlopen(base + "/api/tags", timeout=5) as response:
            available = json.load(response)["models"]
        models = [os.getenv("OLLAMA_CHAT_MODEL", "llama3.1"), os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")]
        report["required_models"] = models
        canonical = lambda name: name if ":" in name.rsplit("/", 1)[-1] else name + ":latest"
        available_names = {canonical(model["name"]) for model in available}
        missing = [name for name in models if canonical(name) not in available_names]
        if missing:
            raise RuntimeError("Missing models; explicitly provision them before retrying: " + ", ".join(missing))
        report["models"] = [model for model in available if canonical(model["name"]) in {canonical(name) for name in models}]
        report["stages"] = []
        with tempfile.TemporaryDirectory(prefix="financial-rag-smoke-") as directory:
            sandbox = Path(directory)
            for name in ("app.py", "rag_pipeline.py"):
                shutil.copyfile(BACKEND / name, sandbox / name)
            for stage in ("ingest", "reload"):
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--run", "--worker", stage, "--sandbox", directory],
                    capture_output=True, text=True, timeout=args.timeout,
                )
                if result.returncode:
                    raise RuntimeError(f"{stage} failed:\n{result.stdout}\n{result.stderr}")
                report["stages"].append(json.loads(result.stdout))
        report["status"] = "passed"
    except Exception as exc:
        report["error"] = str(exc)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
