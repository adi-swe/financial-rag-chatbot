import { useState } from "react";
import { sendQuery, uploadPDF } from "../api.js";

export default function ChatWindow() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Upload a financial PDF, then ask a question about revenue, risks, or guidance.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [status, setStatus] = useState("Ready.");

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) {
      return;
    }

    setIsSending(true);
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");

    try {
      const result = await sendQuery(trimmed);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer || "No answer." },
      ]);
      setStatus("Answer ready.");
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: error.message },
      ]);
      setStatus("Request failed.");
    } finally {
      setIsSending(false);
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file || isIngesting) {
      return;
    }

    setIsIngesting(true);
    setStatus("Ingesting PDF...");

    try {
      await uploadPDF(file);
      setStatus("Ingestion complete. Ask a question.");
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsIngesting(false);
      event.target.value = "";
    }
  };

  return (
    <div className="flex min-h-[600px] flex-col gap-6 rounded-3xl border border-ink/10 bg-white/80 p-8 shadow-[0_25px_70px_-45px_rgba(16,18,35,0.7)]">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-2xl font-semibold text-ink">
            Interactive briefings
          </h2>
          <p className="text-sm text-ink/70">{status}</p>
        </div>
        <label className="cursor-pointer rounded-full border border-ink/20 bg-ink/5 px-4 py-2 text-xs uppercase tracking-[0.2em] text-ink/70 transition hover:border-ink/40">
          {isIngesting ? "Ingesting" : "Upload PDF"}
          <input
            type="file"
            accept="application/pdf"
            onChange={handleUpload}
            className="hidden"
          />
        </label>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto rounded-2xl border border-ink/10 bg-paper/70 p-4">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
              message.role === "user"
                ? "ml-auto bg-ink text-white"
                : "bg-white text-ink"
            }`}
          >
            {message.content}
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <textarea
          rows={3}
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about cash flow trends, guidance changes, or risk factors..."
          className="w-full resize-none rounded-2xl border border-ink/15 bg-white px-4 py-3 text-sm focus:border-ink/40 focus:outline-none"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={isSending}
          className="rounded-2xl bg-ocean px-5 py-3 text-sm uppercase tracking-[0.2em] text-white transition hover:bg-ink disabled:cursor-not-allowed disabled:bg-ink/60"
        >
          {isSending ? "Thinking" : "Send"}
        </button>
      </div>
    </div>
  );
}
