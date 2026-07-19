const BASE_URL = "/api/v1";

export async function getTraces(filters = {}) {
  const params = new URLSearchParams();
  if (filters.search) params.append("search", filters.search);
  if (filters.has_error !== undefined && filters.has_error !== "") {
    params.append("has_error", filters.has_error);
  }
  if (filters.min_duration) {
    params.append("min_duration", filters.min_duration);
  }

  const response = await fetch(`${BASE_URL}/traces/?${params.toString()}`);
  if (!response.ok) throw new Error("Failed to fetch traces");
  return response.json();
}

export async function getTraceDetails(traceId) {
  const response = await fetch(`${BASE_URL}/traces/${traceId}`);
  if (!response.ok) throw new Error("Failed to fetch trace details");
  return response.json();
}

export async function getServiceMap() {
  const response = await fetch(`${BASE_URL}/services/map`);
  if (!response.ok) throw new Error("Failed to fetch service map");
  return response.json();
}

export async function getServiceMetrics() {
  const response = await fetch(`${BASE_URL}/services/metrics`);
  if (!response.ok) throw new Error("Failed to fetch service metrics");
  return response.json();
}
