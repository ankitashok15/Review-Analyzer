import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { FilterBar } from "../components/FilterBar";
import { SearchResultCard } from "../components/CitationCard";
import { api } from "../services/api";
import type { SearchFilters } from "../types/api";

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({});

  const searchMutation = useMutation({
    mutationFn: () => api.search(query, filters, 15),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) searchMutation.mutate();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Semantic Search</h2>
        <p className="text-sm text-slate-500">
          Find reviews by meaning, not just keywords.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
        <FilterBar filters={filters} onChange={setFilters} />
        <div className="space-y-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              className="input flex-1"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. repetitive Discover Weekly playlists"
            />
            <button type="submit" className="btn-primary" disabled={searchMutation.isPending}>
              {searchMutation.isPending ? "Searching…" : "Search"}
            </button>
          </form>

          {searchMutation.isError && (
            <p className="text-sm text-red-600">{(searchMutation.error as Error).message}</p>
          )}

          {searchMutation.data && (
            <div className="space-y-3">
              <p className="text-sm text-slate-500">
                {searchMutation.data.count} results for &ldquo;{searchMutation.data.query}&rdquo;
              </p>
              {searchMutation.data.results.map((result) => (
                <SearchResultCard key={result.review_id} result={result} />
              ))}
              {searchMutation.data.count === 0 && (
                <p className="text-sm text-slate-500">No matching reviews found.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
