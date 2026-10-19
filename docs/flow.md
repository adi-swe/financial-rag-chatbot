# Application flows

Date: 2026-10-19

This document distinguishes implemented behavior from planned behavior.
See [decisions](decision.md) and [delivery plan](plan.md).

## Current implementation

```mermaid
flowchart TD
    User[Browser user] --> UI[React interface]
    UI -->|PDF multipart upload| Ingest[Flask POST /ingest]
    Ingest -->|Client-supplied filename| Uploads[Local upload directory]
    Uploads --> PDF[PyPDFLoader]
    PDF --> Split[Character chunks: 1000 with 150 overlap]
    Split --> Embed[Ollama embeddings]
    Embed --> Index[Process-global FAISS index]
    Index -->|save_local| Disk[Local FAISS files]
    Disk -->|Lazy load with pickle deserialization| Index
    UI -->|Latest query only| Chat[Flask POST /chat]
    Chat --> Retrieve[Retrieve four chunks]
    Index --> Retrieve
    Retrieve --> QA[RetrievalQA stuff chain]
    QA --> Model[Ollama chat model]
    Model --> Answer[Answer string without sources]
    Answer --> UI
```

The browser stores displayed messages in React state. The backend receives no
conversation history. All uploads share the same index. Uploaded PDF presence
does not mean it has been indexed. Health reports index availability, not model
readiness. Compose mounts uploads and index storage; Kubernetes currently does
not. Remote Ollama endpoints are configurable.

## Proposed ingestion flow — not implemented

```mermaid
flowchart TD
    Upload[Upload request] --> Limits[Validate request and resource limits]
    Limits --> Validate[Check PDF and extraction support]
    Validate --> Identity[Generate document ID and content hash]
    Identity --> Duplicate{Already indexed?}
    Duplicate -->|Yes| Existing[Return existing document result]
    Duplicate -->|No| Stage[Stage file under controlled path]
    Stage --> Extract[Extract text and page provenance]
    Extract --> Chunk[Chunk with document metadata]
    Chunk --> Embed[Bounded Ollama embedding request]
    Embed --> Writer[Single index owner]
    Writer --> Snapshot[Write candidate index snapshot]
    Snapshot --> Commit[Commit catalog and active snapshot version]
    Commit --> Ready[Return document ID and index version]
    Limits -->|Rejected| Error[Structured error response]
    Validate -->|Unsupported or invalid| Error
    Extract -->|Failure| Cleanup[Mark failure and clean staging]
    Embed -->|Failure or timeout| Cleanup
    Snapshot -->|Failure| Cleanup
    Cleanup --> Error
```

The commit protocol must specify recovery from interruption between catalog and
snapshot updates. Queries see a committed version. Ingestion failures leave the
previous committed corpus usable. For the first implementation, ingestion stays
synchronous with bounded requests; background jobs are deferred unless measured
processing time requires them.

## Proposed question flow — not implemented

```mermaid
flowchart TD
    Request[Question request] --> Validate[Validate JSON object and bounded query]
    Validate --> Scope[Resolve allowed corpus and document filters]
    Scope --> Snapshot[Read committed index version]
    Snapshot --> Retrieve[Retrieve evidence with page metadata]
    Retrieve --> Evidence{Evidence sufficient?}
    Evidence -->|No| Abstain[Insufficient-evidence response]
    Evidence -->|Yes| Prompt[Build bounded grounded prompt]
    Prompt --> Model[Ollama with timeout]
    Model --> Assemble[Assemble answer and cited sources]
    Assemble --> UI[Render answer with source navigation]
    Abstain --> UI
    Model -->|Failure| Error[Structured service error]
```

Initially, corpus scope is the explicitly local single-user corpus. Shared-host
scope must be derived from authenticated authorization, never a client-supplied
tenant identifier alone. Evidence-sufficiency rules require benchmark validation;
no confidence threshold is claimed to be effective yet.

Conversational query rewriting is a later extension before retrieval. It must
preserve document scope and must not turn previous model answers into evidence.

## Proposed operational boundaries — not implemented

- Browser requests have cancellation and bounded waiting behavior.
- API responses use stable error codes and safe user-facing messages.
- Liveness checks process responsiveness; readiness checks committed storage,
  Ollama connectivity, and required model availability with bounded checks.
- Compose owns local model initialization and persistent mounts.
- Kubernetes uses persistent volumes and a declared model-serving endpoint.
- Logs correlate requests and durations without retaining financial text by
  default. Backup/restore covers uploads, catalog, and index versions together.

## CI verification flow — configured, hosted execution unverified

The [GitHub Actions workflow](../.github/workflows/ci.yml) configures this
verification path. It does not change the application request flows above.

```mermaid
flowchart TD
    Event[Push, pull request, or manual dispatch] --> CI[GitHub Actions CI]
    CI --> Backend[Ubuntu 24.04: Python 3.11]
    CI --> Frontend[Ubuntu 24.04: Node 22]
    Backend --> Pip[Install backend requirements and check compatibility]
    Pip --> Tests[Offline API, FAISS, and smoke-runner tests]
    Frontend --> Npm[Install dependencies from frontend lockfile]
    Npm --> Build[Vite production build]
    Tests --> Checks[GitHub check results]
    Build --> Checks
```

Jobs use disposable hosted runners and dependency download caches. Tests use
synthetic data and temporary corpus storage. CI does not start Ollama, pull
models, publish build artifacts, or deploy containers. Real-model checks remain
an explicitly invoked local verification path.

## Maintenance log

- 2026-10-19: Documented the inspected implementation and separately labeled
  proposed flows. No runtime flow changed. Reviewed against source paths in
  `backend/app.py`, `backend/rag_pipeline.py`, `frontend/src/api.js`, Compose,
  and Kubernetes manifests. Diagram rendering remains to be verified in a
  Mermaid-capable viewer.
- 2026-10-19: Reviewed Phase 0 verification tooling. API tests replace the RAG
  module and redirect uploads to temporary storage. The opt-in smoke runner
  copies the two backend modules to a temporary directory and starts distinct
  ingest and reload processes using real Ollama; it never pulls models. These
  are verification paths, not changes to the application flows above.
- 2026-10-19: Reviewed final Phase 0 changes against the diagrams. Added a real
  PDF/FAISS offline persistence test with fixed model substitutes; this does not
  measure model retrieval quality or real process-restart behavior. The
  [baseline report](baseline.md) records the unavailable real Ollama preflight.
  Runtime diagrams remain unchanged.
- 2026-10-19: Added the configured CI verification flow on GitHub-hosted Ubuntu
  runners. Reviewed current application and planned flows; no runtime component
  or persistence changes. Local command and workflow validation are documented
  in [baseline.md](baseline.md). The first hosted run and Mermaid rendering are
  not claimed as verified.
