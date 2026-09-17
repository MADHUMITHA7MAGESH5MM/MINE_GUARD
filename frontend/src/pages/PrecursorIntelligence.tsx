import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, ScatterChart, Scatter, ZAxis, LineChart, Line, Legend
} from "recharts";

const hazardFreq = [
  { name: "Confined Space", count: 34, sif: 28 },
  { name: "Working at Height", count: 41, sif: 19 },
  { name: "Hot Work", count: 22, sif: 8 },
  { name: "LOTO Bypass", count: 18, sif: 14 },
  { name: "H₂S Exposure", count: 27, sif: 22 },
  { name: "Dropped Object", count: 15, sif: 9 },
  { name: "Struck By", count: 12, sif: 5 },
  { name: "Driving", count: 9, sif: 3 },
];

const heatmapData = [
  { hazard: "Confined Space", noPermit: 28, noAtmTest: 24, noStandby: 21, badPPE: 18, noIsolation: 12 },
  { hazard: "Working at Height", noPermit: 18, noAtmTest: 0, noStandby: 0, badPPE: 22, noIsolation: 4 },
  { hazard: "Hot Work", noPermit: 19, noAtmTest: 14, noStandby: 8, badPPE: 6, noIsolation: 11 },
  { hazard: "H₂S Exposure", noPermit: 14, noAtmTest: 22, noStandby: 16, badPPE: 19, noIsolation: 5 },
  { hazard: "LOTO Bypass", noPermit: 16, noAtmTest: 0, noStandby: 0, badPPE: 4, noIsolation: 14 },
];

const barrierCols = ["noPermit", "noAtmTest", "noStandby", "badPPE", "noIsolation"];
const barrierLabels: Record<string, string> = {
  noPermit: "No PTW",
  noAtmTest: "No Atm. Test",
  noStandby: "No Standby",
  badPPE: "Inadequate PPE",
  noIsolation: "No Isolation",
};

const trend = [
  { month: "Mar", confined: 6, height: 9, hotwork: 4, h2s: 5 },
  { month: "Apr", confined: 8, height: 7, hotwork: 5, h2s: 7 },
  { month: "May", confined: 10, height: 11, hotwork: 3, h2s: 6 },
  { month: "Jun", confined: 7, height: 8, hotwork: 6, h2s: 8 },
  { month: "Jul", confined: 12, height: 14, hotwork: 4, h2s: 9 },
  { month: "Aug", confined: 9, height: 12, hotwork: 5, h2s: 7 },
  { month: "Sep", confined: 11, height: 14, hotwork: 4, h2s: 8 },
];

const insights = [
  { flag: "Top Precursor Combination", text: "Confined Space + No PTW is the most frequent SIF precursor pair this quarter — 28 co-occurrences across 6 sites.", severity: "critical" },
  { flag: "Trend Alert", text: "Working at Height incidents increased 18% compared to last month. Bombay High Offshore and Duliajan account for 74% of these.", severity: "high" },
  { flag: "Barrier Pattern", text: "Atmospheric Testing failure is present in 81% of all H₂S-related SIF-potential incidents — a systemic barrier gap.", severity: "high" },
  { flag: "Contractor Signal", text: "Contractor personnel are involved in 68% of all confined space SIF events. Consider enhanced PTW verification protocols for contract crews.", severity: "medium" },
];

const sevColor = (s: string) => s === "critical" ? "#DC2626" : s === "high" ? "#D97706" : "#3B82F6";
const sevBg = (s: string) => s === "critical" ? "rgba(220,38,38,0.08)" : s === "high" ? "rgba(217,119,6,0.08)" : "rgba(59,130,246,0.08)";

const cellColor = (v: number) => {
  if (v === 0) return "#0A1422";
  if (v < 8) return "rgba(59,130,246,0.25)";
  if (v < 16) return "rgba(217,119,6,0.35)";
  return "rgba(220,38,38,0.45)";
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded px-3 py-2 text-xs" style={{ background: "#0F1929", border: "1px solid rgba(255,255,255,0.1)" }}>
      <div className="font-semibold mb-1" style={{ color: "#8BA3C0" }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color || "#E8531D" }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
};

