import { useQuery } from "@tanstack/react-query";
import { EvidencePanel } from "../components/EvidencePanel";
import { api } from "../services/api";

export function SegmentsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["segments"],
    queryFn: () => api.listSegments(),
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading segments…</p>;
  if (isError) return <p className="text-sm text-red-600">Failed to load segments.</p>;

  const segments = data?.segments ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">User Segments</h2>
        <p className="text-sm text-slate-500">Sentiment breakdown by user segment.</p>
      </div>

      {segments.length === 0 ? (
        <div className="card">
          <p className="text-sm text-slate-600">
            No segment data. Enrichment is required for segment analysis.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="py-2 pr-4">Segment</th>
                <th className="py-2 pr-4">Sentiment</th>
                <th className="py-2 pr-4">Count</th>
                <th className="py-2">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {segments.map((row, idx) => (
                <tr key={idx} className="border-b border-slate-100">
                  <td className="py-3 pr-4">{row.user_segment ?? "—"}</td>
                  <td className="py-3 pr-4">{row.sentiment ?? "—"}</td>
                  <td className="py-3 pr-4">{row.count}</td>
                  <td className="py-3">
                    <EvidencePanel reviewIds={row.evidence_review_ids.slice(0, 3)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
