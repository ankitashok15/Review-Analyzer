import type {
  AskResponse,
  ExportResponse,
  InsightListResponse,
  ReviewDetail,
  SearchFilters,
  SearchResponse,
  SegmentsResponse,
  TopicsResponse,
} from "../types/api";
import { buildClientAskFallback } from "./askFallback";

const API_BASE =
  import.meta.env.VITE_API_URL ||
  "https://review-analyzer-production-453f.up.railway.app";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      ...init,
    });
  } catch {
    throw new Error("Failed to fetch");
  }
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(detail.detail ?? `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function requestAsk(question: string, topK: number): Promise<AskResponse> {
  try {
    return await request<AskResponse>("/api/v1/ask", {
      method: "POST",
      body: JSON.stringify({
        question,
        top_k: topK,
        include_insights: true,
        allow_fallback: true,
      }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Request failed";
    if (message === "Failed to fetch") {
      return buildClientAskFallback(question);
    }
    throw err;
  }
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  search: (query: string, filters: SearchFilters = {}, topK = 10) =>
    request<SearchResponse>("/api/v1/search", {
      method: "POST",
      body: JSON.stringify({ query, filters, top_k: topK, hybrid: true }),
    }),

  ask: (question: string, topK = 15) => requestAsk(question, topK),

  getReview: (id: string) => request<ReviewDetail>(`/api/v1/reviews/${id}`),

  listInsights: () => request<InsightListResponse>("/api/v1/insights"),

  refreshInsights: () =>
    request<InsightListResponse>("/api/v1/insights/refresh", { method: "POST" }),

  getInsight: (type: string, refresh = false) =>
    request<import("../types/api").Insight>(
      `/api/v1/insights/${type}${refresh ? "?refresh=true" : ""}`,
    ),

  listTopics: (limit = 20) => request<TopicsResponse>(`/api/v1/topics?limit=${limit}`),

  listSegments: () => request<SegmentsResponse>("/api/v1/segments"),

  exportJson: (reviewIds: string[]) =>
    request<ExportResponse>("/api/v1/export", {
      method: "POST",
      body: JSON.stringify({ format: "json", review_ids: reviewIds, include_enrichment: true }),
    }),

  exportCsv: async (reviewIds: string[]) => {
    const response = await fetch(`${API_BASE}/api/v1/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format: "csv", review_ids: reviewIds, include_enrichment: true }),
    });
    if (!response.ok) throw new Error("Export failed");
    return response.text();
  },
};
