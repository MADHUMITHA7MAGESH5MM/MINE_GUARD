import { useEffect, useState } from "react";
import { getIncident } from "@/lib/api";
import { exportDossierPDF } from "@/lib/export";
const TIMELINE = [
  { time: "13:45", event: "Shift handover completed — mud system maintenance task assigned to contractor crew", type: "context" },
  { time: "14:00", event: "Contractor crew M/s Bharat Services (2 persons) arrive at site and receive verbal briefing from crew lead", type: "context" },
  { time: "14:15", event: "Workers request Work Permit from shift supervisor — request noted but permit not formally issued", type: "barrier" },
  { time: "14:22", event: "Workers enter mud pit tank without valid PTW. No atmospheric testing conducted. Half-face respirators used", type: "critical" },
  { time: "14:30", event: "Safety Officer P. Borah discovers workers inside confined space during walkthrough. Immediate evacuation initiated", type: "discovery" },
  { time: "14:35", event: "Atmospheric reading taken: H₂S = 22 ppm (PEL: 10 ppm). Tank sealed and declared unsafe", type: "discovery" },
  { time: "14:40", event: "Emergency response team notified. Medical standby activated per site protocol", type: "response" },
  { time: "15:00", event: "Site management briefed. SIFORA report filed. AI classification complete: HIGH SIF POTENTIAL (94%)", type: "response" },
];

const CAUSES = {
  immediate: ["Entry into confined space without PTW", "No atmospheric testing before entry", "Inadequate PPE — half-face respirator used instead of SCBA"],
  underlying: ["Permit-to-Work system not enforced by shift supervisor", "Contractor crew unfamiliar with site confined space requirements", "No designated standby person assigned"],
  root: ["Insufficient contractor induction and PTW training", "Supervisory accountability gap for PTW issuance verification", "Safety culture: production pressure overriding permit compliance"],
};

const ACTIONS = [
  { id: "CA-01", action: "Mandatory re-induction of all contractor crews on Confined Space Entry procedures", owner: "HSE Manager", due: "19 Sep 2024", status: "In Progress" },
  { id: "CA-02", action: "Supervisor accountability training — PTW issuance verification added to shift handover checklist", owner: "Operations Lead", due: "30 Sep 2024", status: "Planned" },
  { id: "CA-03", action: "Deploy SCBA units and atmospheric monitors at all confined space entry points", owner: "Safety Officer", due: "22 Sep 2024", status: "Completed" },
  { id: "CA-04", action: "Audit all active PTW for confined space entries across Duliajan site", owner: "P. Borah", due: "15 Sep 2024", status: "Completed" },
];

const statusColor = (s: string) =>
  s === "Completed" ? "#16A34A" : s === "In Progress" ? "#D97706" : "#5A7A9A";

const typeStyle = (t: string) => {
  const map: Record<string, { color: string; dot: string }> = {
    critical: { color: "#DC2626", dot: "#DC2626" },
    barrier: { color: "#D97706", dot: "#D97706" },
    discovery: { color: "#E8531D", dot: "#E8531D" },
    response: { color: "#3B82F6", dot: "#3B82F6" },
    context: { color: "#5A7A9A", dot: "#2D4560" },
  };
  return map[t] || { color: "#5A7A9A", dot: "#2D4560" };
};

type Props = {
  incidentId: number | null;
};

