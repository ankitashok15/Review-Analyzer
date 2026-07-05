export interface SearchFilters {
  source?: string | null;
  platform?: string | null;
  sentiment?: string | null;
  min_rating?: number | null;
  max_rating?: number | null;
}

export interface SearchResult {
  review_id: string;
  score: number;
  excerpt: string;
  highlight_offsets: number[];
  source: string;
  platform: string;
  rating: number | null;
  review_date: string;
  source_url?: string | null;
  sentiment?: string | null;
  primary_topic?: string | null;
  summary?: string | null;
}

export interface SearchResponse {
  query: string;
  count: number;
  results: SearchResult[];
}

export interface Citation {
  review_id: string;
  excerpt: string;
  source: string;
  relevance_score: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  confidence: "high" | "medium" | "low";
  citations: Citation[];
  related_insights: string[];
  retrieval_count: number;
  answer_mode?: "grounded" | "general";
}

export interface Enrichment {
  sentiment?: string | null;
  primary_topic?: string | null;
  pain_point?: string | null;
  feature_request?: string | null;
  user_segment?: string | null;
  summary?: string | null;
  keywords?: string[];
}

export interface ReviewDetail {
  id: string;
  source: string;
  source_id: string;
  source_url?: string | null;
  app_name: string;
  platform: string;
  rating: number | null;
  title?: string | null;
  body: string;
  language: string;
  review_date: string;
  ingested_at: string;
  enrichment?: Enrichment | null;
}

export interface Insight {
  insight_type: string;
  title: string;
  summary: string;
  evidence_review_ids: string[];
  metrics: Record<string, unknown>;
  generated_at: string;
  cache_key: string;
}

export interface InsightListResponse {
  count: number;
  insights: Insight[];
}

export interface TopicCluster {
  topic: string;
  count: number;
  evidence_review_ids: string[];
}

export interface TopicsResponse {
  count: number;
  topics: TopicCluster[];
}

export interface SegmentRow {
  user_segment: string | null;
  sentiment: string | null;
  count: number;
  evidence_review_ids: string[];
}

export interface SegmentsResponse {
  count: number;
  segments: SegmentRow[];
}

export interface ExportRow {
  review_id: string;
  source: string;
  platform: string;
  rating: number | null;
  review_date: string;
  body: string;
  sentiment?: string | null;
  primary_topic?: string | null;
}

export interface ExportResponse {
  format: string;
  count: number;
  rows: ExportRow[];
}
