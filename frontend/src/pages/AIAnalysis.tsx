import { useState, useRef } from "react";
import {
  submitIncident,
  ApiError,
  type IncidentResponse,
  type PredictionResponse,
} from "@/lib/api";
import VoiceRecorder from "../components/VoiceRecorder";

function verdictLabel(v: PredictionResponse["sif_verdict"]) {
  if (v === "HIGH") return "HIGH SIF POTENTIAL";
  if (v === "REVIEW") return "BORDERLINE — HUMAN REVIEW RECOMMENDED";
  return "LOW SIF POTENTIAL";
}

function verdictColor(v: PredictionResponse["sif_verdict"]) {
  if (v === "HIGH") return "#DC2626";
  if (v === "REVIEW") return "#D97706";
  return "#16A34A";
}

function buildSummary(r: PredictionResponse, barrierFailures: string[]) {
  const parts: string[] = [];
  if (r.sif_verdict === "HIGH") {
    parts.push("This report contains language consistent with Serious Injury or Fatality (SIF) precursors.");
  } else if (r.sif_verdict === "REVIEW") {
    parts.push("The model is not confident enough to classify this automatically — a human reviewer should confirm the verdict.");
  } else {
    parts.push("The model did not find strong SIF-precursor signal in this report.");
  }
  
  if (r.life_saving_rules && r.life_saving_rules.length) {
    parts.push(`Matched to ${r.life_saving_rules.length} DGMS Safety Guideline${r.life_saving_rules.length > 1 ? "s" : ""}: ${r.life_saving_rules.join(", ")}.`);
  }

  if (barrierFailures.length) {
    parts.push(
      ` ${barrierFailures.length} barrier failure${
        barrierFailures.length > 1 ? "s" : ""
      } detected.`
    );
  }
  return parts.join(" ");
}

