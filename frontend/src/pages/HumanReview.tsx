import { useEffect, useState } from "react";
import { listIncidents, reviewIncident, ApiError, type IncidentResponse } from "@/lib/api";

// This page pulls the oldest un-reviewed incident from the database and
// lets a reviewer confirm or override it via PATCH /incidents/{id}/review.
// The backend has no named-reviewer/auth system yet and no general audit
// log endpoint, so the history panel only shows the two events the data
// actually supports (AI classification at submission time, and the
// decision just made) instead of a fabricated multi-step trail.

type HistoryEntry = { time: string; actor: string; action: string };

function verdictLabel(v: IncidentResponse["sif_verdict"]) {
  if (v === "HIGH") return "HIGH SIF POTENTIAL";
  if (v === "REVIEW") return "BORDERLINE — REVIEW REQUIRED";
  return "LOW SIF POTENTIAL";
}

export default function HumanReview() {
  const [pending, setPending] = useState<IncidentResponse[]>([]);
  const [index] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [note, setNote] = useState("");
  const [decision, setDecision] = useState<null | "approved" | "overridden">(null);
  const [overrideVerdict, setOverrideVerdict] = useState("LOW");
  const [decidedAt, setDecidedAt] = useState<string | null>(null);

  const loadPending = () => {
    setLoading(true);
    listIncidents({ reviewed_by_human: false, limit: 25 })
      .then((data: IncidentResponse[]) => {
        setPending(data);
        setError(null);
      })
      .catch((e: unknown) => setError(e instanceof ApiError ? e.message : "Failed to load pending reviews."))
      .finally(() => setLoading(false));
  };

  useEffect(loadPending, []);

  const active: IncidentResponse | null = pending[index] ?? null;

  const resetDecisionState = () => {
    setNote("");
    setDecision(null);
    setOverrideVerdict("LOW");
    setDecidedAt(null);
  };

  const submit = async (kind: "approved" | "overridden") => {
    if (!active) return;
    setSubmitting(true);
    setError(null);
    try {
      await reviewIncident(active.id, {
        human_corrected_verdict: kind === "overridden" ? overrideVerdict : undefined,
        reviewer_notes: note || undefined,
      });
      setDecision(kind);
      setDecidedAt(new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }));
    } catch (e: unknown) {
      setError(e instanceof ApiError ? e.message : "Failed to submit review.");
    } finally {
      setSubmitting(false);
    }
  };

  const nextCase = () => {
    resetDecisionState();
    // remove the case we just decided on and move to the next
    setPending((prev: IncidentResponse[]) => prev.filter((_, i: number) => i !== index));
  };

  if (loading) {
    return <div className="p-6 text-sm" style={{ color: "#5A7A9A" }}>Loading pending reviews…</div>;
  }

  if (!active) {
    return (
      <div className="flex flex-col gap-4 p-6">
        <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
          Human Review Center
        </h1>
        <div className="rounded-lg p-8 text-center" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="text-sm font-medium text-white mb-1">No pending reviews 🎉</div>
          <div className="text-xs" style={{ color: "#5A7A9A" }}>Every incident in the database has been reviewed.</div>
          <button onClick={loadPending} className="mt-4 px-4 py-2 rounded text-xs font-medium text-white" style={{ background: "#E8531D" }}>
            Refresh
          </button>
        </div>
        {error && <div className="text-xs" style={{ color: "#DC2626" }}>{error}</div>}
      </div>
    );
  }

  const history: HistoryEntry[] = [
    { time: new Date(active.submitted_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }), actor: "SIFORA AI", action: `Auto-classified as ${verdictLabel(active.sif_verdict)} (${Math.round(active.sif_probability * 100)}% confidence)` },
    ...(decision ? [{
      time: decidedAt || "",
      actor: "Reviewer",
      action: decision === "approved" ? `Approved AI decision — ${verdictLabel(active.sif_verdict)}` : `Overrode AI decision to: ${overrideVerdict}`,
    }] : []),
  ];

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>
            Human Review Center
          </h1>
          <p className="text-sm mt-0.5" style={{ color: "#5A7A9A" }}>
            Case #{active.id} · {pending.length} pending in queue
          </p>
        </div>
        <span className="text-xs px-3 py-1.5 rounded font-medium" style={{ background: "rgba(217,119,6,0.12)", color: "#D97706", border: "1px solid rgba(217,119,6,0.25)" }}>
          Pending Review
        </span>
      </div>

      {error && (
        <div className="text-xs rounded p-3" style={{ background: "rgba(220,38,38,0.08)", color: "#DC2626", border: "1px solid rgba(220,38,38,0.25)" }}>
          {error}
        </div>
      )}

      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
        {/* Left column */}
        <div className="flex flex-col gap-4">
          {/* Original Report */}
          <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm font-semibold text-white" style={{ fontFamily: "'DM Sans', sans-serif" }}>Original Report</div>
              <span className="text-[10px] px-2 py-0.5 rounded font-mono" style={{ background: "#0F1929", color: "#5A7A9A" }}>{active.submitted_via}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mb-3">
              {[
                { l: "Report ID", v: `#${active.id}` },
                { l: "Submitted At", v: new Date(active.submitted_at).toLocaleString("en-IN") },
                { l: "Site", v: active.site || "—" },
              ].map(f => (
                <div key={f.l}>
                  <div className="text-[10px] uppercase tracking-wide mb-0.5" style={{ color: "#2D4560" }}>{f.l}</div>
                  <div className="text-xs text-white">{f.v}</div>
                </div>
              ))}
            </div>
            <div className="rounded p-3 text-[11px] leading-relaxed" style={{ background: "#070F1A", color: "#7A9AB5", fontFamily: "'JetBrains Mono', monospace", border: "1px solid rgba(255,255,255,0.05)" }}>
              {active.raw_text}
            </div>
          </div>

          {/* AI Prediction */}
          <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-sm font-semibold text-white mb-3" style={{ fontFamily: "'DM Sans', sans-serif" }}>AI Prediction</div>
            <div className="rounded p-4 mb-3" style={{ background: "rgba(220,38,38,0.08)", border: "1px solid rgba(220,38,38,0.2)" }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: "#DC2626" }}>SIF Verdict</div>
                  <div className="text-lg font-bold text-white">{verdictLabel(active.sif_verdict)}</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold" style={{ color: "#DC2626", fontFamily: "'JetBrains Mono', monospace" }}>
                    {Math.round(active.sif_probability * 100)}%
                  </div>
                  <div className="text-[10px]" style={{ color: "#5A7A9A" }}>Confidence</div>
                </div>
              </div>
              <div className="mt-3 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                <div className="h-full rounded-full" style={{ width: `${active.sif_probability * 100}%`, background: "#DC2626" }} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-medium text-white mb-2">Detected Hazards</div>
                <div className="space-y-1">
                  {active.hazards.length ? active.hazards.map(h => (
                    <div key={h} className="text-[11px] px-2 py-1 rounded" style={{ background: "rgba(220,38,38,0.1)", color: "#DC2626" }}>{h}</div>
                  )) : <div className="text-[11px]" style={{ color: "#3A5570" }}>None detected</div>}
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-white mb-2">Barrier Failures</div>
                <div className="space-y-1">
                  {active.barrier_failures.length ? active.barrier_failures.map(b => (
                    <div key={b} className="text-[11px] px-2 py-1 rounded" style={{ background: "rgba(217,119,6,0.1)", color: "#D97706" }}>{b}</div>
                  )) : <div className="text-[11px]" style={{ color: "#3A5570" }}>None detected</div>}
                </div>
              </div>
            </div>
          </div>

          {/* Extracted Entities */}
          <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-sm font-semibold text-white mb-3" style={{ fontFamily: "'DM Sans', sans-serif" }}>Extracted Entities</div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Activities", value: active.activities.join(", ") || "—" },
                { label: "Locations", value: active.locations.join(", ") || "—" },
                { label: "Life-Saving Rules", value: active.life_saving_rules.length ? `${active.life_saving_rules.length} matched` : "None" },
              ].map(e => (
                <div key={e.label} className="rounded p-3" style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div className="text-[10px] uppercase tracking-wide mb-1" style={{ color: "#3A5570" }}>{e.label}</div>
                  <div className="text-xs font-medium text-white">{e.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-4">
          {/* Reviewer Notes */}
          <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-sm font-semibold text-white mb-3" style={{ fontFamily: "'DM Sans', sans-serif" }}>Reviewer Notes</div>
            <textarea
              value={note}
              onChange={e => setNote(e.target.value)}
              rows={5}
              disabled={!!decision}
              placeholder="Document your reasoning, observations, or disagreement with the AI assessment..."
              className="w-full rounded text-xs leading-relaxed resize-none outline-none p-3"
              style={{
                background: "#070F1A", border: "1px solid rgba(255,255,255,0.07)",
                color: "#9BB5CC", fontFamily: "'Inter', sans-serif", lineHeight: "1.7",
              }}
            />
          </div>

          {/* Decision Actions */}
          {!decision ? (
            <div className="rounded-lg p-5" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="text-sm font-semibold text-white mb-4" style={{ fontFamily: "'DM Sans', sans-serif" }}>Decision</div>
              <div className="space-y-3">
                <button onClick={() => submit("approved")} disabled={submitting}
                  className="w-full py-3 rounded text-sm font-semibold text-white transition-all"
                  style={{ background: "#16A34A", opacity: submitting ? 0.6 : 1 }}>
                  ✓ Approve AI Decision
                </button>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.06)" }} />
                    <span className="text-[10px] uppercase tracking-wide" style={{ color: "#3A5570" }}>or override with</span>
                    <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.06)" }} />
                  </div>
                  <select
                    value={overrideVerdict}
                    onChange={e => setOverrideVerdict(e.target.value)}
                    className="w-full px-3 py-2 rounded text-xs outline-none"
                    style={{ background: "#070F1A", border: "1px solid rgba(255,255,255,0.08)", color: "#9BB5CC" }}
                  >
                    <option value="LOW">LOW SIF POTENTIAL</option>
                    <option value="HIGH">HIGH SIF POTENTIAL</option>
                    <option value="NOT_SIF">NOT SIF RELATED</option>
                  </select>
                  <button onClick={() => submit("overridden")} disabled={submitting}
                    className="w-full py-3 rounded text-sm font-semibold transition-all"
                    style={{ background: "rgba(217,119,6,0.15)", color: "#D97706", border: "1px solid rgba(217,119,6,0.3)", opacity: submitting ? 0.6 : 1 }}>
                    ⟳ Override AI Decision
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-lg p-5" style={{ background: decision === "approved" ? "rgba(22,163,74,0.08)" : "rgba(217,119,6,0.08)", border: `1px solid ${decision === "approved" ? "rgba(22,163,74,0.3)" : "rgba(217,119,6,0.3)"}` }}>
              <div className="text-sm font-semibold mb-1" style={{ color: decision === "approved" ? "#16A34A" : "#D97706" }}>
                {decision === "approved" ? "✓ AI Decision Approved" : "⟳ AI Decision Overridden"}
              </div>
              <div className="text-xs" style={{ color: "#5A7A9A" }}>
                {decision === "approved" ? "You confirmed the AI verdict: " + verdictLabel(active.sif_verdict) : `Changed to: ${overrideVerdict}`}
              </div>
              <div className="text-[10px] mt-2" style={{ color: "#3A5570", fontFamily: "'JetBrains Mono', monospace" }}>
                Saved to database · {decidedAt}
              </div>
              <button onClick={nextCase} className="mt-3 w-full py-2 rounded text-xs font-medium text-white" style={{ background: "#E8531D" }}>
                Next Case →
              </button>
            </div>
          )}

          {/* Audit Trail */}
          <div className="rounded-lg p-5 flex-1" style={{ background: "#0A1422", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-sm font-semibold text-white mb-3" style={{ fontFamily: "'DM Sans', sans-serif" }}>Decision History</div>
            <div className="space-y-3">
              {history.map((h: HistoryEntry, i: number) => (
                <div key={i} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-1.5 h-1.5 rounded-full mt-1" style={{ background: h.actor === "SIFORA AI" ? "#E8531D" : "#2D4560" }} />
                    {i < history.length - 1 ? <div className="flex-1 w-px mt-1" style={{ background: "rgba(255,255,255,0.05)" }} /> : null}
                  </div>
                  <div className="pb-3">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-xs font-medium text-white">{h.actor}</span>
                      <span className="text-[10px]" style={{ color: "#3A5570", fontFamily: "'JetBrains Mono', monospace" }}>{h.time}</span>
                    </div>
                    <div className="text-[11px]" style={{ color: "#5A7A9A" }}>{h.action}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}