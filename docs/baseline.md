# Phase 0 baseline and verification

Recorded: 2026-10-19. Application source and production architecture are unchanged.
See [API contract](api-contract.md), [decisions](decision.md),
[flows](flow.md), and [phase status](plan.md).

## Verified environment

- Host: macOS arm64. The preinstalled default Python was 3.13.5.
- Backend verification: isolated CPython 3.11.16 virtual environment at
  `/tmp/financial-rag-baseline-venv`, matching the Docker image's Python 3.11
  minor version. No dependencies were installed into system Python.
- Backend direct dependencies: Flask 3.0.2, Flask-CORS 4.0.0, LangChain 0.2.16,
  langchain-community 0.2.15, pypdf 4.3.1, faiss-cpu 1.8.0,
  python-dotenv 1.0.1. Resolved NumPy: 1.26.4.
- Full installed backend package snapshot: [baseline-python.txt](baseline-python.txt).
  This is observed environment evidence, not a cross-platform dependency lock.
- Node 22.17.0, npm 10.9.2. Project-local install from the tracked
  `frontend/package-lock.json`: React/ReactDOM 18.3.1, Vite 5.4.21,
  plugin-react 4.7.0, Tailwind 3.4.19, PostCSS 8.5.6, Autoprefixer 10.4.24.
- Ollama CLI 0.15.5. CLI emitted an MLX symbol warning and could not contact a
  running server. Server version and installed model digests are unverified.

## Results

- Backend requirements installed successfully in the clean Python 3.11 environment.
- `uv pip check --python /tmp/financial-rag-baseline-venv/bin/python` passed
  for all 51 installed packages. Application and FAISS imports passed.
- `npm ci --ignore-scripts --no-audit --no-fund` passed using a disposable npm
  cache; the tracked lockfile was not changed. `npm run build` passed (33 modules).
  Build reported outdated Browserslist data; no dependency upgrade was made.
- `python -m unittest discover -s backend/tests -v`: **15 tests passed**.
- The fixture's one page and financial text were extracted with the real PDF
  parser. Offline pipeline tests exercised real chunking, FAISS save/load and
  RetrievalQA with deterministic embeddings and a fixed-response fake LLM.
  Cold-cache reload passed; this is not a real-model process-restart result.
- The opt-in smoke invocation without `--run` displayed help and made no model
  calls. Tests verify that missing models or server failures do not start workers.
- `python backend/scripts/smoke_ollama.py --run` exited 1 during server preflight:
  `http://localhost:11434` refused the connection. Retried with local network
  access outside the sandbox to distinguish that result from sandbox denial.
  No model was pulled, no ingest worker ran, and no real answer was measured.

## Reproduce setup

From the repository root, with Python 3.11 installed:

```sh
python3.11 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip check
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

If using uv instead, the verification session used an isolated downloaded runtime:

```sh
UV_CACHE_DIR=/tmp/financial-rag-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/financial-rag-python uv venv --python 3.11 /tmp/financial-rag-baseline-venv
UV_CACHE_DIR=/tmp/financial-rag-uv-cache uv pip install --python /tmp/financial-rag-baseline-venv/bin/python -r backend/requirements.txt
UV_CACHE_DIR=/tmp/financial-rag-uv-cache uv pip check --python /tmp/financial-rag-baseline-venv/bin/python
/tmp/financial-rag-baseline-venv/bin/python -m unittest discover -s backend/tests -v
```

From `frontend/`:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run build
npm ls --depth=0
```

The Python snapshot records current resolution; fresh requirements installs can
resolve different transitive versions. Backend locking remains Phase 4 work.
Python 3.13 was not used to verify this older dependency set. The tests use only
standard-library unittest in addition to application dependencies.

## First-run model setup and real integration test

The following commands are explicit manual provisioning steps. They have not
passed in this session; the scripts never execute them automatically.

In one terminal:

```sh
ollama serve
```

In another terminal:

```sh
ollama pull llama3.1
ollama pull nomic-embed-text
ollama list
backend/.venv/bin/python backend/scripts/smoke_ollama.py --run
```

The runner honors `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, and
`OLLAMA_EMBED_MODEL` environment variables. Export overrides explicitly; it does
not read `.env` files. It checks the server version and installed models before
calling the application. Each worker has a 180-second process deadline, adjustable
with `--timeout`. Preflight HTTP requests have five-second timeouts.

The runner copies `app.py` and `rag_pipeline.py` to a temporary directory, posts
the synthetic PDF through the real Flask handler, asks about FY2025 revenue,
then launches a second Python process against the same temporary index. Each
answer must contain the synthetic value `120`; both processes must report a ready
index after querying. Cleanup removes the temporary corpus after success or
failure. Repository uploads/index files are never read or modified by these
workers. The Flask test client exercises HTTP handlers without starting a TCP
server; ingress/browser networking is not tested here.

Successful JSON output records server version, model details/digests, both stage
answers, and dependency versions. A nonzero exit reports a failed prerequisite,
timeout, or assertion. A single synthetic answer proves wiring only, not numeric
accuracy, grounding, financial usefulness, or production readiness.

## Remaining verification gate

Phase 0 tooling is implemented. Real Ollama ingest/chat/process restart and
successful first-run provisioning remain pending until a reachable server has
both configured models. Capture the successful runner output and update
[plan.md](plan.md) before marking those checks complete. Kubernetes, Docker
startup, frontend interaction, security scanning, and financial evaluation are
outside this baseline's completed checks.

## GitHub Actions CI configuration

Added [ci.yml](../.github/workflows/ci.yml) on 2026-10-19. Pushes, pull requests,
and manual dispatches configure two independent Ubuntu 24.04 jobs:

- Python 3.11: install backend requirements, run `pip check`, record installed
  versions, and run the 15-test offline unittest suite.
- Node 22: install from the frontend lockfile with `npm ci --ignore-scripts`,
  record installed versions, and run the Vite production build.

Both jobs have ten-minute timeouts, dependency caching, and read-only repository
access. Checkout credentials are not persisted. New runs cancel older runs for
the same workflow/event/ref. Official checkout/setup actions are pinned to
commit hashes verified against their v7 tags. No project secrets, Ollama server,
model downloads, or deployment credentials are required.

Local validation passed: actionlint 1.7.7 reported no workflow errors; all 15
backend tests passed again; the frontend production build passed again. These
commands ran on the macOS baseline environment, not the declared Ubuntu runners.
The workflow's first GitHub-hosted execution is pending a push including the
workflow, tests, and synthetic PDF. Backend transitive dependency locking and
successful real-model smoke verification remain pending.

Configuration references: [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[setup-python](https://github.com/actions/setup-python), and
[setup-node](https://github.com/actions/setup-node).
