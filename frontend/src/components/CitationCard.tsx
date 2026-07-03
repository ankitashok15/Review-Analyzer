import { Link } from "react-router-dom";
import type { Citation, SearchResult } from "../types/api";

interface CitationCardProps {
  citation: Citation;
}

export function CitationCard({ citation }: CitationCardProps) {
  return (
    <Link to={`/reviews/${citation.review_id}`} className="card block hover:border-brand-500">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="badge bg-slate-100 text-slate-600">{citation.source}</span>
        <span className="text-xs text-slate-400">
          relevance {(citation.relevance_score * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-sm text-slate-700 italic">&ldquo;{citation.excerpt}&rdquo;</p>
      <p className="mt-2 text-xs text-brand-600">View full review →</p>
    </Link>
  );
}

interface SearchResultCardProps {
  result: SearchResult;
}

export function SearchResultCard({ result }: SearchResultCardProps) {
  return (
    <Link to={`/reviews/${result.review_id}`} className="card block hover:border-brand-500">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="badge bg-slate-100 text-slate-600">{result.source}</span>
        <span className="badge bg-slate-100 text-slate-600">{result.platform}</span>
        {result.rating != null && (
          <span className="badge bg-amber-50 text-amber-700">{result.rating}★</span>
        )}
        {result.sentiment && (
          <span className="badge bg-blue-50 text-blue-700">{result.sentiment}</span>
        )}
        <span className="ml-auto text-xs text-slate-400">
          score {(result.score * 100).toFixed(0)}%
        </span>
      </div>
      <p className="text-sm text-slate-800">{result.excerpt}</p>
      {result.primary_topic && (
        <p className="mt-2 text-xs text-slate-500">Topic: {result.primary_topic}</p>
      )}
      <p className="mt-2 text-xs text-slate-400">{result.review_date.slice(0, 10)}</p>
    </Link>
  );
}
