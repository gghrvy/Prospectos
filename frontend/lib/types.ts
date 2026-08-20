// Mirrors backend/app/models/enums.py and backend/app/schemas/*.py exactly.
// Keep in sync by hand — there is no codegen step in this project.

export const WEBSITE_STATUSES = ["exists", "not_found", "unreachable"] as const;
export type WebsiteStatus = (typeof WEBSITE_STATUSES)[number];

export const QUALITY_CATEGORIES = [
  "EXCELLENT",
  "GOOD",
  "AVERAGE",
  "WEAK",
  "POOR",
  "CRITICAL",
] as const;
export type QualityCategory = (typeof QUALITY_CATEGORIES)[number];

export const OPPORTUNITY_TYPES = [
  "NO_WEBSITE",
  "WEBSITE_REDESIGN",
  "MOBILE_IMPROVEMENT",
  "CONVERSION_IMPROVEMENT",
  "LEAD_CAPTURE",
  "AI_CHATBOT",
  "FAQ_AUTOMATION",
  "BOOKING_AUTOMATION",
  "CUSTOMER_SUPPORT_AUTOMATION",
  "ANALYTICS",
  "FULL_DIGITAL_UPGRADE",
  "CUSTOM_AI_AUTOMATION",
] as const;
export type OpportunityType = (typeof OPPORTUNITY_TYPES)[number];

export const PACKAGE_TYPES = ["STANDARD", "FULL", "CUSTOM"] as const;
export type PackageType = (typeof PACKAGE_TYPES)[number];

export const OUTREACH_ANGLES = [
  "NEW_WEBSITE",
  "WEBSITE_REDESIGN",
  "MOBILE_IMPROVEMENT",
  "AI_CHATBOT",
  "BOOKING",
  "LEAD_CAPTURE",
  "FULL_DIGITAL_UPGRADE",
] as const;
export type OutreachAngle = (typeof OUTREACH_ANGLES)[number];

export const LEAD_STATUSES = [
  "NEW",
  "AUDITED",
  "QUALIFIED",
  "CONTACTED",
  "FOLLOW_UP",
  "REPLIED",
  "DEMO_SENT",
  "CALL_BOOKED",
  "PROPOSAL",
  "WON",
  "LOST",
  "NOT_INTERESTED",
] as const;
export type LeadStatus = (typeof LEAD_STATUSES)[number];

export const BUSINESS_SOURCES = ["openstreetmap", "csv", "manual"] as const;
export type BusinessSource = (typeof BUSINESS_SOURCES)[number];

export interface Business {
  id: string;
  name: string;
  category: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  social_url: string | null;
  source: string | null;
  source_url: string | null;
  google_maps_url: string | null;
  rating: number | null;
  review_count: number | null;
  website_status: string | null;
  created_at: string;
  updated_at: string;
}

export interface BusinessListItem extends Business {
  latest_opportunity_score: number | null;
  latest_quality_category: string | null;
  current_status: string | null;
}

export interface BusinessCreateInput {
  name: string;
  category?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  source?: string | null;
  source_url?: string | null;
  google_maps_url?: string | null;
  rating?: number | null;
  review_count?: number | null;
  website_status?: string | null;
}

export interface WebsiteAudit {
  id: string;
  business_id: string;
  url: string | null;
  http_status: number | null;
  https_enabled: boolean | null;
  title: string | null;
  meta_description: string | null;
  page_count: number | null;
  crawl_depth: number | null;
  has_viewport: boolean | null;
  has_contact_form: boolean | null;
  has_email: boolean | null;
  has_phone: boolean | null;
  has_booking: boolean | null;
  has_faq: boolean | null;
  has_live_chat: boolean | null;
  has_ai_chatbot: boolean | null;
  has_whatsapp: boolean | null;
  has_social_links: boolean | null;
  discovered_email: string | null;
  broken_link_count: number | null;
  mobile_score: number | null;
  design_score: number | null;
  technical_score: number | null;
  content_score: number | null;
  conversion_score: number | null;
  customer_experience_score: number | null;
  website_quality_score: number | null;
  ai_opportunity_score: number | null;
  redesign_opportunity_score: number | null;
  overall_opportunity_score: number | null;
  quality_category: string | null;
  opportunity_types: string[] | null;
  audit_summary: string | null;
  opportunity_reasons: string[] | null;
  screenshot_desktop_path: string | null;
  screenshot_mobile_path: string | null;
  created_at: string;
}

