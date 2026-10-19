# Improvement implementation plan

Date: 2026-10-19

Status: Phase 0 tooling implemented; real-model verification is pending. See
[baseline results and reproduction instructions](baseline.md).

Use [decision.md](decision.md) for proposed constraints and
[flow.md](flow.md) for current and target behavior. Deliver small reviewable
changes in the order below. No dates or effort estimates are committed until
the baseline build and model runtime have been verified.

## Phase 0 — Establish the baseline

- [x] Reproduce backend and frontend installation in isolated environments.
- [x] Record available Python, Node, Ollama CLI, and dependency versions.
- [ ] Record Ollama server version and configured model digests after provisioning.
- [ ] Smoke-test ingest, chat, restart/reload, and first-run model setup using a
  small non-sensitive fixture PDF.
- [x] Introduce API tests with mocked model calls and a separately invoked
  integration smoke test requiring Ollama.
- [x] Capture current API response contracts before extending them.

Evidence: 15 offline tests, backend dependency/import checks, and the locked
frontend build passed. Real-model smoke preflight failed with connection refused
at localhost:11434; no models were downloaded. The implemented smoke runner
checks ingest/chat and a second-process reload when prerequisites are available.
See the [baseline](baseline.md) and [current API contract](api-contract.md).

Exit: setup is reproducible, failures are recorded, and tests do not require
private documents or silently invoke/download models.

## Phase 1 — Close the unsafe input and server boundaries

- [ ] Replace client-derived storage paths with generated IDs; validate path
  containment and separate upload storage from executable/index artifacts.
- [ ] Add request-size, PDF validity, page/text, and query-length limits.
- [ ] Validate JSON object/string types and return stable structured errors.
- [ ] Handle parser errors, empty/image-only/encrypted PDFs, and Ollama failures.
- [ ] Disable debug, configure a production server, restrict CORS, and default
  local published ports to loopback. Start with one backend worker.
- [ ] Review FAISS loading so only application-controlled artifacts are trusted.
- [ ] Correct unconditional privacy messaging and deployment instructions.

Exit: traversal/absolute-path filenames cannot write outside controlled storage;
malformed JSON and unsupported inputs return appropriate 4xx responses; service
failures return safe structured errors; debug is off. Tests cover these cases
and cleanup after failed uploads. No shared deployment is advertised as ready.

## Phase 2 — Make document and index state reliable

Depends on Phase 1 storage boundaries.

- [ ] Define the document catalog schema and index manifest, including content
  hashes, page provenance, model identity, chunking configuration, and versions.
- [ ] Implement idempotent uploads and stable document IDs.
- [ ] Serialize ingestion through one owner and prevent a second writer process.
- [ ] Publish complete snapshots atomically with a documented catalog commit
  and crash-recovery protocol; keep a known-good previous version.
- [ ] Add document listing/status, deletion, and explicit rebuild operations.
- [ ] Reject incompatible embedding configurations with a rebuild instruction.

Exit: duplicate uploads do not add chunks, concurrent operations do not lose
documents, and interruption/restart recovers a consistent committed version.
Deletion removes a document from retrieval. Ingest failure preserves the old
index. Verify these with temporary stores and fault-injection tests.

Migration: existing indexes lack catalog/version metadata. Preserve a backup,
re-ingest retained source PDFs into the new format, verify document counts and
representative answers, then switch versions. Do not silently reuse an index
with unknown embedding configuration. Restore the old version on failure.

## Phase 3 — Make answers inspectable and measure quality

Depends on Phase 2 document identity and provenance.

- [ ] Return answer, sources, and index version; preserve the `answer` field.
- [ ] Add document filters, grounded prompting, and explicit abstention behavior.
- [ ] Render filename/page citations and supporting excerpts in the frontend.
- [ ] Build a versioned, non-sensitive financial QA benchmark with expected
  evidence pages and numeric answers, including unsupported questions.
- [ ] Report retrieval recall, citation support, numeric accuracy, abstention,
  and latency separately. Record model/configuration with every run.
