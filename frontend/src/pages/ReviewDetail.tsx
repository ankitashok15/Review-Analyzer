import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";

export function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["review", id],
    queryFn: () => api.getReview(id!),
    enabled: Boolean(id),
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading review…</p>;
  if (isError) return <p className="text-sm text-red-600">{(error as Error).message}</p>;
  if (!data) return null;

  const enrichment = data.enrichment;

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-brand-600 hover:underline">
        ← Back to search
      </Link>

      <div className="card space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge bg-slate-100 text-slate-600">{data.source}</span>
          <span className="badge bg-slate-100 text-slate-600">{data.platform}</span>
          {data.rating != null && (
            <span className="badge bg-amber-50 text-amber-700">{data.rating}★</span>
          )}
          <span className="text-xs text-slate-400">{data.review_date.slice(0, 10)}</span>
        </div>

        {data.title && <h2 className="text-lg font-semibold">{data.title}</h2>}
        <p className="whitespace-pre-wrap text-slate-800">{data.body}</p>

        {data.source_url && (
          <a
            href={data.source_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-brand-600 hover:underline"
          >
            View original source
          </a>
        )}
      </div>

      {enrichment && (
        <div className="card">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">AI Enrichment</h3>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            {enrichment.sentiment && (
              <>
                <dt className="text-slate-500">Sentiment</dt>
                <dd>{enrichment.sentiment}</dd>
              </>
            )}
            {enrichment.primary_topic && (
              <>
                <dt className="text-slate-500">Topic</dt>
                <dd>{enrichment.primary_topic}</dd>
              </>
            )}
            {enrichment.pain_point && (
              <>
                <dt className="text-slate-500">Pain point</dt>
                <dd>{enrichment.pain_point}</dd>
              </>
            )}
            {enrichment.feature_request && (
              <>
                <dt className="text-slate-500">Feature request</dt>
                <dd>{enrichment.feature_request}</dd>
              </>
            )}
            {enrichment.user_segment && (
              <>
                <dt className="text-slate-500">Segment</dt>
                <dd>{enrichment.user_segment}</dd>
              </>
            )}
            {enrichment.summary && (
              <>
                <dt className="text-slate-500 sm:col-span-2">Summary</dt>
                <dd className="sm:col-span-2">{enrichment.summary}</dd>
              </>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}
