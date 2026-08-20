import type {
  Business,
  BusinessCreateInput,
  BusinessDetail,
  BusinessListItem,
  Contract,
  ContractGenerateRequest,
  CSVImportResult,
  DiscoveredBusiness,
  GeocodeResult,
  LeadStatusChangeInput,
  LeadStatusHistoryEntry,
  NoteCreateInput,
  Note,
  OSMSearchRequest,
  Outreach,
  OutreachGenerateRequest,
  PaginatedResponse,
  Sender,
  SenderCreateInput,
  WebsiteAudit,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers:
      options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json", ...options.headers }
        : options.headers,
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      message = data.detail ? JSON.stringify(data.detail) : JSON.stringify(data);
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, message || `Request to ${path} failed`);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

function toQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export interface ListBusinessesParams {
  [key: string]: string | number | undefined;
  category?: string;
  city?: string;
  website_status?: string;
  search?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  listBusinesses: (params: ListBusinessesParams = {}) =>
    request<PaginatedResponse<BusinessListItem>>(`/api/businesses${toQueryString(params)}`),

  getBusiness: (id: string) => request<BusinessDetail>(`/api/businesses/${id}`),

  createBusiness: (payload: BusinessCreateInput) =>
    request<Business>("/api/businesses", { method: "POST", body: JSON.stringify(payload) }),

  updateBusiness: (id: string, payload: Partial<BusinessCreateInput>) =>
    request<Business>(`/api/businesses/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),

  deleteBusiness: (id: string) => request<void>(`/api/businesses/${id}`, { method: "DELETE" }),

  runAudit: (id: string) => request<WebsiteAudit>(`/api/businesses/${id}/audit`, { method: "POST" }),

  generateOutreach: (id: string, payload: OutreachGenerateRequest = {}) =>
    request<Outreach>(`/api/businesses/${id}/outreach`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  addNote: (id: string, payload: NoteCreateInput) =>
    request<Note>(`/api/businesses/${id}/notes`, { method: "POST", body: JSON.stringify(payload) }),

  changeStatus: (id: string, payload: LeadStatusChangeInput) =>
    request<LeadStatusHistoryEntry>(`/api/businesses/${id}/status`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  searchOSM: (payload: OSMSearchRequest) =>
    request<DiscoveredBusiness[] | Business[]>("/api/businesses/search", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  searchCategories: () => request<{ categories: string[] }>("/api/businesses/search/categories"),

  saveBusinesses: (businesses: DiscoveredBusiness[]) =>
    request<Business[]>("/api/businesses/save", {
      method: "POST",
      body: JSON.stringify({ businesses }),
    }),

  listSenders: () => request<Sender[]>("/api/senders"),

  createSender: (payload: SenderCreateInput) =>
    request<Sender>("/api/senders", { method: "POST", body: JSON.stringify(payload) }),

  deleteSender: (id: string) => request<void>(`/api/senders/${id}`, { method: "DELETE" }),

  generateContract: (id: string, payload: ContractGenerateRequest) =>
    request<Contract>(`/api/businesses/${id}/contract`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  geocode: (place: string) =>
    request<GeocodeResult>("/api/businesses/search/geocode", {
      method: "POST",
      body: JSON.stringify({ place }),
    }),

  importCSV: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<CSVImportResult>("/api/businesses/import-csv", {
      method: "POST",
      body: formData,
    });
  },

  exportCSVUrl: () => `${API_BASE_URL}/api/businesses/export-csv`,

  screenshotUrl: (path: string | null) => {
    if (!path) return null;
    const filename = path.split(/[\\/]/).pop();
    return filename ? `${API_BASE_URL}/screenshots/${filename}` : null;
  },
};
