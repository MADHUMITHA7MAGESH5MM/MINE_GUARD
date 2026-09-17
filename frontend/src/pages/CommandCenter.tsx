import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from "recharts";

const riskTrend = [
  { month: "Mar", sif: 12, near: 34, unsafe: 67 },
  { month: "Apr", sif: 9, near: 29, unsafe: 71 },
  { month: "May", sif: 15, near: 41, unsafe: 58 },
  { month: "Jun", sif: 7, near: 38, unsafe: 63 },
  { month: "Jul", sif: 18, near: 52, unsafe: 82 },
  { month: "Aug", sif: 11, near: 44, unsafe: 74 },
  { month: "Sep", sif: 14, near: 48, unsafe: 69 },
];

const sites = [
  { id: "DIG-01", name: "Duliajan Drilling Complex", risk: "critical", score: 87, incidents: 12, lat: 65, lng: 72 },
  { id: "REF-02", name: "Numaligarh Refinery", risk: "high", score: 64, incidents: 7, lat: 35, lng: 58 },
  { id: "PPL-03", name: "Jorhat Pipeline Station", risk: "high", score: 61, incidents: 5, lat: 48, lng: 78 },
  { id: "TKF-04", name: "Digboi Tank Farm", risk: "medium", score: 42, incidents: 3, lat: 22, lng: 45 },
  { id: "NHK-05", name: "Naharkatiya Production Facility", risk: "critical", score: 91, incidents: 15, lat: 75, lng: 32 },
  { id: "PRO-06", name: "Moran Processing Unit", risk: "medium", score: 38, incidents: 2, lat: 55, lng: 62 },
];

const alerts = [
  { time: "09:14", site: "Naharkatiya Production Facility", type: "CRITICAL", msg: "Confined space entry without PTW detected — Gas Compression Unit-2", color: "#DC2626" },
  { time: "09:02", site: "Duliajan Drilling", type: "HIGH", msg: "High H₂S concentration reported near wellhead DU-12", color: "#D97706" },
  { time: "08:51", site: "Numaligarh Refinery", type: "HIGH", msg: "Working at height without fall arrest — Tank T-07 maintenance", color: "#D97706" },
  { time: "08:33", site: "Jorhat Pipeline", type: "MEDIUM", msg: "Hot work permit expired — Section KM 142.3", color: "#E8531D" },
  { time: "08:19", site: "Digboi Tank Farm", type: "LOW", msg: "Housekeeping deficiency observed at pumping station", color: "#4A6080" },
  { time: "07:58", site: "Moran Processing Unit", type: "MEDIUM", msg: "LOTO procedure deviation reported by shift supervisor", color: "#E8531D" },
];

const kpis = [
  { label: "Total Incidents YTD", value: "1001", delta: "+12%", up: true },
  { label: "High-SIF Cases", value: "248", delta: "+3 this week", up: true },
  { label: "Pending Reviews", value: "17", delta: "6 overdue", up: true },
  { label: "Fatality Prevention Score", value: "55.8", delta: "+2.1 pts", up: false, unit: "/100" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded px-3 py-2 text-xs" style={{ background: "#0F1929", border: "1px solid rgba(255,255,255,0.1)" }}>
      <div className="font-semibold mb-1" style={{ color: "#8BA3C0" }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color }}>{p.name}: {p.value}</div>
      ))}
    </div>
  );
};

