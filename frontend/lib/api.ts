const API_BASE_URL = ((import.meta as unknown as { env: Record<string, string> }).env.VITE_API_BASE_URL) || "http://localhost:8000";

// --- Interfaces & Types ---

export interface PredictionResponse {
  sif_verdict: "HIGH" | "REVIEW" | "LOW";
  sif_probability: number;
  life_saving_rules: string[];
  hazards: string[];
  barrier_failures: string[];
  activities: string[];
  locations: string[];
  cleaned_text?: string;
}

export interface IncidentResponse {
  id: number;
  raw_text: string;
  cleaned_text?: string;
  site?: string;
  incident_type?: string;
  severity?: string;
  department?: string;
  submitted_via: string;
  submitted_at: string;
  sif_verdict: "HIGH" | "REVIEW" | "LOW";
  sif_probability: number;
  life_saving_rules: string[];
  hazards: string[];
  barrier_failures: string[];
  activities: string[];
  locations: string[];
  reviewed_by_human: boolean;
  human_corrected_verdict?: string;
  reviewer_notes?: string;
}

export interface IncidentReviewPayload {
  human_corrected_verdict?: string;
  reviewer_notes?: string;
}

export interface ListIncidentsParams {
  reviewed_by_human?: boolean;
  limit?: number;
  offset?: number;
  site?: string;
}

export interface AnalyticsSummary {
  total_incidents: number;
  high_sif_count: number;
  review_pending_count: number;
  high_sif_ratio: number;
}

export interface SiteAnalyticsItem {
  site: string;
  total_reports: number;
  high_sif_count: number;
  high_sif_density: number;
}

export interface PatternAnalyticsItem {
  activity: string;
  barrier_failure: string;
  count: number;
}

export class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

// --- Helper Functions ---

async function handleResponse<T>(response: Response, errorMessage: string): Promise<T> {
  if (!response.ok) {
    throw new ApiError(errorMessage, response.status);
  }
  return await response.json();
}

// --- API Methods ---

export async function predict(reportText: string): Promise<PredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: reportText }),
  });
  return handleResponse<PredictionResponse>(response, "Prediction failed");
}

export async function submitIncident(
  reportText: string, 
  site: string,
  incidentType?: string,
  severity?: string,
  department?: string
): Promise<IncidentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      raw_text: reportText, 
      site: site,
      incident_type: incidentType || "Incident",
      severity: severity || "Medium",
      department: department || "Operations",
      submitted_via: "web"
    }),
  });
  return handleResponse<IncidentResponse>(response, "Failed to save incident");
}

export async function listIncidents(params: ListIncidentsParams = {}): Promise<IncidentResponse[]> {
  const query = new URLSearchParams();
  if (params.reviewed_by_human !== undefined) {
    query.append("reviewed_by_human", String(params.reviewed_by_human));
  }
  if (params.limit !== undefined) query.append("limit", String(params.limit));
  if (params.offset !== undefined) query.append("offset", String(params.offset));
  if (params.site) query.append("site", params.site);

  const url = `${API_BASE_URL}/api/v1/incidents${query.toString() ? `?\${query.toString()}` : ""}`;
  const response = await fetch(url);
  return handleResponse<IncidentResponse[]>(response, "Failed to list incidents");
}

export async function reviewIncident(
  incidentId: number,
  payload: IncidentReviewPayload
): Promise<IncidentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/incidents/${incidentId}/review`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<IncidentResponse>(response, "Failed to review incident");
}

// Changed to match the incidents router paths
export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v1/incidents/summary`);
  return handleResponse<AnalyticsSummary>(response, "Failed to fetch analytics summary");
}

export async function getSiteAnalytics(): Promise<SiteAnalyticsItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/incidents/sites`);
  return handleResponse<SiteAnalyticsItem[]>(response, "Failed to fetch site analytics");
}

export async function getPatternAnalytics(): Promise<PatternAnalyticsItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/incidents/patterns`);
  return handleResponse<PatternAnalyticsItem[]>(response, "Failed to fetch pattern analytics");
}