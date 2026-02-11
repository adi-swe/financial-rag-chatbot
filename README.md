# Financial RAG Chatbot (Flask + React)

Local-first RAG chatbot for financial PDFs using Flask, LangChain, FAISS, and Ollama.

## Features
- PDF ingestion and chunking
- FAISS vector store for retrieval
- Local Llama chat model via Ollama
- React + Vite + Tailwind UI

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

## Notes
- Vector store files are saved under `backend/vectorstore`.
- Uploaded PDFs are stored in `backend/data/uploads`.
- Configure Ollama models via `backend/.env.example`.
