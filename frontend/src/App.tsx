import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AskPage } from "./pages/Ask";
import { ExportPage } from "./pages/Export";
import { InsightsPage } from "./pages/Insights";
import { ReviewDetailPage } from "./pages/ReviewDetail";
import { SearchPage } from "./pages/Search";
import { SegmentsPage } from "./pages/Segments";
import { TopicsPage } from "./pages/Topics";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<SearchPage />} />
          <Route path="ask" element={<AskPage />} />
          <Route path="insights" element={<InsightsPage />} />
          <Route path="topics" element={<TopicsPage />} />
          <Route path="segments" element={<SegmentsPage />} />
          <Route path="export" element={<ExportPage />} />
          <Route path="reviews/:id" element={<ReviewDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