export default function CommandCenter() {
  const riskColor = (r: string) =>
    r === "critical" ? "#DC2626" : r === "high" ? "#D97706" : "#3B82F6";

  return (
    <div className="flex flex-col gap-6 p-6 min-h-full">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Safety Command Center
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
            Real-time operational overview · OIL India field network · {new Date().toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs px-3 py-1.5 rounded"
          style={{ background: "rgba(220,38,38,0.1)", border: "1px solid rgba(220,38,38,0.25)", color: "#DC2626" }}>
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse inline-block" />
          LIVE · 6 active alerts
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-lg px-5 py-4"
            style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-xs uppercase tracking-widest font-medium mb-2" style={{ color: "#3A5570" }}>{k.label}</div>
            <div className="flex items-end gap-2">
              <span className="text-3xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                {k.value}
              </span>
              {k.unit && <span className="text-base mb-0.5" style={{ color: "#3A5570" }}>{k.unit}</span>}
            </div>
            <div className="mt-1.5 text-xs font-medium" style={{ fontFamily: "'JetBrains Mono', monospace", color: k.up ? "#D97706" : "#16A34A" }}>
              {k.delta}
            </div>
          </div>
        ))}
      </div>

      {/* Main content grid */}
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 360px" }}>
        {/* Risk Trend Chart */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>SIF Precursor Trend</div>
              <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>Rolling 7-month view — SIF events, near-misses, unsafe conditions</div>
            </div>
            <div className="flex items-center gap-4 text-xs" style={{ color: "#5A7A9A" }}>
              <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-red-500 inline-block rounded" />SIF Events</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block rounded" style={{ background: "#D97706" }} />Near-Miss</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 inline-block rounded" style={{ background: "#3B82F6" }} />Unsafe Acts</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={riskTrend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="sifGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#DC2626" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#DC2626" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="nearGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#D97706" stopOpacity={0.12} />
                  <stop offset="95%" stopColor="#D97706" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="unsafeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: "#4A6080", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#4A6080", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="unsafe" stroke="#3B82F6" strokeWidth={1.5} fill="url(#unsafeGrad)" name="Unsafe Acts" />
              <Area type="monotone" dataKey="near" stroke="#D97706" strokeWidth={1.5} fill="url(#nearGrad)" name="Near-Miss" />
              <Area type="monotone" dataKey="sif" stroke="#DC2626" strokeWidth={2} fill="url(#sifGrad)" name="SIF Events" />
              <ReferenceLine y={10} stroke="rgba(220,38,38,0.3)" strokeDasharray="4 4" label={{ value: "Threshold", fill: "#DC2626", fontSize: 10, position: "insideTopRight" }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Live Alert Stream */}
        <div className="rounded-lg flex flex-col" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="px-5 pt-5 pb-3 border-b" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
            <div className="flex items-center justify-between">
              <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>Live Alert Stream</div>
              <span className="text-[10px] px-2 py-0.5 rounded font-medium" style={{ background: "rgba(220,38,38,0.15)", color: "#DC2626" }}>
                LIVE
              </span>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto">
            {alerts.map((a, i) => (
              <div key={i} className="px-4 py-3 hover:bg-white/[0.02] transition-colors"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-semibold font-mono"
                    style={{ background: `${a.color}18`, color: a.color, fontFamily: "'JetBrains Mono', monospace" }}>
                    {a.type}
                  </span>
                  <span className="text-[10px]" style={{ color: "#3A5570", fontFamily: "'JetBrains Mono', monospace" }}>{a.time}</span>
                </div>
                <div className="text-xs font-medium text-white mb-0.5">{a.site}</div>
                <div className="text-[11px] leading-relaxed" style={{ color: "#5A7A9A" }}>{a.msg}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Site Risk Map */}
      <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>Site Risk Map</div>
            <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>Interactive operational footprint — India field network</div>
          </div>
          <div className="flex items-center gap-4 text-xs" style={{ color: "#5A7A9A" }}>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />Critical</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full inline-block" style={{ background: "#D97706" }} />High</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />Medium</span>
          </div>
        </div>
        <div className="flex gap-4">
          {/* Map area */}
          <div className="flex-1 rounded relative overflow-hidden"
            style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.06)", minHeight: 220 }}>
            {/* Simplified India outline SVG */}
            <svg viewBox="0 0 500 380" className="w-full h-full" style={{ minHeight: 220 }}>
              <path
                d="M 120 40 L 180 30 L 260 35 L 320 55 L 370 90 L 390 140 L 400 190 L 380 240 L 340 290 L 300 340 L 260 370 L 240 360 L 200 320 L 170 280 L 140 240 L 110 200 L 95 160 L 100 110 L 120 70 Z"
                fill="rgba(30,47,71,0.5)" stroke="rgba(255,255,255,0.06)" strokeWidth="1.5"
              />
              {/* Grid lines */}
              {[100, 150, 200, 250, 300, 350].map(y => (
                <line key={y} x1="80" y1={y} x2="420" y2={y} stroke="rgba(255,255,255,0.025)" strokeWidth="0.5" />
              ))}
              {[120, 180, 240, 300, 360].map(x => (
                <line key={x} x1={x} y1="20" x2={x} y2="380" stroke="rgba(255,255,255,0.025)" strokeWidth="0.5" />
              ))}
              {/* Site nodes */}
              {sites.map((s) => {
                const c = riskColor(s.risk);
                return (
                  <g key={s.id}>
                    <circle cx={s.lng * 4.5 + 60} cy={s.lat * 4.0 + 30} r={s.risk === "critical" ? 10 : 7}
                      fill={`${c}25`} stroke={c} strokeWidth={1.5} />
                    <circle cx={s.lng * 4.5 + 60} cy={s.lat * 4.0 + 30} r={3} fill={c} />
                    {s.risk === "critical" && (
                      <circle cx={s.lng * 4.5 + 60} cy={s.lat * 4.0 + 30} r={14}
                        fill="none" stroke={c} strokeWidth={1} opacity={0.4}>
                        <animate attributeName="r" from="8" to="18" dur="2s" repeatCount="indefinite" />
                        <animate attributeName="opacity" from="0.4" to="0" dur="2s" repeatCount="indefinite" />
                      </circle>
                    )}
                    <text x={s.lng * 4.5 + 70} y={s.lat * 4.0 + 35} fill={c} fontSize="9"
                      fontFamily="'JetBrains Mono', monospace">{s.id}</text>
                  </g>
                );
              })}
            </svg>
          </div>
          {/* Site list */}
          <div className="w-80 space-y-1.5">
            {sites.map((s) => (
              <div key={s.id} className="flex items-center gap-3 px-3 py-2 rounded cursor-pointer hover:bg-white/[0.03] transition-colors"
                style={{ border: "1px solid rgba(255,255,255,0.05)" }}>
                <div className="w-1.5 h-8 rounded-full flex-shrink-0" style={{ background: riskColor(s.risk) }} />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-white truncate">{s.name}</div>
                  <div className="text-[10px] mt-0.5" style={{ color: "#3A5570", fontFamily: "'JetBrains Mono', monospace" }}>
                    {s.id} · {s.incidents} incidents
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold" style={{ color: riskColor(s.risk), fontFamily: "'JetBrains Mono', monospace" }}>
                    {s.score}
                  </div>
                  <div className="text-[9px] uppercase" style={{ color: "#3A5570" }}>Risk</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