export default function AIAnalysis() {
  const [mode, setMode] = useState<"single" | "bulk">("single");
  const [file, setFile] = useState<File | null>(null);

  // Single Report State
  const [report, setReport] = useState("");
  const [selectedSite, setSelectedSite] = useState("");
  const [incidentType, setIncidentType] = useState("");
  const [severity, setSeverity] = useState("");
  const [department, setDepartment] = useState("");

  // Response State
  const [result, setResult] = useState<IncidentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bulkSuccess, setBulkSuccess] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [reportId] = useState(
    `INC-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`
  );

  const isFormInvalid = loading || !report.trim();

  const analyzeSingle = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await submitIncident(report, selectedSite, incidentType, severity, department);
      console.log("API RESPONSE:", res);
      setResult(res);
    } catch (e: unknown) {
      setResult(null);
      setError(e instanceof ApiError ? e.message : "Something went wrong analyzing this report.");
    } finally {
      setLoading(false);
    }
  };

  const uploadBulk = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setBulkSuccess(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/v1/incidents/bulk", {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) throw new Error("Bulk upload failed. Check the backend server.");
      const data = await response.json();
      setBulkSuccess(data.message);
      setFile(null);
    } catch (e: any) {
      setError(e.message || "Failed to process bulk upload.");
    } finally {
      setLoading(false);
    }
  };

  const analyzed = result !== null;

  const hasMetadata = [
    result?.site,
    result?.incident_type,
    result?.severity,
    result?.department,
  ].some(
    (v) =>
      Boolean(v?.trim()) &&
      v !== "Not specified" &&
      v !== "Unknown" &&
      v !== "N/A"
  );

  const workflowStatus =
    result?.sif_verdict === "HIGH"
      ? "Escalated for Immediate Review"
      : result?.sif_verdict === "REVIEW"
      ? "Pending Human Review"
      : "Closed by AI Screening";

  // UPDATED FOR MINING DOMAIN
  const HAZARD_BARRIER_MAP: Record<string, string[]> = {
    "roof fall": ["inadequate roof support", "no roof bolting"],
    "strata spalling": ["pre-shift inspection", "no roof bolting"],
    "methane accumulation": ["poor ventilation", "defunct audio-visual alarm"],
    "coal dust explosion": ["poor ventilation", "gas testing"],
    "inundation": ["permit to work"],
    "dumper rollover": ["substandard berm"],
    "dump slide": ["substandard berm"],
    "heavy machinery run-over": ["defunct audio-visual alarm", "safety belt"],
    "confined space": ["permit to work", "gas testing"],
    "misfire": ["permit to work"]
  };

  const displayBarrierFailures = Array.from(
    new Set(
      result?.barrier_failures?.length &&
      !result.barrier_failures.some((b) => b.toLowerCase() === "none detected")
        ? result.barrier_failures
        : result?.hazards?.flatMap(
            (hazard: string) => HAZARD_BARRIER_MAP[hazard.toLowerCase()] || []
          ) || []
    )
  );

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Incident Submission Center
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
            Capture field observations or upload historical datasets for SIF risk evaluation.
          </p>
        </div>
        
        {/* Mode Toggle */}
        <div className="flex bg-[#0A1422] rounded-lg p-1 border border-white/5">
          <button 
            onClick={() => { setMode("single"); setResult(null); setError(null); setBulkSuccess(null); }}
            className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${mode === "single" ? 'bg-[#E8531D] text-white' : 'text-[#5A7A9A] hover:text-white'}`}
          >
            Single Entry
          </button>
          <button 
            onClick={() => { setMode("bulk"); setResult(null); setError(null); setBulkSuccess(null); }}
            className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${mode === "bulk" ? 'bg-[#E8531D] text-white' : 'text-[#5A7A9A] hover:text-white'}`}
          >
            Bulk Upload
          </button>
        </div>
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: analyzed ? "1fr 1fr" : "1fr" }}>
        
        {/* INPUT PANEL */}
        <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          
          {mode === "single" ? (
             <div className="flex flex-col">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                    Incident Metadata & Details
                  </div>
                  <VoiceRecorder
                    onTranscript={(text) => {
                      console.log("Received transcript:", text);
                      setReport(text);
                    }}
                  />
                </div>

                <div className="flex justify-between items-center mb-3 mt-2 text-xs" style={{ color: "#5A7A9A" }}>
                  <span>Report ID</span>
                  <span className="font-mono" style={{ color: "#E8531D" }}>{reportId}</span>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-3">
                  <select
                    value={incidentType}
                    onChange={(e) => setIncidentType(e.target.value)}
                    className="w-full rounded p-3 text-xs outline-none"
                    style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.07)", color: "#9BB5CC" }}
                  >
                    <option value="">Incident Type</option>
                    <option value="Unsafe Act">Unsafe Act</option>
                    <option value="Unsafe Condition">Unsafe Condition</option>
                    <option value="Near Miss">Near Miss</option>
                    <option value="First Aid Case">First Aid Case</option>
                    <option value="Incident">Incident</option>
                  </select>

                  {/* UPDATED MINING SITES */}
                  <select
                    value={selectedSite}
                    onChange={(e) => setSelectedSite(e.target.value)}
                    className="w-full rounded p-3 text-xs outline-none"
                    style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.07)", color: "#9BB5CC" }}
                  >
                    <option value="">Select Site</option>
                    <option value="SECL - Churcha Colliery">SECL - Churcha</option>
                    <option value="BCCL - Jharia Division">BCCL - Jharia</option>
                    <option value="ECL - Raniganj Area">ECL - Raniganj</option>
                    <option value="SCCL - Singareni Deep Seam">SCCL - Singareni</option>
                    <option value="NCL - Singrauli Opencast">NCL - Singrauli</option>
                    <option value="WCL - Nagpur Wardha Valley">WCL - Nagpur</option>
                    <option value="MCL - Talcher Concession">MCL - Talcher</option>
                  </select>

                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full rounded p-3 text-xs outline-none"
                    style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.07)", color: "#9BB5CC" }}
                  >
                    <option value="">Potential Severity</option>
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>

                  {/* UPDATED MINING DEPARTMENTS */}
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full rounded p-3 text-xs outline-none"
                    style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.07)", color: "#9BB5CC" }}
                  >
                    <option value="">Department</option>
                    <option value="Underground Operations">Underground Operations</option>
                    <option value="Surface Mining">Surface Mining</option>
                    <option value="Ventilation & Safety">Ventilation & Safety</option>
                    <option value="Maintenance">Maintenance</option>
                    <option value="Logistics & Transport">Logistics & Transport</option>
                  </select>
                </div>

                <textarea
                  value={report}
                  onChange={(e) => setReport(e.target.value)}
                  className="w-full rounded text-xs leading-relaxed resize-none outline-none p-3"
                  rows={analyzed ? 14 : 10}
                  placeholder="Enter detailed incident narrative, work activity, hazards observed, controls missing, personnel involved, and immediate actions taken..."
                  style={{
                    background: "#070F1A",
                    border: "1px solid rgba(255,255,255,0.07)",
                    color: "#9BB5CC",
                    fontFamily: "'JetBrains Mono', monospace",
                    lineHeight: "1.7",
                  }}
                />

                <div className="flex items-center justify-between mt-3">
                  <span className="text-[11px]" style={{ color: "#3A5570" }}>
                    DGMS Mining Safety Workflow
                  </span>
                  <button
                    onClick={analyzeSingle}
                    disabled={isFormInvalid}
                    className="px-5 py-2 rounded text-sm font-semibold text-white transition-all"
                    style={{
                      background: isFormInvalid ? "#1E2F47" : "#E8531D",
                      cursor: isFormInvalid ? "not-allowed" : "pointer",
                    }}
                  >
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
                        Analyzing...
                      </span>
                    ) : (
                      "Submit Incident"
                    )}
                  </button>
                </div>
             </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 border-2 border-dashed border-white/10 rounded-lg bg-[#070F1A]">
              <div className="text-4xl mb-4">📂</div>
              <h3 className="text-white font-medium mb-1">Upload Historical Incidents</h3>
              <p className="text-xs text-[#5A7A9A] mb-6">Supports .CSV containing a 'report' column</p>
              
              <input 
                type="file" 
                accept=".csv" 
                className="hidden" 
                ref={fileInputRef}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 rounded text-xs font-medium text-white border border-white/10 hover:bg-white/5 transition-colors"
              >
                {file ? file.name : "Select File"}
              </button>

              {file && (
                <button
                  onClick={uploadBulk}
                  disabled={loading}
                  className="mt-6 px-8 py-2.5 rounded text-sm font-semibold text-white transition-all bg-[#16A34A] hover:bg-[#15803d]"
                >
                  {loading ? "Processing Dataset..." : "Run ML Inference Pipeline"}
                </button>
              )}

              {bulkSuccess && <div className="mt-4 text-xs text-[#16A34A] font-medium px-4 py-2 bg-green-500/10 border border-green-500/20 rounded">{bulkSuccess}</div>}
            </div>
          )}

          {error && (
            <div
              className="mt-3 text-xs rounded p-3"
              style={{
                background: "rgba(220,38,38,0.08)",
                color: "#DC2626",
                border: "1px solid rgba(220,38,38,0.25)",
              }}
            >
              {error}
            </div>
          )}
        </div>

        {/* Results Panel */}
        {result && (
          <div className="flex flex-col gap-3 overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
            {/* Workflow Status */}
            <div
              className="rounded-lg p-4"
              style={{
                background: "#0A1422",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              <div
                className="text-[10px] uppercase tracking-widest mb-2"
                style={{ color: "#16A34A" }}
              >
                Workflow Status
              </div>
              <div className="text-sm text-white font-semibold">
                Incident Successfully Logged
              </div>
              <div
                className="text-xs mt-1"
                style={{ color: "#7A9AB5" }}
              >
                Status: {workflowStatus}
              </div>
            </div>

            {/* Incident Metadata */}
            {hasMetadata && (
              <div
                className="rounded-lg p-4"
                style={{
                  background: "#0A1422",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                <div className="text-xs font-semibold text-white mb-3">
                  Incident Metadata
                </div>

                <div className="grid grid-cols-2 gap-y-2 text-xs">
                  {result.site &&
                    result.site !== "Not specified" &&
                    result.site !== "Unknown" &&
                    result.site !== "N/A" && (
                      <div>
                        <span style={{ color: "#5A7A9A" }}>Site:</span>
                        <div className="text-white">{result.site}</div>
                      </div>
                    )}

                  {result.incident_type &&
                    result.incident_type !== "Not specified" &&
                    result.incident_type !== "Unknown" &&
                    result.incident_type !== "N/A" && (
                      <div>
                        <span style={{ color: "#5A7A9A" }}>Type:</span>
                        <div className="text-white">{result.incident_type}</div>
                      </div>
                    )}

                  {result.severity &&
                    result.severity !== "Not specified" &&
                    result.severity !== "Unknown" &&
                    result.severity !== "N/A" && (
                      <div>
                        <span style={{ color: "#5A7A9A" }}>Severity:</span>
                        <div className="text-white">{result.severity}</div>
                      </div>
                    )}

                  {result.department &&
                    result.department !== "Not specified" &&
                    result.department !== "Unknown" &&
                    result.department !== "N/A" && (
                      <div>
                        <span style={{ color: "#5A7A9A" }}>Department:</span>
                        <div className="text-white">{result.department}</div>
                      </div>
                    )}
                </div>
              </div>
            )}

            {/* Verdict */}
            <div
              className="rounded-lg p-4"
              style={{
                background: `${verdictColor(result.sif_verdict)}14`,
                border: `1px solid ${verdictColor(result.sif_verdict)}40`,
              }}
            >
              <div className="flex items-start justify-between">
                {/* ADDED flex-1 pr-4 RIGHT HERE TO FIX THE LAYOUT BUG */}
                <div className="flex-1 pr-4">
                  <div
                    className="text-[10px] uppercase tracking-widest font-semibold mb-1"
                    style={{ color: verdictColor(result.sif_verdict) }}
                  >
                    SIF Verdict
                  </div>
                  <div className="text-xl font-bold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                    {verdictLabel(result.sif_verdict)}
                  </div>
                  <p className="text-xs mt-2 leading-relaxed" style={{ color: "#8BA3C0" }}>
                    {buildSummary(result, displayBarrierFailures)}
                  </p>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <div
                    className="text-3xl font-bold"
                    style={{
                      color: verdictColor(result.sif_verdict),
                      fontFamily: "'JetBrains Mono', monospace",
                    }}
                  >
                    {/* BULLETPROOF MATH TO HANDLE BOTH DECIMALS AND WHOLE NUMBERS */}
                    {(() => {
                      const rawProb = result.sif_probability || (result as any).probability || 0;
                      return Math.round(rawProb <= 1 ? rawProb * 100 : rawProb);
                    })()}%
                  </div>
                  <div className="text-[10px] uppercase tracking-wide mt-0.5" style={{ color: "#5A7A9A" }}>
                    SIF
                  </div>
                </div>
              </div>
            </div>
            {/* Chips */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
                <div className="text-xs font-semibold text-white mb-2" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                  Detected Hazards
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {result.hazards.length ? (
                    result.hazards.map((h: string) => (
                      <span
                        key={h}
                        className="text-[11px] px-2 py-1 rounded"
                        style={{
                          background: "rgba(220,38,38,0.1)",
                          color: "#DC2626",
                          border: "1px solid rgba(220,38,38,0.2)",
                        }}
                      >
                        {h}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px]" style={{ color: "#3A5570" }}>
                      None detected
                    </span>
                  )}
                </div>
              </div>
              <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
                <div className="text-xs font-semibold text-white mb-2" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                  Barrier Failures
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {displayBarrierFailures.length ? (
                    displayBarrierFailures.map((b: string) => (
                      <span
                        key={b}
                        className="text-[11px] px-2 py-1 rounded"
                        style={{
                          background: "rgba(217,119,6,0.1)",
                          color: "#D97706",
                          border: "1px solid rgba(217,119,6,0.2)",
                        }}
                      >
                        {b}
                      </span>
                    ))
                  ) : (
                    <span className="text-[11px]" style={{ color: "#3A5570" }}>
                      None detected
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Life Saving Rules */}
            <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-xs font-semibold text-white mb-2" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                DGMS Safety Guidelines Matched
              </div>
              <div className="space-y-1.5">
                {result.life_saving_rules && result.life_saving_rules.length ? (
                  result.life_saving_rules.map((r: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-[11px]" style={{ color: "#7A9AB5" }}>
                      <span style={{ color: "#E8531D" }}>→</span>
                      <span>{r}</span>
                    </div>
                  ))
                ) : (
                  <span className="text-[11px]" style={{ color: "#3A5570" }}>
                    No specific rule matched
                  </span>
                )}
              </div>
            </div>

            {/* Extracted Entities */}
            <div className="rounded-lg p-4" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-xs font-semibold text-white mb-3" style={{ fontFamily: "'DM Sans', sans-serif" }}>
                Extracted Entities
              </div>
              <div className="grid grid-cols-2 gap-y-2">
                <div>
                  <div className="text-[10px] uppercase tracking-wide" style={{ color: "#3A5570" }}>
                    Activities
                  </div>
                  <div className="text-xs mt-0.5 text-white">{result.activities?.join(", ") || "Not specified"}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wide" style={{ color: "#3A5570" }}>
                    Locations
                  </div>
                  <div className="text-xs mt-0.5 text-white">{result.locations?.join(", ") || "Not specified"}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}