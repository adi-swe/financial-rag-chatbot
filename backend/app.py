import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from rag_pipeline import ingest_pdf, ask_rag, get_status

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "vectorstore_ready": get_status()})


@app.post("/ingest")
def ingest():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(save_path)
    result = ingest_pdf(save_path)
    return jsonify(result)


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    query = payload.get("query", "").strip()
    if not query:
        return jsonify({"error": "Missing query"}), 400

    try:
        answer = ask_rag(query)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
