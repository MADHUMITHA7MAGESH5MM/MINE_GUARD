import { useState } from "react";
import Sidebar from "./components/Sidebar";
import CommandCenter from "./pages/CommandCenter";
import AIAnalysis from "./pages/AIAnalysis";
import IncidentRepository from "./pages/IncidentRepository";
import HumanReview from "./pages/HumanReview";
import PrecursorIntelligence from "./pages/PrecursorIntelligence";
import Analytics from "./pages/Analytics";
import InvestigationDossier from "./pages/InvestigationDossier";
import FatalitySimulator from "./pages/FatalitySimulator";
import SiteDigitalTwin from "./pages/SiteDigitalTwin";

export type Page =
  | "command"
  | "ai-analysis"
  | "repository"
  | "review"
  | "precursor"
  | "analytics"
  | "investigation"
  | "simulator"
  | "digital-twin";

type StandardPage = Exclude<Page, "repository" | "investigation">;

const PAGE_MAP: Record<StandardPage, React.ComponentType> = {
  command: CommandCenter,
  "ai-analysis": AIAnalysis,
  review: HumanReview,
  precursor: PrecursorIntelligence,
  analytics: Analytics,
  simulator: FatalitySimulator,
  "digital-twin": SiteDigitalTwin,
};

export default function App() {
  const [page, setPage] = useState<Page>("command");
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(null);

  const PageComponent =
    page !== "repository" && page !== "investigation"
      ? PAGE_MAP[page]
      : null;

  return (
    <div className="flex min-h-screen" style={{ background: "#040B18" }}>
      <Sidebar page={page} setPage={setPage} />

      <main className="flex-1 overflow-y-auto" style={{ maxHeight: "100vh" }}>
        {page === "repository" ? (
          <IncidentRepository
            setSelectedIncidentId={setSelectedIncidentId}
            setPage={setPage}
          />
        ) : page === "investigation" ? (
          <InvestigationDossier incidentId={selectedIncidentId} />
        ) : PageComponent ? (
          <PageComponent />
        ) : null}
      </main>
    </div>
  );
}