- [ ] Test malicious instructions embedded in documents and unsupported claims.

Exit: every returned citation maps to an indexed document/page; answer support
is reviewed on the benchmark. Record baseline results and agree numerical
release thresholds before claiming quality improvements. Mocked tests are not
evidence of model accuracy.

## Phase 4 — Complete deployment and operational verification

Depends on the persistence design in Phase 2; deployment preparation may begin
earlier, but persistence claims require recovery tests.

- [x] Configure GitHub Actions for offline backend tests and locked frontend builds.
- [ ] Record the first successful hosted CI run after pushing workflow and tests.
- [ ] Lock backend dependencies and finish reproducible deployment installs.
- [ ] Make Compose provision required models and wait for bounded readiness.
- [ ] Align README Ollama instructions with the actual Compose service topology.
- [ ] Add Kubernetes persistent storage, probes, resource limits, ingress-class
  configuration, and an explicit Ollama provisioning/external-service path.
- [ ] Validate ingress rewrites, upload limits, and inference timeout settings.
- [ ] Add request IDs, safe structured logs, timings, and readiness diagnostics.
- [ ] Document and exercise backup/restore of the catalog, PDFs, and index.
- [ ] Scan dependencies/images and triage actual findings.

Exit: a fresh Compose installation ingests and answers after model initialization;
restart preserves the corpus. Kubernetes rollout and ingress are tested in a
declared environment, and volume persistence and restore are demonstrated.
Keep one index-owning backend replica until a scaling decision supersedes D3.

## Phase 5 — Improve the product against measured needs

- [ ] Add upload/document states, source navigation, accessible input/status
  labels, request cancellation, and clear retry behavior.
- [ ] Introduce bounded conversational history, reset behavior, and follow-up
  query rewriting; test period/company/document references across turns.
- [ ] Evaluate OCR, table extraction, hybrid retrieval, or reranking only where
  benchmark failures justify the complexity.
- [ ] Add answer streaming if measured latency warrants it, with cancellation
  and error handling tested end to end.

Exit: follow-up questions resolve the intended context, users can inspect and
manage their documents, and quality changes are backed by benchmark comparisons.

## Shared-host release gate

This is a separate deployment milestone, not an implied feature of Phases 0–5.
Choose authentication and tenancy requirements, implement corpus authorization,
TLS, quotas and retention/deletion policy, then test cross-user isolation and
resource abuse. A CORS allowlist or Kubernetes deployment alone does not meet
this gate.

## Working agreement and immediate next change

Finish the Phase 0 real-model gate when Ollama is available, then begin Phase 1
upload/input regression tests. Keep the stack
and current API routes unless a documented migration is necessary. After each
completed unit, update decisions and flows when behavior changes, record checks
and limitations, and run documentation-link and whitespace checks. Mark tasks
complete only when their acceptance evidence exists.

## Maintenance log

- 2026-10-19: Created the phased backlog and acceptance gates from the repository
  review. Reviewed current and proposed architecture in [flow.md](flow.md) and
  decisions in [decision.md](decision.md); no application behavior changed.
- 2026-10-19: Added Phase 0 contract tests, synthetic PDF, offline pipeline
  persistence check, and explicit real-model restart smoke runner. Recorded
  successful installs/builds and the unavailable Ollama prerequisite. Reviewed
  decisions and flows; production architecture is unchanged. Kept model-dependent
  verification unchecked rather than treating deterministic substitutes as results.
- 2026-10-19: Brought forward the CI configuration task from Phase 4. Added
  push/PR/manual test and build jobs; hosted execution remains a separate unchecked
  gate. Reviewed [decisions](decision.md) and [flows](flow.md), including the new
  configured verification platform; application architecture is unchanged.
- 2026-10-19: Reviewed decisions and flows while preparing the Phase 0 commit.
  Removed Markdown trailing whitespace and marked PDFs as binary in Git so
  fixture format bytes are not treated as text whitespace. No runtime flow or
  architecture change; staged whitespace validation is required before commit.
