import ChatWindow from "./components/ChatWindow.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-atlas text-ink">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-12">
        <header className="grid gap-6">
          <p className="text-xs uppercase tracking-[0.3em] text-ocean">
            Financial RAG Studio
          </p>
          <h1 className="font-display text-4xl font-semibold leading-tight text-ink md:text-5xl">
            Turn dense filings into crisp answers.
          </h1>
          <p className="max-w-2xl font-serif text-lg text-ink/80">
            Upload quarterly reports, build your knowledge base, and interrogate it with
            a local Llama model.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <ChatWindow />
          <aside className="rounded-3xl border border-ink/10 bg-paper/80 p-8 shadow-[0_18px_60px_-40px_rgba(16,18,35,0.6)]">
            <h2 className="font-display text-2xl font-semibold text-ink">
              Operational checklist
            </h2>
            <ul className="mt-6 space-y-4 text-sm text-ink/75">
              <li>
                Ensure Ollama is running locally and the models are pulled.
              </li>
              <li>
                Ingest at least one PDF before asking multi-document questions.
              </li>
              <li>
                Use focused queries like “Summarize liquidity risks in 2023”.
              </li>
              <li>
                Keep ingestion batches under 30 pages for faster iteration.
              </li>
            </ul>
            <div className="mt-8 rounded-2xl bg-ink/5 p-4 text-xs uppercase tracking-[0.2em] text-ink/50">
              Local-first. No data leaves your machine.
            </div>
          </aside>
        </section>
      </div>
    </div>
  );
}
