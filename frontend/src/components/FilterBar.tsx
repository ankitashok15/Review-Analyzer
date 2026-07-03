import type { SearchFilters } from "../types/api";

interface FilterBarProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

export function FilterBar({ filters, onChange }: FilterBarProps) {
  return (
    <div className="card space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">Filters</h3>
      <label className="block text-xs text-slate-500">
        Source
        <input
          className="input mt-1"
          value={filters.source ?? ""}
          onChange={(e) => onChange({ ...filters, source: e.target.value || null })}
          placeholder="e.g. google_play"
        />
      </label>
      <label className="block text-xs text-slate-500">
        Platform
        <input
          className="input mt-1"
          value={filters.platform ?? ""}
          onChange={(e) => onChange({ ...filters, platform: e.target.value || null })}
          placeholder="e.g. android"
        />
      </label>
      <label className="block text-xs text-slate-500">
        Sentiment
        <select
          className="input mt-1"
          value={filters.sentiment ?? ""}
          onChange={(e) => onChange({ ...filters, sentiment: e.target.value || null })}
        >
          <option value="">Any</option>
          <option value="positive">Positive</option>
          <option value="negative">Negative</option>
          <option value="neutral">Neutral</option>
          <option value="mixed">Mixed</option>
        </select>
      </label>
      <label className="block text-xs text-slate-500">
        Min rating
        <input
          type="number"
          min={1}
          max={5}
          className="input mt-1"
          value={filters.min_rating ?? ""}
          onChange={(e) =>
            onChange({
              ...filters,
              min_rating: e.target.value ? Number(e.target.value) : null,
            })
          }
        />
      </label>
    </div>
  );
}
