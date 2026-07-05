import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { useMutation } from "@tanstack/react-query";
import { CitationCard } from "../components/CitationCard";
import { api } from "../services/api";

const SAMPLE_QUESTIONS = [
  "Why do users struggle to discover new music?",
  "What frustrations exist with recommendations?",
  "Which product features are most frequently requested?",
];

export function AskPage() {
  const [question, setQuestion] = useState("");

  const askMutation = useMutation({
    mutationFn: (q: string) => api.ask(q, 15),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim()) askMutation.mutate(question.trim());
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Research Q&A</h2>
        <p className="text-sm text-slate-500">
          Ask questions and get citation-backed answers from review evidence.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {SAMPLE_QUESTIONS.map((sample) => (
          <button
            key={sample}
            type="button"
            className="btn-secondary text-left text-xs"
            onClick={() => {
              setQuestion(sample);
              askMutation.mutate(sample);
            }}
          >
            {sample}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          className="input flex-1"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a research question…"
        />
        <button type="submit" className="btn-primary" disabled={askMutation.isPending}>
          {askMutation.isPending ? "Thinking…" : "Ask"}
        </button>
      </form>

      {askMutation.isError && (
        <p className="text-sm text-red-600">{(askMutation.error as Error).message}</p>
      )}

      {askMutation.data && (
        <div className="space-y-4">
          {askMutation.data.answer_mode === "general" && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              General AI insight — not backed by embedded reviews in this dataset.
            </div>
          )}
          <div className="card">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="badge bg-brand-50 text-brand-700">
                {askMutation.data.confidence} confidence
              </span>
              {askMutation.data.answer_mode === "grounded" && (
                <span className="badge bg-emerald-50 text-emerald-700">evidence-backed</span>
              )}
              <span className="text-xs text-slate-400">
                {askMutation.data.retrieval_count} reviews retrieved
              </span>
            </div>
            <div className="prose prose-sm max-w-none text-slate-800">
              <ReactMarkdown>{askMutation.data.answer}</ReactMarkdown>
            </div>
          </div>

          {askMutation.data.citations.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-700">Citations</h3>
              {askMutation.data.citations.map((citation) => (
                <CitationCard key={citation.review_id} citation={citation} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
