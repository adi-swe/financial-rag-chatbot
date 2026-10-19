# Change decisions

Date: 2026-10-19

Status: proposed implementation baseline; application changes have not started.

See [flows](flow.md) and the [implementation plan](plan.md).

## Scope and evidence

Keep the Flask, React, Ollama, and FAISS stack while fixing the highest-impact
gaps. The first target is a reliable, single-user local installation. A shared
or internet-facing service requires a separate access-control milestone.

The repository review covered application code, dependency manifests, Docker,
Kubernetes, and setup instructions. Flask probes with mocked RAG and file saves
confirmed that traversal filenames reach the save operation, malformed chat JSON
returns 500, and arbitrary request origins receive CORS permission. These probes
did not write uploaded files or measure model quality. Full builds, model calls,
dependency vulnerability checks, and Kubernetes deployment remain unverified.

## D1 — Make uploads a bounded, trusted input boundary

Use server-generated document IDs and storage paths. Treat the supplied filename
as display metadata only. Enforce upload-directory containment, request size,
PDF signature/parser validation, and page/extracted-text limits. Reject empty,
invalid, encrypted, or unsupported documents with structured errors; report
image-only PDFs as requiring OCR until OCR is implemented.

Remove temporary files after failure. Prevent upload writes from reaching code
or index artifacts. FAISS pickle metadata may only be loaded from index files
created and controlled by this application; enabling dangerous deserialization
does not establish trust by itself.

## D2 — Keep local operation simple; gate shared access

Disable Flask debug mode and use a production WSGI server for containers. Bind
local published services to loopback by default and configure an explicit CORS
allowlist. CORS is not authentication.

Do not enable shared access until authentication, corpus authorization, TLS,
request limits, and per-user access tests are in place. Identity-provider and
tenant design are deferred pending deployment requirements. Do not claim that
data stays on the machine when Ollama is configured at a remote address.

## D3 — Use one index owner before adding workers

Retain FAISS for the initial single-instance deployment. Use one process owning
the index, serialized ingestion, consistent reads during publication, and
versioned snapshots published atomically. Keep the previous valid snapshot
until the new one is committed. A second writer process must fail clearly.

Track document ID, content hash, original filename, page provenance, ingestion
state, embedding model identity, chunking configuration, and index version in a
durable catalog. Define snapshot/catalog recovery so a crash cannot expose
partially committed documents. Re-uploading identical content is idempotent.
Changing embedding configuration requires an explicit rebuild.

Multiple backend replicas or independent WSGI workers require a new storage and
coordination decision; increasing replica count is not an approved scaling path.

## D4 — Return evidence with answers

Extend successful chat responses to include `answer`, `sources`, and
`index_version`. Each source includes a document ID, display filename,
one-based page number, and supporting excerpt. Preserve existing `answer`
clients while introducing these additional fields.

Associate answer citations with retrieved source identifiers. Add an explicit
insufficient-evidence response and treat retrieved text as untrusted content.
Citations show provenance; they do not prove correctness. Do not present raw
retrieval similarity as calibrated confidence.

## D5 — Measure financial quality before increasing retrieval complexity

Create a labeled benchmark for revenue, cash flow, negative values, currencies,
units, reporting periods, table extraction, conflicting filings, and unanswered
questions. Separate retrieval recall, citation support, numeric correctness,
abstention, and latency measurements.

Retain basic retrieval as the baseline. Evaluate metadata filtering, hybrid
search, reranking, table-aware extraction, and OCR against observed failures.
Do not add these components solely because they are common in RAG systems.

## D6 — Make deployment and verification reproducible

Retain the tracked frontend lockfile, add backend dependency locking, use
reproducible installation commands, add CI, and
document tested runtime/model versions. Compose must provision required models
and wait for readiness. Kubernetes must declare persistent storage and either
provide Ollama or document and validate an external endpoint.

Separate liveness from readiness. Bound model requests and log request IDs,
durations, and error categories without logging document contents or queries by
default. Verify backup restoration, not only backup creation.

GitHub Actions CI is configured in [ci.yml](../.github/workflows/ci.yml): pushes,
pull requests, and manual dispatches run independent Ubuntu 24.04 jobs for
Python 3.11 offline tests and a Node 22 frontend build. Use the tracked frontend
lockfile, dependency caches, read-only repository permissions, immutable action
commit references, and bounded job durations. Model calls, model downloads, and
deployment are excluded from this automatic verification path. The first hosted
run remains unverified until the workflow and its test fixtures are pushed.

## D7 — Add conversational behavior after the evidence contract

First make document state and citations visible. Then introduce bounded session
history and query rewriting with explicit retention and reset behavior. Prior
turns can clarify a question but are not document evidence. Until then, describe
the interface as independent questions rather than a context-aware conversation.

## Deferred choices

- Shared-host identity provider and tenant isolation model.
- OCR/table extraction engine and any additional retrieval infrastructure.
- Multi-replica vector storage and job-queue technology.
- Chat-history persistence and retention policy.

Resolve these through measured needs or deployment requirements. Record changed
decisions here with dates and rationale rather than silently replacing them.

## Maintenance log

- 2026-10-19: Established proposed decisions from the repository review. No
  runtime architecture changed. Cross-checked this document against the current
  and proposed flows and phased acceptance criteria.
- 2026-10-19: Phase 0 added isolated API contract tests and an explicit real-model
  smoke runner with disposable corpus storage and separate ingest/reload
  processes. Reviewed the decisions and flows: runtime architecture is unchanged.
  Corrected the review's lockfile claim: `frontend/package-lock.json` is tracked.
- 2026-10-19: Reviewed the completed Phase 0 tooling and [baseline](baseline.md).
  Real PDF/FAISS cold-cache tests use deterministic model substitutes; the
  separate real-model runner remains blocked on server availability. No new
  production architecture decision or runtime change was introduced.
- 2026-10-19: Implemented the CI portion of D6 with a GitHub Actions workflow.
  Reviewed production architecture and verification flows; application behavior
  and persistence are unchanged. Local test/build and workflow validation results
  are recorded in [baseline.md](baseline.md); hosted execution remains pending.
