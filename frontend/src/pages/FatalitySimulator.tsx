import { useState } from "react";

const CONTROLS = [
  { id: "ptw", label: "Work Permit (PTW)", description: "Valid PTW issued and verified before entry", riskReduction: 18, category: "Administrative" },
  { id: "atmtest", label: "Atmospheric Testing", description: "Pre-entry and continuous atmospheric monitoring", riskReduction: 22, category: "Technical" },
  { id: "scba", label: "Supplied-Air Breathing Apparatus", description: "SCBA instead of half-face respirator", riskReduction: 14, category: "PPE" },
  { id: "standby", label: "Rescue Standby Team", description: "Trained standby with rescue equipment outside", riskReduction: 12, category: "Emergency" },
  { id: "isolation", label: "Energy Isolation (LOTO)", description: "Full lockout/tagout of all energy sources", riskReduction: 8, category: "Technical" },
  { id: "supervisor", label: "Competent Supervision", description: "Qualified supervisor present and monitoring", riskReduction: 7, category: "Administrative" },
  { id: "induction", label: "Confined Space Induction", description: "Formal training completed within 12 months", riskReduction: 5, category: "Training" },
];

const BASE_RISK = 92;

const categoryColor = (c: string) => {
  const map: Record<string, string> = {
    Administrative: "#3B82F6",
    Technical: "#D97706",
    PPE: "#E8531D",
    Emergency: "#DC2626",
    Training: "#16A34A",
  };
  return map[c] || "#5A7A9A";
};

const riskLevel = (r: number) => {
  if (r >= 70) return { label: "CRITICAL", color: "#DC2626" };
  if (r >= 40) return { label: "HIGH", color: "#D97706" };
  if (r >= 20) return { label: "MEDIUM", color: "#E8531D" };
  if (r >= 10) return { label: "LOW", color: "#3B82F6" };
  return { label: "MITIGATED", color: "#16A34A" };
};

