import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../services/api";

export function ExportPage() {
  const [idsText, setIdsText] = useState("");
  const [format, setFormat] = useState<"json" | "csv">("json");

  const exportMutation = useMutation({
    mutationFn: async () => {
      const reviewIds = idsText
        .split(/[\s,]+/)
        .map((s) => s.trim())
        .filter(Boolean);
      if (!reviewIds.length) throw new Error("Enter at least one review ID");

      if (format === "csv") {
        const csv = await api.exportCsv(reviewIds);
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "reviews-export.csv";
        a.click();
        URL.revokeObjectURL(url);
        return { count: reviewIds.length };
      }

      return api.exportJson(reviewIds);
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Export Findings</h2>
        <p className="text-sm text-slate-500">
          Export selected reviews from search or insight evidence.
        </p>
      </div>

      <div className="card space-y-4">
        <label className="block text-sm text-slate-600">
          Review IDs (comma or newline separated)
          <textarea
            className="input mt-1 min-h-[120px] font-mono text-xs"
            value={idsText}
            onChange={(e) => setIdsText(e.target.value)}
            placeholder="uuid-1, uuid-2, …"
          />
        </label>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              checked={format === "json"}
              onChange={() => setFormat("json")}
            />
            JSON
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              checked={format === "csv"}
              onChange={() => setFormat("csv")}
            />
            CSV download
          </label>
        </div>

        <button
          className="btn-primary"
          onClick={() => exportMutation.mutate()}
          disabled={exportMutation.isPending}
        >
          {exportMutation.isPending ? "Exporting…" : "Export"}
        </button>

        {exportMutation.isError && (
          <p className="text-sm text-red-600">{(exportMutation.error as Error).message}</p>
        )}

        {exportMutation.data && format === "json" && "rows" in exportMutation.data && (
          <pre className="max-h-96 overflow-auto rounded bg-slate-900 p-4 text-xs text-slate-100">
            {JSON.stringify(exportMutation.data, null, 2)}
          </pre>
        )}

        {exportMutation.data && format === "csv" && (
          <p className="text-sm text-green-700">CSV download started.</p>
        )}
      </div>
    </div>
  );
}
