import { useEffect, useState } from "react";
import { listIncidents, ApiError, type IncidentResponse } from "@/lib/api";

type Props = {
  setSelectedIncidentId: (id: number) => void;
  setPage: (page: any) => void;
};

function riskBucket(prob: number): "critical" | "high" | "medium" | "low" {
  if (prob >= 0.85) return "critical";
  if (prob >= 0.65) return "high";
  if (prob >= 0.4) return "medium";
  return "low";
}

const riskStyle = (r: string) => {
  const map: Record<string, { color: string; bg: string }> = {
    critical: { color: "#DC2626", bg: "rgba(220,38,38,0.12)" },
    high: { color: "#D97706", bg: "rgba(217,119,6,0.12)" },
    medium: { color: "#3B82F6", bg: "rgba(59,130,246,0.12)" },
    low: { color: "#16A34A", bg: "rgba(22,163,74,0.12)" },
  };
  return map[r] || { color: "#5A7A9A", bg: "rgba(90,122,154,0.12)" };
};

function statusOf(inc: IncidentResponse): string {
  if (inc.sif_verdict === "REVIEW" && !inc.reviewed_by_human) {
    return "Pending Human Review";
  }

  if (inc.reviewed_by_human) {
    return inc.human_corrected_verdict ? "Overridden" : "Reviewed";
  }

  return "AI Classified";
}

const statusStyle = (s: string) => {
  if (s === "Pending Human Review") return { color: "#D97706" };
  if (s === "Overridden") return { color: "#3B82F6" };
  if (s === "Reviewed") return { color: "#16A34A" };
  return { color: "#5A7A9A" };
};

