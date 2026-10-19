# Financial RAG Chatbot (Flask + React)

Local-first RAG chatbot for financial PDFs using Flask, LangChain, FAISS, and Ollama.

## Features
- PDF ingestion and chunking
- FAISS vector store for retrieval
- Local Llama chat model via Ollama
- React + Vite + Tailwind UI

## Improvement planning

- [Proposed decisions](docs/decision.md)
- [Current and proposed application flows](docs/flow.md)
- [Phased implementation plan](docs/plan.md)
- [Baseline verification and test setup](docs/baseline.md)
- [Current API contract](docs/api-contract.md)

## Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama installed and running

## Ollama Setup
```bash
ollama pull llama3.1
ollama pull nomic-embed-text
ollama serve
```

## Backend Setup
```bash
cd financial-rag-chatbot/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API runs at `http://localhost:5000`.

## Frontend Setup
```bash
cd financial-rag-chatbot/frontend
npm install
npm run dev
```

Open the app at the URL shown by Vite (usually `http://localhost:5173`).

## Docker
```bash
cd financial-rag-chatbot
docker compose up --build
```

The frontend is served at `http://localhost:5173` and the API at `http://localhost:5000`.

If Ollama runs on your host, Docker uses `OLLAMA_BASE_URL=http://host.docker.internal:11434`.

## Kubernetes
Build images (example names used in the manifests):
```bash
docker build -t financial-rag-backend:latest ./backend
docker build --build-arg VITE_API_URL=/api -t financial-rag-frontend:latest ./frontend
```

Apply manifests:
```bash
kubectl apply -f k8s/ollama-config.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/ingress-backend.yaml
kubectl apply -f k8s/ingress-frontend.yaml
```

Update `OLLAMA_BASE_URL` in the config map if Ollama is hosted elsewhere.

## API Reference
- `POST /ingest` (multipart form-data with `file`)
- `POST /chat` JSON: `{ "query": "..." }`
- `GET /health`

## Tests

GitHub Actions [CI](.github/workflows/ci.yml) runs on pushes, pull requests, and
manual dispatches. Separate Ubuntu 24.04 jobs run the offline backend suite on
Python 3.11 and build the frontend from its lockfile on Node 22. No secrets or
Ollama models are required. GitHub execution is pending the first push of the
workflow and test files; this workflow does not deploy the application.

From the repository root, after installing the backend requirements:

```sh
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

The default suite uses synthetic data and model substitutes; it does not call
Ollama or download models. The real Ollama ingest/chat/restart smoke test is
explicitly opt-in and requires both configured models to be installed:

```sh
backend/.venv/bin/python backend/scripts/smoke_ollama.py --run
```

See [baseline setup and results](docs/baseline.md) for environment creation,
model provisioning, current limitations, and the difference between offline
checks and real-model verification.

## Notes
- Vector store files are saved under `backend/vectorstore`.
- Uploaded PDFs are stored in `backend/data/uploads`.
- Configure Ollama models via `backend/.env.example`.
