import { useEffect, useState } from "react";
import { getSiteAnalytics } from "@/lib/api";

// Fallback coordinate mappings for known sites
const SITE_COORDS: Record<string, { x: number; y: number }> = {
  "SECL - Churcha Colliery": { x: 200, y: 130 },
  "BCCL - Jharia Division": { x: 280, y: 190 },
  "ECL - Raniganj Area": { x: 380, y: 150 },
  "SCCL - Singareni Deep Seam": { x: 460, y: 240 },
  "NCL - Singrauli Opencast": { x: 550, y: 100 },
  "WCL - Nagpur Wardha Valley": { x: 340, y: 280 },
  "MCL - Talcher Concession": { x: 180, y: 260 }
};

const INCIDENTS = [
  { x: 265, y: 205, type: "critical", label: "INC-0847: Methane accumulation detected" },
  { x: 195, y: 145, type: "high", label: "INC-0840: No PTW at underground panel" },
  { x: 385, y: 162, type: "medium", label: "INC-0834: LOTO deviation on vent fan" },
];

const riskColor = (r: string) => ({
  critical: "#DC2626", high: "#D97706", medium: "#3B82F6", low: "#16A34A"
}[r] || "#5A7A9A");

const riskBg = (r: string) => ({
  critical: "rgba(220,38,38,0.15)", high: "rgba(217,119,6,0.15)",
  medium: "rgba(59,130,246,0.15)", low: "rgba(22,163,74,0.15)"
}[r] || "transparent");

