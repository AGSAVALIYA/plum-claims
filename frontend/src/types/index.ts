// ── Enums ───────────────────────────────────────────────────

export type ClaimCategory =
  | 'CONSULTATION'
  | 'DIAGNOSTIC'
  | 'PHARMACY'
  | 'DENTAL'
  | 'VISION'
  | 'ALTERNATIVE_MEDICINE';

export type ClaimStatus =
  | 'SUBMITTED'
  | 'VALIDATING'
  | 'PROCESSING'
  | 'DECIDED'
  | 'DOCUMENT_ERROR'
  | 'ERROR'
  | 'CLOSED';

export type Decision = 'APPROVED' | 'PARTIAL' | 'REJECTED' | 'MANUAL_REVIEW';

export type DocumentType =
  | 'PRESCRIPTION'
  | 'HOSPITAL_BILL'
  | 'LAB_REPORT'
  | 'PHARMACY_BILL'
  | 'DENTAL_REPORT'
  | 'DIAGNOSTIC_REPORT'
  | 'DISCHARGE_SUMMARY';

export type VerificationStatus = 'PENDING' | 'VERIFIED' | 'FAILED' | 'SKIPPED';

export type UserRole = 'member' | 'admin';

// ── API Response Types ──────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  token_type: string;
  member_id: string;
  member_name: string;
  role: UserRole;
}

export interface DocumentResponse {
  document_id: number;
  file_name: string;
  document_type: string | null;
  detected_type: string | null;
  verification_status: VerificationStatus;
  quality_score: number | null;
  patient_name_on_doc: string | null;
  error_message: string | null;
}

export interface LineItemResponse {
  description: string;
  amount: number;
  approved_amount: number | null;
  is_covered: boolean | null;
  rejection_reason: string | null;
}

export interface DocumentErrorResponse {
  error_type: string;
  document_id: number | string | null;
  file_name: string | null;
  message: string;
  details: Record<string, unknown>;
}

export interface ProcessingCheck {
  rule?: string;
  check?: string;
  passed?: boolean;
  reason?: string;
  details?: Record<string, unknown>;
}

export interface ProcessingStepResponse {
  step_index: number;
  step_name: string;
  agent_name: string;
  status: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_message: string | null;
  confidence_score: number | null;
  checks_performed: Array<Record<string, unknown>>;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface ProcessingTraceResponse {
  claim_id: number;
  steps: ProcessingStepResponse[];
  started_at: string | null;
  completed_at: string | null;
  failed_components: string[];
  degraded: boolean;
  all_agents_failed: boolean;
}

export interface ClaimResponse {
  claim_id: number;
  member_id: string;
  policy_id: string;
  claim_category: string;
  treatment_date: string | null;
  claimed_amount: number | null;
  approved_amount: number | null;
  decision: Decision | null;
  decision_reason: string | null;
  confidence_score: number | null;
  status: ClaimStatus;
  hospital_name: string | null;
  manual_review_recommended: boolean;
  degraded_components: string[];
  processing_trace: ProcessingTraceResponse | null;
  submitted_at: string | null;
  processed_at: string | null;
  documents: DocumentResponse[];
  line_items: LineItemResponse[];
  document_errors: DocumentErrorResponse[] | null;
  error_messages: string[] | null;
}

export interface ClaimListResponse {
  claims: ClaimResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface ClaimSubmitAsyncResponse {
  claim_id: number;
  status: string;
  message: string;
}

export interface AdminDashboardResponse {
  total_claims: number;
  status_counts: Record<string, number>;
  decision_counts: Record<string, number>;
  avg_confidence: number;
  manual_review_count: number;
  recent_events: Array<Record<string, unknown>>;
}

export interface AdminClaimListResponse {
  claims: ClaimResponse[];
  total: number;
  limit: number;
  offset: number;
}

// ── App Types ───────────────────────────────────────────────

export interface UploadedFileEntry {
  file: File;
  document_type: DocumentType;
  preview_url?: string;
}

export interface User {
  member_id: string;
  member_name: string;
  role: UserRole;
}

export const CLAIM_CATEGORIES: { value: ClaimCategory; label: string; icon: string }[] = [
  { value: 'CONSULTATION', label: 'Consultation', icon: '🩺' },
  { value: 'DIAGNOSTIC', label: 'Diagnostic', icon: '🔬' },
  { value: 'PHARMACY', label: 'Pharmacy', icon: '💊' },
  { value: 'DENTAL', label: 'Dental', icon: '🦷' },
  { value: 'VISION', label: 'Vision', icon: '👁️' },
  { value: 'ALTERNATIVE_MEDICINE', label: 'Alternative Medicine', icon: '🌿' },
];

export const DOCUMENT_TYPES: DocumentType[] = [
  'PRESCRIPTION',
  'HOSPITAL_BILL',
  'LAB_REPORT',
  'PHARMACY_BILL',
  'DENTAL_REPORT',
  'DIAGNOSTIC_REPORT',
  'DISCHARGE_SUMMARY',
];

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  PRESCRIPTION: 'Prescription',
  HOSPITAL_BILL: 'Hospital Bill',
  LAB_REPORT: 'Lab Report',
  PHARMACY_BILL: 'Pharmacy Bill',
  DENTAL_REPORT: 'Dental Report',
  DIAGNOSTIC_REPORT: 'Diagnostic Report',
  DISCHARGE_SUMMARY: 'Discharge Summary',
};

// ── Policy-aware Categories ──────────────────────────────

export interface ClaimCategoryInfo {
  value: string;
  label: string;
  icon: string;
  sub_limit: number;
  copay_percent: number;
  requires_prescription: boolean;
  requires_pre_auth: boolean;
}

// ── Admin: Member Detail ─────────────────────────────────

export interface MemberDependent {
  member_id: string;
  name: string;
  relationship: string;
  date_of_birth: string | null;
}

export interface MemberClaimsSummary {
  year: number;
  total_claims_count: number;
  total_claims_amount: number;
  approved_claims_count: number;
  approved_claims_amount: number;
  last_claim_date: string | null;
  family_approved_amount: number;
  family_combined_limit: number;
  sessions_used_this_year: number;
  same_day_claim_count: number;
}

export interface MemberDetail {
  member_id: string;
  name: string;
  date_of_birth: string | null;
  gender: string | null;
  relationship: string | null;
  join_date: string | null;
  primary_member_id: string | null;
  role: string;
  claims_summary: MemberClaimsSummary | null;
  dependents: MemberDependent[];
}