export default function FatalitySimulator() {
  const [enabled, setEnabled] = useState<Set<string>>(new Set());

  const totalReduction = CONTROLS.filter(c => enabled.has(c.id))
    .reduce((sum, c) => sum + c.riskReduction, 0);

  const currentRisk = Math.max(4, BASE_RISK - totalReduction);
  const { label: riskLabel, color: riskColor } = riskLevel(currentRisk);

  const toggle = (id: string) => {
    setEnabled(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const saved = BASE_RISK - currentRisk;
  const circumference = 2 * Math.PI * 60;
  const offset = circumference * (1 - currentRisk / 100);

  return (
    <div className="flex flex-col gap-5 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
          Fatality Prevention Simulator
        </h1>
        <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
          Toggle safety controls to see how predicted fatality risk changes — Scenario: Confined Space Entry, Mud Pit Tank, Duliajan
        </p>
      </div>

      <div className="grid gap-5" style={{ gridTemplateColumns: "1fr 360px" }}>
        {/* Controls panel */}
        <div className="flex flex-col gap-3">
          <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-sm font-semibold text-white mb-1" style={{ fontFamily: "'DM Sans', sans-serif" }}>Safety Control Toggles</div>
            <p className="text-xs mb-4" style={{ color: "#5A7A9A" }}>
              Enable or disable safety barriers to simulate their protective effect on fatality probability.
            </p>
            <div className="space-y-2.5">
              {CONTROLS.map(ctrl => {
                const active = enabled.has(ctrl.id);
                const cc = categoryColor(ctrl.category);
                return (
                  <div
                    key={ctrl.id}
                    onClick={() => toggle(ctrl.id)}
                    className="flex items-center gap-4 rounded-lg px-4 py-3.5 cursor-pointer transition-all"
                    style={{
                      background: active ? `${cc}10` : "#070F1A",
                      border: `1px solid ${active ? cc + "40" : "rgba(255,255,255,0.06)"}`,
                    }}
                  >
                    {/* Toggle */}
                    <div className="flex-shrink-0 w-9 h-5 rounded-full transition-colors flex items-center px-0.5"
                      style={{ background: active ? cc : "#1E2F47" }}>
                      <div className="w-4 h-4 rounded-full bg-white shadow transition-transform"
                        style={{ transform: active ? "translateX(16px)" : "translateX(0)" }} />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium" style={{ color: active ? "#FFFFFF" : "#7A9AB5" }}>{ctrl.label}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded font-medium"
                          style={{ background: `${cc}15`, color: cc }}>{ctrl.category}</span>
                      </div>
                      <div className="text-[11px] mt-0.5" style={{ color: "#4A6080" }}>{ctrl.description}</div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-sm font-semibold" style={{ color: active ? "#16A34A" : "#3A5570", fontFamily: "'JetBrains Mono', monospace" }}>
                        -{ctrl.riskReduction}%
                      </div>
                      <div className="text-[10px]" style={{ color: "#3A5570" }}>risk reduction</div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-2 mt-3">
              <button onClick={() => setEnabled(new Set(CONTROLS.map(c => c.id)))}
                className="flex-1 py-2 rounded text-xs font-medium transition-colors"
                style={{ background: "rgba(22,163,74,0.1)", color: "#16A34A", border: "1px solid rgba(22,163,74,0.25)" }}>
                Enable All Controls
              </button>
              <button onClick={() => setEnabled(new Set())}
                className="flex-1 py-2 rounded text-xs font-medium transition-colors"
                style={{ background: "rgba(220,38,38,0.08)", color: "#DC2626", border: "1px solid rgba(220,38,38,0.2)" }}>
                Remove All Controls
              </button>
            </div>
          </div>
        </div>

        {/* Risk readout */}
        <div className="flex flex-col gap-3">
          {/* Gauge */}
          <div className="rounded-lg p-5 flex flex-col items-center" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-xs font-semibold mb-4 text-center" style={{ color: "#5A7A9A" }}>
              Predicted Fatality Risk
            </div>
            <div className="relative">
              <svg width="160" height="160" viewBox="0 0 160 160">
                <circle cx="80" cy="80" r="60" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
                <circle
                  cx="80" cy="80" r="60"
                  fill="none" stroke={riskColor}
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                  transform="rotate(-90 80 80)"
                  style={{ transition: "stroke-dashoffset 0.6s ease, stroke 0.4s ease" }}
                />
                <text x="80" y="76" textAnchor="middle" fill="white" fontSize="28" fontWeight="700"
                  fontFamily="'JetBrains Mono', monospace" style={{ transition: "all 0.3s" }}>
                  {currentRisk}%
                </text>
                <text x="80" y="96" textAnchor="middle" fill={riskColor} fontSize="9" fontWeight="600" letterSpacing="1"
                  fontFamily="'Inter', sans-serif">
                  {riskLabel}
                </text>
              </svg>
            </div>

            <div className="w-full mt-4 space-y-2">
              <div className="flex justify-between text-xs">
                <span style={{ color: "#5A7A9A" }}>Baseline (no controls)</span>
                <span style={{ color: "#DC2626", fontFamily: "'JetBrains Mono', monospace" }}>{BASE_RISK}%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span style={{ color: "#5A7A9A" }}>Current risk</span>
                <span style={{ color: riskColor, fontFamily: "'JetBrains Mono', monospace" }}>{currentRisk}%</span>
              </div>
              <div className="h-px w-full" style={{ background: "rgba(255,255,255,0.06)" }} />
              <div className="flex justify-between text-xs font-semibold">
                <span style={{ color: "#16A34A" }}>Risk prevented</span>
                <span style={{ color: "#16A34A", fontFamily: "'JetBrains Mono', monospace" }}>{saved} pts ({Math.round(saved / BASE_RISK * 100)}%)</span>
              </div>
            </div>
          </div>

          {/* Control summary */}
          <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-xs font-semibold text-white mb-3">Active Barriers ({enabled.size}/{CONTROLS.length})</div>
            {enabled.size === 0 ? (
              <div className="text-center py-4 text-xs" style={{ color: "#2D4560" }}>
                No barriers active — maximum fatality risk
              </div>
            ) : (
              <div className="space-y-1.5">
                {CONTROLS.filter(c => enabled.has(c.id)).map(c => (
                  <div key={c.id} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2" style={{ color: "#7A9AB5" }}>
                      <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#16A34A" }} />
                      {c.label}
                    </span>
                    <span style={{ color: "#16A34A", fontFamily: "'JetBrains Mono', monospace" }}>-{c.riskReduction}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Scenario context */}
          <div className="rounded-lg p-4" style={{ background: "rgba(232,83,29,0.06)", border: "1px solid rgba(232,83,29,0.15)" }}>
            <div className="text-[10px] uppercase tracking-widest mb-2 font-semibold" style={{ color: "#E8531D" }}>
              Scenario Context
            </div>
            <p className="text-[11px] leading-relaxed" style={{ color: "#7A9AB5" }}>
              Confined space entry into a mud pit tank with H₂S present at 22 ppm. Two contractor workers.
              Based on 47 similar incidents in OIL India SIF database and IOGP global statistics.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
