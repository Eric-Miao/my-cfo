const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: "ok";
  service: string;
  environment: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export interface AuthState {
  authenticated: boolean;
  principal?: "admin";
}

export interface HouseholdOverview {
  official_base_currency: string;
  display_currency: string;
  display_values_are_estimates: boolean;
  current: null | {
    group_id: string;
    revision_id: string;
    reporting_at: string;
    net_worth_official: string;
    total_assets_official: string;
    total_liabilities_official: string;
    net_worth_display: string;
  };
}

export interface LatestGroupDetail {
  group_id: string | null;
  revision_id: string | null;
  members: Array<{
    owner_id: string;
    owner_name: string;
    owner_snapshot_id: string;
    asset_total_official: string;
    liability_total_official: string;
    net_worth_official: string;
  }>;
}

export function login(password: string): Promise<AuthState> {
  return request<AuthState>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export function logout(): Promise<AuthState> {
  return request<AuthState>("/api/v1/auth/logout", { method: "POST" });
}

export function fetchMe(): Promise<AuthState> {
  return request<AuthState>("/api/v1/auth/me");
}

export function fetchHouseholdOverview(): Promise<HouseholdOverview> {
  return request<HouseholdOverview>("/api/v1/dashboard/household-overview");
}

export function fetchLatestGroupDetail(): Promise<LatestGroupDetail> {
  return request<LatestGroupDetail>("/api/v1/dashboard/latest-group-detail");
}