export default function IncidentRepository({
  setSelectedIncidentId,
  setPage,
}: Props) {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [filterRisk, setFilterRisk] = useState("All");
  const [filterSIF, setFilterSIF] = useState("All");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listIncidents({ limit: 200 })
      .then((data) => {
        if (!cancelled) {
          setIncidents(data);
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled)
          setError(
            e instanceof ApiError ? e.message : "Failed to load incidents."
          );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = incidents.filter((inc) => {
    const hazard = inc.hazards[0] || "";
    if (search) {
      const q = search.toLowerCase();
      const haystack = `${inc.id} ${inc.site ?? ""} ${hazard}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    if (
      filterRisk !== "All" &&
      riskBucket(inc.sif_probability) !== filterRisk.toLowerCase()
    )
      return false;
    
    // SIF Filter matching exact verdict status
    if (filterSIF === "HIGH SIF" && inc.sif_verdict !== "HIGH")
      return false;

    if (filterSIF === "REVIEW" && inc.sif_verdict !== "REVIEW")
      return false;

    if (filterSIF === "LOW SIF" && inc.sif_verdict !== "LOW")
      return false;
    return true;
  });

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1
            className="text-2xl font-semibold text-white"
            style={{ fontFamily: "'DM Sans', sans-serif" }}
          >
            Incident Repository
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
            {loading
              ? "Loading…"
              : `${incidents.length} records from the live database`}
          </p>
        </div>
      </div>

      {error && (
        <div
          className="text-xs rounded p-3"
          style={{
            background: "rgba(220,38,38,0.08)",
            color: "#DC2626",
            border: "1px solid rgba(220,38,38,0.25)",
          }}
        >
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <span
            className="absolute left-3 top-1/2 -translate-y-1/2 text-xs"
            style={{ color: "#3A5570" }}
          >
            ⌕
          </span>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ID, site, hazard..."
            className="w-full pl-7 pr-3 py-2 rounded text-sm outline-none"
            style={{
              background: "#0A1422",
              border: "1px solid rgba(255,255,255,0.07)",
              color: "#C4D5E5",
              fontFamily: "'Inter', sans-serif",
            }}
          />
        </div>
        {["All", "Critical", "High", "Medium", "Low"].map((r) => (
          <button
            key={r}
            onClick={() => setFilterRisk(r)}
            className="px-3 py-2 rounded text-xs font-medium transition-colors"
            style={{
              background:
                filterRisk === r ? "rgba(232,83,29,0.15)" : "#0A1422",
              color: filterRisk === r ? "#E8531D" : "#5A7A9A",
              border: `1px solid ${
                filterRisk === r
                  ? "rgba(232,83,29,0.3)"
                  : "rgba(255,255,255,0.07)"
              }`,
            }}
          >
            {r}
          </button>
        ))}
        <select
          value={filterSIF}
          onChange={(e) => setFilterSIF(e.target.value)}
          className="px-3 py-2 rounded text-xs outline-none"
          style={{
            background: "#0A1422",
            border: "1px solid rgba(255,255,255,0.07)",
            color: "#5A7A9A",
          }}
        >
          <option>All</option>
          <option>HIGH SIF</option>
          <option>REVIEW</option>
          <option>LOW SIF</option>

        </select>
      </div>

      {/* Table */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: "1px solid rgba(255,255,255,0.06)" }}
      >
        <table className="w-full text-xs">
          <thead>
            <tr
              style={{
                background: "#070F1A",
                borderBottom: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              {[
                "Report ID",
                "Date",
                "Site",
                "Source",
                "Primary Hazard",
                "Risk Level",
                "SIF Flag",
                "Status",
              ].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left font-medium uppercase tracking-widest"
                  style={{ color: "#2D4560", fontSize: "10px" }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={8}
                  className="text-center py-12 text-sm"
                  style={{ color: "#3A5570" }}
                >
                  Loading incidents…
                </td>
              </tr>
            ) : (
              filtered.map((inc, i) => {
                const rs = riskStyle(riskBucket(inc.sif_probability));
                const status = statusOf(inc);
                return (
                  <tr
                    key={inc.id}
                    onClick={() => {
                      setSelectedIncidentId(inc.id);
                      setPage("investigation");
                    }}
                    className="hover:bg-white/[0.02] cursor-pointer transition-colors"
                    style={{
                      borderBottom: "1px solid rgba(255,255,255,0.04)",
                      background: i % 2 === 0 ? "#0A1422" : "#080F1C",
                    }}
                  >
                    <td
                      className="px-4 py-3 font-medium"
                      style={{
                        color: "#E8531D",
                        fontFamily: "'JetBrains Mono', monospace",
                      }}
                    >
                      #{inc.id}
                    </td>
                    <td className="px-4 py-3" style={{ color: "#5A7A9A" }}>
                      {new Date(inc.submitted_at).toLocaleDateString("en-IN", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    <td className="px-4 py-3 font-medium text-white">
                      {inc.site || "—"}
                    </td>
                    <td className="px-4 py-3" style={{ color: "#7A9AB5" }}>
                      {inc.submitted_via}
                    </td>
                    <td className="px-4 py-3" style={{ color: "#C4D5E5" }}>
                      {inc.hazards[0] || "—"}
                      {inc.hazards.length > 1
                        ? ` +${inc.hazards.length - 1}`
                        : ""}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide"
                        style={{ background: rs.bg, color: rs.color }}
                      >
                        {riskBucket(inc.sif_probability)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {inc.sif_verdict === "HIGH" && (
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold"
                          style={{
                            background: "rgba(220,38,38,0.15)",
                            color: "#DC2626",
                          }}
                        >
                          HIGH
                        </span>
                      )}
                      {inc.sif_verdict === "REVIEW" && (
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold"
                          style={{
                            background: "rgba(217,119,6,0.15)",
                            color: "#D97706",
                          }}
                        >
                          REVIEW
                        </span>
                      )}
                      {inc.sif_verdict === "LOW" && (
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold"
                          style={{
                            background: "rgba(22,163,74,0.15)",
                            color: "#16A34A",
                          }}
                        >
                          LOW
                        </span>
                      )}
                      {!["HIGH", "REVIEW", "LOW"].includes(
                        inc.sif_verdict
                      ) && (
                        <span className="text-[10px]" style={{ color: "#2D4560" }}>
                          —
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="text-[11px] font-medium"
                        style={statusStyle(status)}
                      >
                        {status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td
                  colSpan={8}
                  className="text-center py-12 text-sm"
                  style={{ color: "#3A5570" }}
                >
                  No records match your filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!loading && (
        <div
          className="flex items-center justify-between text-xs"
          style={{ color: "#3A5570" }}
        >
          <span>
            Showing {filtered.length} of {incidents.length} records
          </span>
        </div>
      )}
    </div>
  );
}