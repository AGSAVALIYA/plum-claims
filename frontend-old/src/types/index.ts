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

export interface DocumentMeta {
  file_id: string;
  file_name: string;
  actual_type: string;
  quality?: string;
  patient_name_on_doc?: string;
  content?: Record<string, unknown>;
}

export interface ClaimSubmitRequest {
  member_id: string;
  policy_id?: string;
  claim_category: ClaimCategory;
  treatment_date: string;
  claimed_amount: number;
  hospital_name?: string;
  ytd_claims_amount?: number;
  documents: DocumentMeta[];
  claims_history?: Record<string, unknown>[];
  simulate_component_failure?: boolean;
}

export interface DocumentError {
  error_type: string;
  document_id?: number | string;
  file_name?: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface LineItemResult {
  description: string;
  amount: number;
  approved_amount?: number;
  is_covered?: boolean;
  rejection_reason?: string;
}

export interface ProcessingStep {
  step_index: number;
  step_name: string;
  agent_name: string;
  status: 'STARTED' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  error_message?: string;
  confidence_score?: number;
  checks_performed?: Array<{
    check: string;
    passed: boolean;
    reason: string;
  }>;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface ProcessingTrace {
  claim_id: number;
  steps: ProcessingStep[];
  started_at?: string;
  completed_at?: string;
  failed_components: string[];
  degraded: boolean;
  all_agents_failed: boolean;
}

export interface ClaimResponse {
  claim_id: number;
  member_id: string;
  policy_id: string;
  claim_category: string;
  treatment_date?: string;
  claimed_amount?: number;
  approved_amount?: number;
  decision?: string;
  decision_reason?: string;
  confidence_score?: number;
  status: string;
  hospital_name?: string;
  manual_review_recommended: boolean;
  degraded_components: string[];
  processing_trace?: ProcessingTrace;
  submitted_at?: string;
  processed_at?: string;
  documents: Array<{
    document_id: number;
    file_name: string;
    document_type?: string;
    verification_status: string;
    quality_score?: number;
    error_message?: string;
  }>;
  line_items: LineItemResult[];
  document_errors?: DocumentError[];
  error_messages?: string[];
}

export interface ClaimEvent {
  event_id: number;
  claim_id: number;
  event_type: string;
  previous_status?: string;
  new_status?: string;
  actor_type: string;
  actor_id?: string;
  comment?: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

export interface ClaimRetryAttempt {
  retry_id: number;
  claim_id: number;
  attempt_number: number;
  retry_reason?: string;
  failed_step_index?: number;
  new_documents?: Record<string, unknown>[];
  requested_by: string;
  requested_at?: string;
  completed_at?: string;
  result_status: string;
}

export interface AdminDashboardStats {
  total_claims: number;
  status_counts: Record<string, number>;
  decision_counts: Record<string, number>;
  avg_confidence: number;
  manual_review_count: number;
  recent_events: Array<{
    event_id: number;
    claim_id: number;
    event_type: string;
    actor_type: string;
    comment?: string;
    created_at?: string;
  }>;
}