export interface Outreach {
  id: string;
  business_id: string;
  angle: string | null;
  subject: string | null;
  body: string | null;
  generated_by: string | null;
  sender_id: string | null;
  sender_name: string | null;
  sender_title: string | null;
  sender_email: string | null;
  sender_phone: string | null;
  sender_portfolio_url: string | null;
  created_at: string;
}

export interface Sender {
  id: string;
  name: string;
  title: string | null;
  email: string | null;
  phone: string | null;
  portfolio_url: string | null;
  created_at: string;
}

export interface SenderCreateInput {
  name: string;
  title?: string | null;
  email?: string | null;
  phone?: string | null;
  portfolio_url?: string | null;
}

export type ContractType = "SERVICE_AGREEMENT" | "NDA" | "WELCOME_PACKET";

export const CONTRACT_TYPE_LABELS: Record<ContractType, string> = {
  SERVICE_AGREEMENT: "Service Agreement",
  NDA: "NDA",
  WELCOME_PACKET: "Welcome Packet",
};

export interface Contract {
  id: string;
  business_id: string;
  contract_type: ContractType;
  content: string;
  studio_name: string | null;
  project_description: string | null;
  price_amount: number | null;
  currency: string | null;
  deposit_percent: number | null;
  sender_id: string | null;
  sender_name: string | null;
  sender_title: string | null;
  sender_email: string | null;
  sender_phone: string | null;
  sender_portfolio_url: string | null;
  created_at: string;
}

export interface ContractGenerateRequest {
  contract_type: ContractType;
  sender_id?: string | null;
  studio_name?: string | null;
  project_description?: string | null;
  price_amount?: number | null;
  currency?: string;
  deposit_percent?: number;
}

export interface LeadStatusHistoryEntry {
  id: string;
  business_id: string;
  status: string;
  note: string | null;
  changed_by: string | null;
  created_at: string;
}

export interface Note {
  id: string;
  business_id: string;
  content: string;
  author: string | null;
  created_at: string;
}

export interface BusinessDetail extends Business {
  current_status: string | null;
  latest_audit: WebsiteAudit | null;
  audits: WebsiteAudit[];
  outreach_drafts: Outreach[];
  contracts: Contract[];
  status_history: LeadStatusHistoryEntry[];
  notes: Note[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface DiscoveredBusiness {
  name: string;
  category: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  social_url: string | null;
  source: string;
  source_url: string | null;
  google_maps_url: string | null;
  rating: number | null;
  review_count: number | null;
}

export interface OSMSearchRequest {
  category?: string;
  city?: string | null;
  country?: string | null;
  radius_km?: number;
  limit?: number;
  save?: boolean;
  latitude?: number | null;
  longitude?: number | null;
}

export interface GeocodeResult {
  latitude: number;
  longitude: number;
  display_name: string;
}

export interface CSVImportResult {
  total_rows: number;
  imported: number;
  skipped_duplicates: number;
  businesses: Business[];
}

export interface OutreachGenerateRequest {
  angle?: string | null;
  sender_id?: string | null;
}

export interface LeadStatusChangeInput {
  status: LeadStatus;
  note?: string | null;
  changed_by?: string | null;
}

export interface NoteCreateInput {
  content: string;
  author?: string | null;
}

// UI-only helper labels — not part of the API contract.
export const LEAD_STATUS_LABELS: Record<string, string> = {
  NEW: "New",
  AUDITED: "Audited",
  QUALIFIED: "Qualified",
  CONTACTED: "Contacted",
  FOLLOW_UP: "Follow-up",
  REPLIED: "Replied",
  DEMO_SENT: "Demo sent",
  CALL_BOOKED: "Call booked",
  PROPOSAL: "Proposal",
  WON: "Won",
  LOST: "Lost",
  NOT_INTERESTED: "Not interested",
};

export const OPPORTUNITY_TYPE_LABELS: Record<string, string> = {
  NO_WEBSITE: "No website",
  WEBSITE_REDESIGN: "Website redesign",
  MOBILE_IMPROVEMENT: "Mobile improvement",
  CONVERSION_IMPROVEMENT: "Conversion improvement",
  LEAD_CAPTURE: "Lead capture",
  AI_CHATBOT: "AI chatbot",
  FAQ_AUTOMATION: "FAQ automation",
  BOOKING_AUTOMATION: "Booking automation",
  CUSTOMER_SUPPORT_AUTOMATION: "Customer support automation",
  ANALYTICS: "Analytics",
  FULL_DIGITAL_UPGRADE: "Full digital upgrade",
  CUSTOM_AI_AUTOMATION: "Custom AI automation",
};
