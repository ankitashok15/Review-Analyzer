import { useQuery } from "@tanstack/react-query";
import { EvidencePanel } from "../components/EvidencePanel";
import { api } from "../services/api";

export function TopicsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["topics"],
    queryFn: () => api.listTopics(30),
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading topics…</p>;
  if (isError) return <p className="text-sm text-red-600">Failed to load topics.</p>;

  const topics = data?.topics ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Topic Clusters</h2>
        <p className="text-sm text-slate-500">Primary topics from enriched reviews.</p>
      </div>

      {topics.length === 0 ? (
        <div className="card">
          <p className="text-sm text-slate-600">
            No topics found. Run enrichment to populate topic data.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {topics.map((topic) => (
            <div key={topic.topic} className="card">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-slate-900">{topic.topic}</h3>
                <span className="badge bg-slate-100 text-slate-600">{topic.count} reviews</span>
              </div>
              <div className="mt-3">
                <EvidencePanel reviewIds={topic.evidence_review_ids} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
