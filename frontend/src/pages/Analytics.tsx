import { useEffect, useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, Cell, PieChart, Pie
} from "recharts";
import {
  getAnalyticsSummary, getSiteAnalytics, getPatternAnalytics, ApiError,
  type SiteAnalyticsItem, type PatternAnalyticsItem, type AnalyticsSummary,
} from "@/lib/api";

const typeBreakdown = [
  { name: "Near-Miss", value: 112, color: "#D97706" },
  { name: "Unsafe Act", value: 78, color: "#E8531D" },
  { name: "Unsafe Condition", value: 63, color: "#3B82F6" },
  { name: "Safety Observation", value: 22, color: "#5A7A9A" },
  { name: "Incident", value: 9, color: "#DC2626" },
];

const radarData = [
  { subject: "PTW Compliance", score: 62 },
  { subject: "PPE Usage", score: 78 },
  { subject: "Hazard ID", score: 55 },
  { subject: "Supervisory Obs.", score: 71 },
  { subject: "Contractor Mgmt", score: 44 },
  { subject: "Emergency Prep.", score: 80 },
];

const riskTrend = [
  { q: "Q1 '23", sif: 28, nonsif: 89 },
  { q: "Q2 '23", sif: 34, nonsif: 102 },
  { q: "Q3 '23", sif: 29, nonsif: 95 },
  { q: "Q4 '23", sif: 41, nonsif: 114 },
  { q: "Q1 '24", sif: 38, nonsif: 107 },
  { q: "Q2 '24", sif: 32, nonsif: 98 },
  { q: "Q3 '24", sif: 44, nonsif: 121 },
];

