const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

export async function uploadPDF(file) {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || "Failed to ingest PDF.");
  }

  return response.json();
}

export async function sendQuery(query) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || "Failed to fetch answer.");
  }

  return response.json();
}
