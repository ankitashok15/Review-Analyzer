import { Link } from "react-router-dom";

interface EvidencePanelProps {
  title?: string;
  reviewIds: string[];
}

export function EvidencePanel({ title = "Supporting evidence", reviewIds }: EvidencePanelProps) {
  if (!reviewIds.length) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        <p className="mt-2 text-sm text-slate-500">No linked reviews.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      <ul className="mt-3 space-y-2">
        {reviewIds.map((id) => (
          <li key={id}>
            <Link
              to={`/reviews/${id}`}
              className="text-sm text-brand-600 hover:text-brand-700 hover:underline"
            >
              Review {id.slice(0, 8)}…
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
