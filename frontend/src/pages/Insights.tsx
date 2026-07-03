import { useMutation, useQuery } from "@tanstack/react-query";
import { EvidencePanel } from "../components/EvidencePanel";
import { api } from "../services/api";

export function InsightsPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["insights"],
    queryFn: () => api.listInsights(),
  });

  const refreshMutation = useMutation({
    mutationFn: () => api.refreshInsights(),
    onSuccess: () => refetch(),
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading insights…</p>;
  if (isError) return <p className="text-sm text-red-600">Failed to load insights.</p>;

  const insights = data?.insights ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Insights</h2>
          <p className="text-sm text-slate-500">Aggregated pain points, trends, and themes.</p>
        </div>
        <button
          className="btn-secondary"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
        >
          {refreshMutation.isPending ? "Refreshing…" : "Refresh"}
        </button>
      </div>

      {insights.length === 0 ? (
        <div className="card">
          <p className="text-sm text-slate-600">
            No cached insights yet. Click Refresh to generate from enriched reviews.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((insight) => (
            <div key={`${insight.insight_type}-${insight.cache_key}`} className="card">
              <div className="mb-2 flex items-center gap-2">
                <span className="badge bg-brand-50 text-brand-700">{insight.insight_type}</span>
                <span className="text-xs text-slate-400">{insight.generated_at.slice(0, 10)}</span>
              </div>
              <h3 className="font-semibold text-slate-900">{insight.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{insight.summary}</p>
              <div className="mt-4">
                <EvidencePanel
                  title="Evidence"
                  reviewIds={insight.evidence_review_ids.slice(0, 5)}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
