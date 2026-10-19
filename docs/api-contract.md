# Baseline API contract

Captured: 2026-10-19, before Phase 1 changes. Tests live in
`backend/tests/test_api.py`. These are current behaviors, including defects,
not the target validation/error contract. No authentication or corpus selection
is implemented.

## GET /health

HTTP 200, JSON:

```json
{"status": "ok", "vectorstore_ready": false}
```

`vectorstore_ready` becomes `true` when an index is available. This does not
prove Ollama connectivity or model availability. Index-loading failures can
propagate instead of producing a healthy response.

## POST /ingest

Multipart form data with one field named `file`. Successful HTTP 200, JSON:

```json
{"status": "ingested", "chunks": 1, "file": "synthetic-financial.pdf"}
```

`chunks` is the number produced from this upload, not the corpus total.
`file` is the saved basename; no stable document ID is returned. The handler
saves the file before calling ingestion. Repeated uploads append chunks.

- Missing field: HTTP 400, `{"error": "No file part"}`.
- Empty filename: HTTP 400, `{"error": "Empty filename"}`.
- Parser/embedding/storage exceptions: unhandled HTTP 500, normally HTML.

The current handler does not enforce PDF validity, filename safety, or application
upload limits. The browser file picker restriction is not server validation.

## POST /chat

JSON object:

```json
{"query": "What was revenue in FY2025?"}
```

Leading/trailing query whitespace is removed. Successful HTTP 200, JSON:

```json
{"answer": "USD 120 million."}
```

This example is synthetic; actual text depends on the model. Sources, page
citations, session history, and index versions are not returned or accepted as
part of the implemented contract. Only the latest query reaches the pipeline.

- Missing/blank query: HTTP 400, `{"error": "Missing query"}`.
- Malformed JSON: HTTP 400 with the same missing-query error.
- Empty index: HTTP 400,
  `{"error": "Vector store is empty. Ingest a PDF first."}`.
- Other `ValueError` from the pipeline: HTTP 400 with its message in `error`.
- Non-empty JSON array or non-string query: can return HTTP 500, normally HTML.
- Uncaught model/service exceptions: HTTP 500, normally HTML.

Phase 1 must replace the malformed-type and service-failure characterization
tests when implementing safe structured errors; preserving these defects is not
a compatibility requirement. Successful `answer` clients should remain compatible
when citations are added in Phase 3.