export default function PrecursorIntelligence() {
  return (
    <div className="flex flex-col gap-5 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
          Precursor Intelligence Engine
        </h1>
        <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
          Systemic pattern analysis across hazards, barrier failures, and SIF events · YTD 2024
        </p>
      </div>

      {/* Insights Banner */}
      <div className="grid grid-cols-2 gap-3">
        {insights.map((ins, i) => (
          <div key={i} className="rounded-lg p-4" style={{ background: sevBg(ins.severity), border: `1px solid ${sevColor(ins.severity)}25` }}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: sevColor(ins.severity) }} />
              <span className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: sevColor(ins.severity) }}>{ins.flag}</span>
            </div>
            <p className="text-xs leading-relaxed" style={{ color: "#8BA3C0" }}>{ins.text}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
        {/* Hazard Frequency */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="mb-4">
            <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>Hazard Frequency vs SIF Events</div>
            <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>Total reports vs SIF-flagged subset</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={hazardFreq} margin={{ top: 0, right: 0, left: -20, bottom: 0 }} barSize={14} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#4A6080", fontSize: 9 }} axisLine={false} tickLine={false} angle={-30} textAnchor="end" height={48} />
              <YAxis tick={{ fill: "#4A6080", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#1E3050" name="Total Reports" radius={[2, 2, 0, 0]} />
              <Bar dataKey="sif" fill="#DC2626" name="SIF Events" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="flex gap-4 mt-2 text-xs" style={{ color: "#4A6080" }}>
            <span className="flex items-center gap-1.5"><span className="w-3 h-2.5 rounded-sm inline-block" style={{ background: "#1E3050" }} />Total</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-2.5 rounded-sm inline-block bg-red-600" />SIF-Flagged</span>
          </div>
        </div>

        {/* Hazard Trend */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="mb-4">
            <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>Top Hazard Trend — 7 Months</div>
            <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>Monthly occurrence by hazard category</div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: "#4A6080", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#4A6080", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="confined" stroke="#DC2626" strokeWidth={2} dot={false} name="Confined Space" />
              <Line type="monotone" dataKey="height" stroke="#D97706" strokeWidth={2} dot={false} name="Working at Height" />
              <Line type="monotone" dataKey="h2s" stroke="#E8531D" strokeWidth={1.5} dot={false} name="H₂S Exposure" strokeDasharray="4 2" />
              <Line type="monotone" dataKey="hotwork" stroke="#3B82F6" strokeWidth={1.5} dot={false} name="Hot Work" strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Hazard × Barrier Failure Heatmap */}
      <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="mb-5">
          <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>Hazard × Barrier Failure Co-occurrence Matrix</div>
          <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>
            Cell intensity shows co-occurrence frequency — darker red = higher frequency = greater systemic risk
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="text-left pr-6 pb-3 font-medium" style={{ color: "#3A5570" }}>Hazard</th>
                {barrierCols.map(c => (
                  <th key={c} className="pb-3 text-center font-medium" style={{ color: "#3A5570", minWidth: 80 }}>
                    {barrierLabels[c]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {heatmapData.map((row, ri) => (
                <tr key={ri}>
                  <td className="pr-6 py-2 font-medium text-white whitespace-nowrap">{row.hazard}</td>
                  {barrierCols.map(c => {
                    const val = (row as any)[c] as number;
                    return (
                      <td key={c} className="py-2 text-center">
                        <div className="mx-auto rounded flex items-center justify-center w-16 h-9 text-xs font-semibold"
                          style={{
                            background: cellColor(val),
                            color: val === 0 ? "#2D4560" : val >= 16 ? "#FFD0C8" : val >= 8 ? "#FFE5B0" : "#B0C8FF",
                            fontFamily: "'JetBrains Mono', monospace",
                          }}>
                          {val === 0 ? "—" : val}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center gap-4 mt-4 text-[10px]" style={{ color: "#3A5570" }}>
          <span>Co-occurrence intensity:</span>
          {[
            { label: "None", bg: "#0A1422" },
            { label: "Low (1-7)", bg: "rgba(59,130,246,0.25)" },
            { label: "Medium (8-15)", bg: "rgba(217,119,6,0.35)" },
            { label: "High (16+)", bg: "rgba(220,38,38,0.45)" },
          ].map(l => (
            <span key={l.label} className="flex items-center gap-1.5">
              <span className="w-4 h-3 rounded-sm inline-block" style={{ background: l.bg, border: "1px solid rgba(255,255,255,0.08)" }} />
              {l.label}
            </span>
          ))}
        </div>
      </div>

      {/* Sankey-style flow visualization */}
      <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="mb-4">
          <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>Precursor → Barrier Failure → SIF Outcome Flow</div>
          <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>Simplified causal flow — width represents frequency of pathway</div>
        </div>
        <svg viewBox="0 0 900 280" className="w-full" style={{ minHeight: 200 }}>
          {/* Column labels */}
          {["PRECURSOR EVENTS", "BARRIER FAILURES", "SIF OUTCOMES"].map((label, i) => (
            <text key={label} x={[100, 450, 790][i]} y={20} textAnchor="middle"
              fill="#2D4560" fontSize="9" fontFamily="'JetBrains Mono', monospace" letterSpacing="1">
              {label}
            </text>
          ))}

          {/* Precursor nodes */}
          {[
            { label: "Confined Space", y: 60, h: 50, color: "#DC2626" },
            { label: "Working at Height", y: 120, h: 40, color: "#D97706" },
            { label: "H₂S Exposure", y: 170, h: 34, color: "#E8531D" },
            { label: "Hot Work", y: 214, h: 28, color: "#3B82F6" },
          ].map((n) => (
            <g key={n.label}>
              <rect x={20} y={n.y} width={160} height={n.h} rx={4} fill={`${n.color}20`} stroke={n.color} strokeWidth={1} />
              <text x={100} y={n.y + n.h / 2 + 4} textAnchor="middle" fill={n.color} fontSize="9.5" fontFamily="'Inter', sans-serif" fontWeight="500">{n.label}</text>
            </g>
          ))}

          {/* Barrier failure nodes */}
          {[
            { label: "No Work Permit", y: 50, h: 44, color: "#DC2626" },
            { label: "No Atmospheric Test", y: 104, h: 36, color: "#DC2626" },
            { label: "No Rescue Standby", y: 150, h: 32, color: "#D97706" },
            { label: "Inadequate PPE", y: 192, h: 30, color: "#D97706" },
            { label: "No LOTO", y: 232, h: 24, color: "#3B82F6" },
          ].map((n) => (
            <g key={n.label}>
              <rect x={370} y={n.y} width={160} height={n.h} rx={4} fill={`${n.color}15`} stroke={n.color} strokeWidth={1} />
              <text x={450} y={n.y + n.h / 2 + 4} textAnchor="middle" fill={n.color} fontSize="9.5" fontFamily="'Inter', sans-serif" fontWeight="500">{n.label}</text>
            </g>
          ))}

          {/* Outcome nodes */}
          {[
            { label: "Critical SIF Event", y: 70, h: 48, color: "#DC2626" },
            { label: "High SIF Potential", y: 130, h: 40, color: "#D97706" },
            { label: "Medium SIF Potential", y: 180, h: 32, color: "#3B82F6" },
          ].map((n) => (
            <g key={n.label}>
              <rect x={720} y={n.y} width={160} height={n.h} rx={4} fill={`${n.color}15`} stroke={n.color} strokeWidth={1} />
              <text x={800} y={n.y + n.h / 2 + 4} textAnchor="middle" fill={n.color} fontSize="9.5" fontFamily="'Inter', sans-serif" fontWeight="500">{n.label}</text>
            </g>
          ))}

          {/* Flow paths */}
          {[
            { x1: 180, y1: 85, x2: 370, y2: 72, w: 4, c: "#DC2626" },
            { x1: 180, y1: 85, x2: 370, y2: 122, w: 3, c: "#DC2626" },
            { x1: 180, y1: 140, x2: 370, y2: 206, w: 3, c: "#D97706" },
            { x1: 180, y1: 187, x2: 370, y2: 122, w: 2, c: "#E8531D" },
            { x1: 180, y1: 228, x2: 370, y2: 72, w: 2, c: "#3B82F6" },
            { x1: 530, y1: 72, x2: 720, y2: 94, w: 4, c: "#DC2626" },
            { x1: 530, y1: 122, x2: 720, y2: 94, w: 3, c: "#DC2626" },
            { x1: 530, y1: 166, x2: 720, y2: 150, w: 3, c: "#D97706" },
            { x1: 530, y1: 207, x2: 720, y2: 196, w: 2, c: "#D97706" },
            { x1: 530, y1: 244, x2: 720, y2: 196, w: 1.5, c: "#3B82F6" },
          ].map((f, i) => (
            <path key={i}
              d={`M ${f.x1} ${f.y1} C ${(f.x1 + f.x2) / 2} ${f.y1}, ${(f.x1 + f.x2) / 2} ${f.y2}, ${f.x2} ${f.y2}`}
              fill="none" stroke={f.c} strokeWidth={f.w} strokeOpacity={0.35}
            />
          ))}
        </svg>
      </div>
    </div>
  );
}