export default function SiteDigitalTwin() {
  const [selected, setSelected] = useState<string | null>(null);
  const [zones, setZones] = useState<any[]>([]);

  useEffect(() => {
    getSiteAnalytics()
      .then(data => {
        const mapped = data.map((site, index) => {
          // If the site name isn't in SITE_COORDS, dynamically assign coordinates on a grid so it never breaks
          const fallbackCoords = {
            x: 120 + (index % 4) * 140,
            y: 120 + Math.floor(index / 4) * 100
          };
          const coords = SITE_COORDS[site.site] || fallbackCoords;

          const siteNameClean = site.site && site.site.trim() !== "" ? site.site : "Unknown Mining Site";
          const id = siteNameClean === "Unknown Mining Site" ? `SITE-${index + 1}` : `${siteNameClean.split(" ").map(w => w[0]).join("").toUpperCase()}-${index + 1}`;

          return {
            id,
            siteName: siteNameClean,
            label: siteNameClean,
            x: coords.x,
            y: coords.y,
            alerts: site.high_sif_density > 75 ? 3 : site.high_sif_density > 65 ? 2 : site.high_sif_density > 50 ? 1 : 0,
            risk: site.high_sif_density > 75 ? "critical" : site.high_sif_density > 65 ? "high" : site.high_sif_density > 50 ? "medium" : "low",
            score: Math.round(site.high_sif_density),
            safetyScore: 100 - Math.round(site.high_sif_density)
          };
        });

        setZones(mapped);
        if (mapped.length > 0) {
          setSelected(mapped[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const selectedZone = zones.find(z => z.id === selected);

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Site Digital Twin
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
            DGMS Operational Sites · AI-Powered SIF Risk Monitoring · Live Safety Intelligence
          </p>
        </div>
        <div className="flex gap-2 text-xs">
          {["critical", "high", "medium", "low"].map(r => (
            <span key={r} className="flex items-center gap-1.5 px-2.5 py-1 rounded"
              style={{ background: riskBg(r), color: riskColor(r) }}>
              <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: riskColor(r) }} />
              {r.charAt(0).toUpperCase() + r.slice(1)}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 300px" }}>
        {/* Map */}
        <div className="rounded-lg overflow-hidden" style={{ background: "#050D18", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="px-4 py-3 flex items-center gap-3 border-b" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
            <span className="text-xs font-semibold text-white">DGMS Operational Sites — Digital Twin Overview</span>
            <span className="ml-auto text-[10px] px-2 py-0.5 rounded" style={{ background: "rgba(220,38,38,0.12)", color: "#DC2626" }}>
              {zones.reduce((sum, z) => sum + z.alerts, 0)} Active Alerts
            </span>
          </div>
          <div className="relative" style={{ minHeight: 400 }}>
            <svg viewBox="0 0 700 400" className="w-full" style={{ minHeight: 400 }}>
              <rect x={60} y={40} width={580} height={330} rx={8}
                fill="rgba(10,20,40,0.6)" stroke="rgba(255,255,255,0.08)" strokeWidth={1.5} />

              {[80, 140, 200, 260, 320, 380].map(y => (
                <line key={y} x1={60} y1={y} x2={640} y2={y} stroke="rgba(255,255,255,0.03)" strokeWidth={0.5} />
              ))}
              {[120, 200, 280, 360, 440, 520, 600].map(x => (
                <line key={x} x1={x} y1={40} x2={x} y2={370} stroke="rgba(255,255,255,0.03)" strokeWidth={0.5} />
              ))}

              <text x={80} y={62} fill="rgba(255,255,255,0.15)" fontSize={9} fontFamily="'JetBrains Mono', monospace" letterSpacing={1}>
                DGMS — SITE RISK MAP
              </text>

              <path d="M 120 200 L 580 200" stroke="rgba(255,255,255,0.06)" strokeWidth={6} strokeLinecap="round" />
              <path d="M 340 80 L 340 360" stroke="rgba(255,255,255,0.06)" strokeWidth={6} strokeLinecap="round" />

              {zones.map(zone => (
                <g key={zone.id}>
                  <rect
                    x={zone.x - 44} y={zone.y - 22} width={88} height={44} rx={6}
                    fill={selected === zone.id ? `${riskColor(zone.risk)}25` : riskBg(zone.risk)}
                    stroke={riskColor(zone.risk)}
                    strokeWidth={selected === zone.id ? 1.5 : 0.8}
                    strokeOpacity={0.6}
                    style={{ cursor: "pointer" }}
                    onClick={() => setSelected(zone.id)}
                  />
                  <text x={zone.x} y={zone.y - 4} textAnchor="middle" fill={riskColor(zone.risk)}
                    fontSize={8.5} fontFamily="'Inter', sans-serif" fontWeight="600" style={{ cursor: "pointer" }}
                    onClick={() => setSelected(zone.id)}>
                    {zone.id}
                  </text>
                  <text x={zone.x} y={zone.y + 9} textAnchor="middle" fill="rgba(255,255,255,0.45)"
                    fontSize={7.5} fontFamily="'Inter', sans-serif" style={{ cursor: "pointer" }}
                    onClick={() => setSelected(zone.id)}>
                    {zone.label.split(" ").slice(0, 2).join(" ")}
                  </text>
                  {zone.alerts > 0 && (
                    <g>
                      <circle cx={zone.x + 38} cy={zone.y - 16} r={7} 
                        fill={
                          zone.risk === "critical" ? "#DC2626" : zone.risk === "high" ? "#D97706" : zone.risk === "medium" ? "#3B82F6" : "#16A34A"
                        } 
                      />
                      <text x={zone.x + 38} y={zone.y - 13} textAnchor="middle" fill="white" fontSize={8} fontWeight="bold" fontFamily="'JetBrains Mono', monospace">
                        {zone.alerts}
                      </text>
                    </g>
                  )}
                </g>
              ))}

              {INCIDENTS.map((inc, i) => (
                <g key={i}>
                  <circle cx={inc.x} cy={inc.y} r={8} fill={`${riskColor(inc.type)}30`} stroke={riskColor(inc.type)} strokeWidth={1.5}>
                    <animate attributeName="r" values="8;14;8" dur="3s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.8;0.3;0.8" dur="3s" repeatCount="indefinite" />
                  </circle>
                  <text x={inc.x} y={inc.y + 4} textAnchor="middle" fill={riskColor(inc.type)} fontSize={9} fontFamily="'JetBrains Mono', monospace" fontWeight="bold">!</text>
                </g>
              ))}

              <g transform="translate(616, 60)">
                <circle r={14} fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" strokeWidth={0.5} />
                <text y={4} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize={10} fontFamily="'Inter', sans-serif" fontWeight="600">N</text>
              </g>
            </svg>
          </div>
        </div>

        {/* Right panel */}
        <div className="flex flex-col gap-3">
          {selectedZone && (
            <div className="rounded-lg p-4" style={{ background: "#0A1422", border: `1px solid ${riskColor(selectedZone.risk)}40` }}>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full" style={{ background: riskColor(selectedZone.risk) }} />
                <span className="text-xs font-bold" style={{ color: riskColor(selectedZone.risk) }}>{selectedZone.id}</span>
                <span className="text-[10px] uppercase ml-auto px-1.5 py-0.5 rounded"
                  style={{ background: riskBg(selectedZone.risk), color: riskColor(selectedZone.risk) }}>
                  {selectedZone.risk}
                </span>
              </div>
              <div className="text-sm font-semibold text-white mb-1">{selectedZone.label}</div>
              <div className="text-xs mb-1" style={{ color: "#5A7A9A" }}>Site: {selectedZone.siteName}</div>
              <div className="text-xs mb-1" style={{ color: "#5A7A9A" }}>Risk Level: {selectedZone.risk.toUpperCase()}</div>
              <div className="text-xs mb-3" style={{ color: "#5A7A9A" }}>High SIF Density: {selectedZone.score}%</div>
              
              <div className="flex gap-4 text-xs">
                <div>
                  <div className="text-[10px] uppercase tracking-wide" style={{ color: "#3A5570" }}>Active Alerts</div>
                  <div className="font-bold mt-0.5" style={{ color: selectedZone.alerts > 0 ? "#DC2626" : "#16A34A", fontFamily: "'JetBrains Mono', monospace" }}>
                    {selectedZone.alerts}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide" style={{ color: "#3A5570" }}>Safety Score</div>
                  <div className="font-bold mt-0.5" style={{
                    color: selectedZone.safetyScore >= 80 ? "#16A34A" : selectedZone.safetyScore >= 60 ? "#D97706" : "#DC2626",
                    fontFamily: "'JetBrains Mono', monospace"
                  }}>
                    {selectedZone.safetyScore}%
                  </div>  
                </div>
              </div>
            </div>
          )}

          {/* Zone list */}
          <div className="rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="px-4 py-2.5 border-b text-[10px] uppercase tracking-widest font-medium"
              style={{ background: "#070F1A", borderColor: "rgba(255,255,255,0.06)", color: "#2D4560" }}>
              All Zones
            </div>
            <div>
              {zones.map(zone => (
                <div key={zone.id}
                  onClick={() => setSelected(zone.id)}
                  className="flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors hover:bg-white/[0.02]"
                  style={{
                    background: selected === zone.id ? `${riskColor(zone.risk)}08` : "#0A1422",
                    borderBottom: "1px solid rgba(255,255,255,0.04)",
                  }}>
                  <div className="w-1 h-8 rounded-full" style={{ background: riskColor(zone.risk) }} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-white">{zone.label}</div>
                    <div className="text-[10px]" style={{ color: "#3A5570" }}>{zone.id} · SIF Density {zone.score}%</div>
                  </div>
                  {zone.alerts > 0 && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded"
                      style={{ background: riskBg(zone.risk), color: riskColor(zone.risk), fontFamily: "'JetBrains Mono', monospace" }}>
                      {zone.alerts}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Active incidents */}
          <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-xs font-semibold text-white mb-2">Active Incidents on Map</div>
            <div className="space-y-2">
              {INCIDENTS.map((inc, i) => (
                <div key={i} className="flex items-start gap-2 text-[11px]">
                  <div className="w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0" style={{ background: riskColor(inc.type) }} />
                  <span style={{ color: "#7A9AB5" }}>{inc.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}