interface TooltipPayloadItem {
  name: string;
  value: number | string;
  color?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded px-3 py-2 text-xs" style={{ background: "#0F1929", border: "1px solid rgba(255,255,255,0.1)" }}>
      <div className="font-semibold mb-1" style={{ color: "#8BA3C0" }}>{label}</div>
      {payload.map((p: TooltipPayloadItem) => (
        <div key={p.name} style={{ color: p.color || "#E8531D" }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

const scoreColor = (s: number) => (s >= 75 ? "#DC2626" : s >= 50 ? "#D97706" : "#16A34A");

export default function Analytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [sites, setSites] = useState<SiteAnalyticsItem[]>([]);
  const [patterns, setPatterns] = useState<PatternAnalyticsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getAnalyticsSummary(), getSiteAnalytics(), getPatternAnalytics()])
      .then(([s, si, p]) => {
        if (!cancelled) {
          setSummary(s);
          setSites(si);
          setPatterns(p);
          setError(null);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : "Failed to load analytics.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Aggregate activity x barrier_failure combos into a top barrier-failure list
  const barrierFailures = Object.entries(
    patterns.reduce<Record<string, number>>((acc, p) => {
      acc[p.barrier_failure] = (acc[p.barrier_failure] || 0) + p.count;
      return acc;
    }, {})
  )
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  const maxBarrierCount = Math.max(1, ...barrierFailures.map((b) => b.count));
  const total = typeBreakdown.reduce((sum: number, t) => sum + t.value, 0);

  return (
    <div className="flex flex-col gap-5 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
          Analytics Suite
        </h1>
        <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
          Executive safety intelligence · live database
        </p>
      </div>

      {error && (
        <div className="text-xs rounded p-3" style={{ background: "rgba(220,38,38,0.08)", color: "#DC2626", border: "1px solid rgba(220,38,38,0.25)" }}>
          {error}
        </div>
      )}

      {/* Summary KPIs — live */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Total Incidents", value: summary?.total_incidents },
          { label: "High-SIF Count", value: summary?.high_sif_count },
          
          { label: "High-SIF Ratio", value: summary ? `${summary.high_sif_ratio}%` : undefined },
        ].map((k) => (
          <div key={k.label} className="rounded-lg px-5 py-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-xs uppercase tracking-widest font-medium mb-2" style={{ color: "#3A5570" }}>
              {k.label}
            </div>
            <div className="text-3xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
              {loading ? "…" : k.value ?? "—"}
            </div>
          </div>
        ))}
      </div>

      {/* SIF Event Trend */}
      <div className="rounded-lg p-6" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-start justify-between mb-6">
          <div>
            <div className="text-lg font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
              SIF Event Trend — 7 Quarters
            </div>
            <p className="text-xs mt-0.5" style={{ color: "#5A7A9A" }}>
              Trend of SIF precursor incidents over time across reporting periods.
            </p>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={riskTrend} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="sifG" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#DC2626" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#DC2626" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="nonsifG" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1E3050" stopOpacity={0.6} />
                <stop offset="95%" stopColor="#1E3050" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="q" tick={{ fill: "#4A6080", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#4A6080", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="nonsif" stroke="#1E3050" strokeWidth={1.5} fill="url(#nonsifG)" name="Non-SIF Incidents" />
            <Area type="monotone" dataKey="sif" stroke="#DC2626" strokeWidth={2.5} fill="url(#sifG)" name="SIF Events" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr 1fr" }}>
        {/* Top barrier failures — live */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="font-semibold text-white text-sm mb-1" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Top Barrier Failures
          </div>
          <div className="text-xs mb-4" style={{ color: "#3A5570" }}>
            Which controls broke down most? (HIGH-SIF reports)
          </div>
          {loading ? (
            <div className="text-xs" style={{ color: "#3A5570" }}>Loading…</div>
          ) : barrierFailures.length === 0 ? (
            <div className="text-xs" style={{ color: "#3A5570" }}>No HIGH-SIF patterns recorded yet</div>
          ) : (
            <div className="space-y-2.5">
              {barrierFailures.map((b, i: number) => (
                <div key={b.name}>
                  <div className="flex justify-between text-xs mb-1">
                    <span style={{ color: "#8BA3C0" }}>{b.name}</span>
                    <span style={{ color: "#DC2626", fontFamily: "'JetBrains Mono', monospace" }}>{b.count}</span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.05)" }}>
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${(b.count / maxBarrierCount) * 100}%`,
                        background: i === 0 ? "#DC2626" : i === 1 ? "#D97706" : "#E8531D",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Report type breakdown */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex items-center justify-between mb-1">
            <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>
              Incident Type Distribution
            </div>
          </div>
          <div className="text-xs mb-4" style={{ color: "#3A5570" }}>What is being reported?</div>
          <div className="flex justify-center mb-3">
            <PieChart width={140} height={140}>
              <Pie data={typeBreakdown} cx={70} cy={70} innerRadius={42} outerRadius={65} dataKey="value" strokeWidth={0}>
                {typeBreakdown.map((entry, index: number) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </div>
          <div className="space-y-1.5">
            {typeBreakdown.map((t) => (
              <div key={t.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2" style={{ color: "#7A9AB5" }}>
                  <span className="w-2 h-2 rounded-full inline-block" style={{ background: t.color }} />
                  {t.name}
                </span>
                <span style={{ color: "#C4D5E5", fontFamily: "'JetBrains Mono', monospace" }}>
                  {t.value} <span style={{ color: "#3A5570" }}>({Math.round((t.value / total) * 100)}%)</span>
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Safety radar */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex items-center justify-between mb-1">
            <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>
              Safety Culture Radar
            </div>
          </div>
          <div className="text-xs mb-3" style={{ color: "#3A5570" }}>How each safety dimension performs</div>
          <div style={{ width: "100%", height: 220 }}>
            <RadarChart width={260} height={220} data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.06)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "#4A6080", fontSize: 9 }} />
              <Radar name="Score" dataKey="score" stroke="#E8531D" fill="#E8531D" fillOpacity={0.15} strokeWidth={1.5} />
            </RadarChart>
          </div>
        </div>
      </div>

      {/* Site Rankings — live */}
      <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="font-semibold text-white text-sm" style={{ fontFamily: "'DM Sans', sans-serif" }}>
              Site Risk Rankings
            </div>
            <div className="text-xs mt-0.5" style={{ color: "#3A5570" }}>
              Higher HIGH-SIF density = higher risk exposure — requires more attention
            </div>
          </div>
        </div>
        {loading ? (
          <div className="text-xs" style={{ color: "#3A5570" }}>Loading…</div>
        ) : sites.length === 0 ? (
          <div className="text-xs" style={{ color: "#3A5570" }}>No site data recorded yet</div>
        ) : (
          <div className="space-y-2">
            {sites.map((s, i: number) => (
              <div
                key={s.site}
                className="flex items-center gap-4 px-4 py-3 rounded"
                style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.04)" }}
              >
                <div className="w-6 text-center text-xs font-bold" style={{ color: "#2D4560" }}>
                  {i + 1}
                </div>
                <div className="flex-1 text-sm font-medium text-white">{s.site}</div>
                <div className="w-48 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${s.high_sif_density}%`, background: scoreColor(s.high_sif_density) }}
                  />
                </div>
                <div
                  className="w-10 text-right text-sm font-bold"
                  style={{ color: scoreColor(s.high_sif_density), fontFamily: "'JetBrains Mono', monospace" }}
                >
                  {s.high_sif_density}
                </div>
                <div className="w-24 text-right text-xs" style={{ color: "#5A7A9A" }}>
                  {s.total_reports} reports
                </div>
                <div className="w-20 text-right text-xs" style={{ color: "#5A7A9A" }}>
                  {s.high_sif_count} HIGH-SIF
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}