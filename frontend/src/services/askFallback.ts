import type { AskResponse } from "../types/api";

function staticBullets(question: string): string[] {
  const q = question.toLowerCase();
  const bullets: string[] = [];
  if (q.includes("discover") || q.includes("new music")) {
    bullets.push(
      "Recommendation loops that replay familiar artists instead of surfacing new music",
      "Shuffle and autoplay behavior that feels repetitive",
      "Discover Weekly / Made For You playlists lacking variety",
    );
  }
  if (q.includes("recommend") || q.includes("frustration")) {
    bullets.push(
      "Irrelevant or overly narrow recommendations",
      "Suggested songs that do not match listening history",
      "Difficulty dismissing or tuning recommendations",
    );
  }
  if (q.includes("listen") || q.includes("behavior")) {
    bullets.push(
      "Queue control, shuffle, and replay expectations",
      "Playlist curation and skipping unwanted tracks",
      "Podcast vs music playback feature gaps",
    );
  }
  if (q.includes("same content") || q.includes("repeat") || q.includes("shuffle")) {
    bullets.push(
      "Shuffle algorithms playing the same subset of songs",
      "Feedback loops reinforcing already-popular tracks",
      "Limited true randomization in large libraries",
    );
  }
  if (q.includes("segment") || q.includes("user")) {
    bullets.push(
      "Free-tier users hitting ads and skip limits",
      "Premium users expecting better personalization",
      "Platform differences (mobile vs desktop vs car)",
    );
  }
  if (q.includes("unmet") || q.includes("need")) {
    bullets.push(
      "More control over recommendations and discovery",
      "Better offline, queue, and playback features",
      "Transparency in why specific songs are suggested",
    );
  }
  if (bullets.length === 0) {
    return [
      "Discovery and recommendation quality",
      "Playback control (shuffle, queue, skip)",
      "Ads, premium tiers, and feature gaps",
    ];
  }
  return [...new Set(bullets)].slice(0, 6);
}

export function buildClientAskFallback(question: string): AskResponse {
  const lines = staticBullets(question).map((item) => `- ${item}`).join("\n");
  return {
    question: question.trim(),
    answer:
      "**General product guidance** — the API could not be reached or returned an error " +
      "(often Gemini daily quota or a pending Railway deploy).\n\n" +
      `**Question:** ${question.trim()}\n\n` +
      "Typical themes in music streaming app research include:\n" +
      `${lines}\n\n` +
      "Try **Search** for raw review excerpts, or retry **Ask** in a few minutes.",
    confidence: "low",
    citations: [],
    related_insights: [],
    retrieval_count: 0,
    answer_mode: "general",
  };
}