export default function InvestigationDossier({ incidentId }: Props) {
  const [incident, setIncident] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "rca" | "actions">("timeline");

  useEffect(() => {
    if (incidentId === null || incidentId === undefined) return;

    getIncident(incidentId)
      .then(setIncident)
      .catch(console.error);
  }, [incidentId]);

  if (!incident) {
    return (
      <div className="p-6 text-white">
        Loading incident...
      </div>
    );
  }

  return (
    <div id="dossier-report"className="flex flex-col gap-5 p-6">
       <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Investigation Dossier
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
            Case #{incident.id} · {incident.site} · {Math.round(incident.sif_probability * 100)}% confidence
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1.5 rounded font-medium"
            style={{ background: "rgba(220,38,38,0.1)", color: "#DC2626", border: "1px solid rgba(220,38,38,0.25)" }}>
            {incident?.sif_verdict}
          </span>
          <button className="px-4 py-1.5 rounded text-xs font-medium text-white"
            style={{ background: "#1E2F47", border: "1px solid rgba(255,255,255,0.08)" }}
            onClick={exportDossierPDF}>
            Export PDF
          </button>
        </div>
      </div>

      {/* Case summary strip */}
      <div className="grid grid-cols-5 gap-3">
        {[
          {
            label: "Case Type",
            value: incident.sif_verdict === "HIGH" ? "SIF Potential" : "Non-SIF"
          },
          { label: "Site", value: incident.site || "Unknown" },
          { label: "Persons Involved", value: "2 (Contractor)" },
          { label: "Injuries", value: "None Reported" },
          { label: "Investigation Lead", value: "P. Borah (Safety Officer)" },
        ].map(f => (
          <div key={f.label} className="rounded p-3" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.05)" }}>
            <div className="text-[10px] uppercase tracking-wide mb-1" style={{ color: "#3A5570" }}>{f.label}</div>
            <div className="text-xs font-medium text-white">{f.value}</div>
          </div>
        ))}
      </div>

      {/* AI Extracted Entities */}
      <div
        className="rounded-lg p-4"
        style={{
          background: "#0A1422",
          border: "1px solid rgba(255,255,255,0.06)"
        }}>
        <div className="text-xs font-semibold text-white mb-3">
          AI Extracted Entities
        </div>

        <div className="flex flex-wrap gap-2">
          {incident.hazards?.map((h: string) => (
            <span
              key={h}
              className="px-2 py-1 rounded text-xs"
              style={{
                background: "rgba(220,38,38,0.15)",
                color: "#F87171"
              }}
            >
              {h}
            </span>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
        {[
          { id: "timeline", label: "Event Timeline" },
          { id: "rca", label: "Root Cause Analysis" },
          { id: "actions", label: "Corrective Actions" },
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id as any)}
            className="px-4 py-2.5 text-xs font-medium transition-colors"
            style={{
              color: activeTab === t.id ? "#E8531D" : "#5A7A9A",
              borderBottom: activeTab === t.id ? "2px solid #E8531D" : "2px solid transparent",
              marginBottom: -1,
            }}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: activeTab === "rca" ? "1fr" : "2fr 1fr" }}>
        <div>
          {/* Timeline */}
          {activeTab === "timeline" && (
            <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-sm font-semibold text-white mb-4" style={{ fontFamily: "'DM Sans', sans-serif" }}>Reconstructed Event Sequence</div>
              <div className="space-y-0">
                {TIMELINE.map((evt, i) => {
                  const style = typeStyle(evt.type);
                  return (
                    <div key={i} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="w-3 h-3 rounded-full border-2 flex-shrink-0 mt-0.5"
                          style={{ borderColor: style.dot, background: evt.type === "critical" ? style.dot : "transparent" }} />
                        {i < TIMELINE.length - 1 && <div className="w-px flex-1 my-1" style={{ background: "rgba(255,255,255,0.06)" }} />}
                      </div>
                      <div className="pb-4">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="text-[11px] font-bold" style={{ color: style.dot, fontFamily: "'JetBrains Mono', monospace" }}>
                            {evt.time}
                          </span>
                          {evt.type === "critical" && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded uppercase font-semibold"
                              style={{ background: "rgba(220,38,38,0.15)", color: "#DC2626" }}>
                              Critical Act
                            </span>
                          )}
                          {evt.type === "barrier" && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded uppercase font-semibold"
                              style={{ background: "rgba(217,119,6,0.15)", color: "#D97706" }}>
                              Barrier Failure
                            </span>
                          )}
                        </div>
                        <p className="text-xs leading-relaxed" style={{ color: "#7A9AB5" }}>{evt.event}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* RCA */}
          {activeTab === "rca" && (
            <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-sm font-semibold text-white mb-5" style={{ fontFamily: "'DM Sans', sans-serif" }}>Root Cause Analysis — 3-Layer Model</div>
              <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
                {[
                  { label: "Immediate Causes", items: CAUSES.immediate, color: "#DC2626", desc: "Direct acts and conditions" },
                  { label: "Underlying Causes", items: CAUSES.underlying, color: "#D97706", desc: "System and process failures" },
                  { label: "Root Causes", items: CAUSES.root, color: "#E8531D", desc: "Organizational and cultural factors" },
                ].map(col => (
                  <div key={col.label}>
                    <div className="mb-3">
                      <div className="text-xs font-semibold mb-0.5" style={{ color: col.color }}>{col.label}</div>
                      <div className="text-[10px]" style={{ color: "#3A5570" }}>{col.desc}</div>
                    </div>
                    <div className="space-y-2">
                      {col.items.map((item, i) => (
                        <div key={i} className="rounded p-3 text-[11px] leading-relaxed"
                          style={{ background: `${col.color}0D`, border: `1px solid ${col.color}25`, color: "#8BA3C0" }}>
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* AI Recommendation */}
              <div className="mt-5 rounded-lg p-4" style={{ background: "rgba(232,83,29,0.06)", border: "1px solid rgba(232,83,29,0.2)" }}>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-5 h-5 rounded flex items-center justify-center text-white text-[10px] font-bold"
                    style={{ background: "#E8531D" }}>
                    AI
                  </div>
                  <span className="text-xs font-semibold" style={{ color: "#E8531D" }}>SIFORA AI Recommendation</span>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "#7A9AB5" }}>
                  This incident is structurally similar to 7 prior confined space events across the OIL India network (2021–2024), all involving contractor personnel and PTW non-compliance. Systemic resolution requires embedding PTW verification into contractor access control — workers should not be able to physically enter confined space zones without digital permit confirmation. A technology-enforced barrier (e.g., badge access + PTW system integration) would prevent recurrence more reliably than training alone.
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          {activeTab === "actions" && (
            <div className="rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ background: "#070F1A", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    {["ID", "Corrective Action", "Owner", "Due Date", "Status"].map(h => (
                      <th key={h} className="px-4 py-3 text-left font-medium uppercase tracking-widest"
                        style={{ color: "#2D4560", fontSize: "10px" }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ACTIONS.map((a, i) => (
                    <tr key={a.id} style={{ background: i % 2 === 0 ? "#0A1422" : "#080F1C", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: "#E8531D", fontFamily: "'JetBrains Mono', monospace" }}>{a.id}</td>
                      <td className="px-4 py-3" style={{ color: "#C4D5E5", maxWidth: 300 }}>{a.action}</td>
                      <td className="px-4 py-3" style={{ color: "#7A9AB5" }}>{a.owner}</td>
                      <td className="px-4 py-3 font-mono text-xs" style={{ color: "#5A7A9A", fontFamily: "'JetBrains Mono', monospace" }}>{a.due}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-medium" style={{ color: statusColor(a.status) }}>{a.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Sidebar */}
        {activeTab !== "rca" && (
          <div className="flex flex-col gap-3">
            <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-xs font-semibold text-white mb-3">Contributing Factors</div>
              <div className="space-y-2">
                {[
                  { factor: "Time pressure — maintenance backlog", weight: 78 },
                  { factor: "Contractor unfamiliarity with site", weight: 91 },
                  { factor: "Supervisor complacency", weight: 65 },
                  { factor: "H₂S awareness gap", weight: 57 },
                ].map(f => (
                  <div key={f.factor}>
                    <div className="flex justify-between text-[11px] mb-1">
                      <span style={{ color: "#7A9AB5" }}>{f.factor}</span>
                      <span style={{ color: "#D97706", fontFamily: "'JetBrains Mono', monospace" }}>{f.weight}%</span>
                    </div>
                    <div className="h-1 rounded-full" style={{ background: "rgba(255,255,255,0.05)" }}>
                      <div className="h-full rounded-full" style={{ width: `${f.weight}%`, background: "#D97706" }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-xs font-semibold text-white mb-3">Reviewer Comments</div>
              <div className="space-y-3">
                {[
                  { author: "P. Borah", time: "12 Sep, 15:30", text: "Confirmed: no PTW was issued. Supervisor has been interviewed. Verbal instruction given but permit not formally processed." },
                  { author: "R. Sharma", time: "12 Sep, 17:00", text: "AI classification confirmed. Escalating to site GM. Corrective actions initiated." },
                ].map((c, i) => (
                  <div key={i} className="rounded p-3" style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] font-medium text-white">{c.author}</span>
                      <span className="text-[10px]" style={{ color: "#3A5570", fontFamily: "'JetBrains Mono', monospace" }}>{c.time}</span>
                    </div>
                    <p className="text-[11px] leading-relaxed" style={{ color: "#6B8AAA" }}>{c.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}