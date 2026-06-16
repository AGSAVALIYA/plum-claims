import type {
  ClaimCategoryInfo,
  ClaimListResponse,
  ClaimResponse,
  ClaimSubmitAsyncResponse,
  MemberDetail,
  TokenResponse,
  AdminDashboardResponse,
  AdminClaimListResponse,
  ProcessingTraceResponse,
  DocumentResponse,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://plum-backend.akshitgs.me/api/v1';

// ── Helpers ─────────────────────────────────────────────────

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.detail?.error?.message || body?.detail?.message || body?.detail || res.statusText;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  // 204 No Content
  if (res.status === 204) return {} as T;
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────

export async function login(member_id: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ member_id, password }),
  });
  return handleResponse<TokenResponse>(res);
}

export async function register(member_id: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ member_id, password }),
  });
  return handleResponse<TokenResponse>(res);
}

// ── Claims ───────────────────────────────────────────────────

export async function submitClaimWithFiles(formData: FormData): Promise<ClaimSubmitAsyncResponse> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const res = await fetch(`${API_BASE}/claims/upload-and-submit`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  return handleResponse<ClaimSubmitAsyncResponse>(res);
}

export async function getClaim(claimId: number): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/claims/${claimId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function listClaims(params?: {
  member_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<ClaimListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.member_id) searchParams.set('member_id', params.member_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const url = `${API_BASE}/claims${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  return handleResponse<ClaimListResponse>(res);
}

export async function getClaimTrace(claimId: number): Promise<ProcessingTraceResponse> {
  const res = await fetch(`${API_BASE}/claims/${claimId}/trace`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<ProcessingTraceResponse>(res);
}

export async function retryClaim(
  claimId: number,
  data: { comment?: string; documents?: Array<Record<string, unknown>> }
): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/claims/${claimId}/retry`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<ClaimResponse>(res);
}

// ── Documents ────────────────────────────────────────────────

export function getDocumentViewUrl(documentId: number): string {
  return `${API_BASE}/documents/db/${documentId}/view`;
}

export async function getClaimDocuments(claimId: number): Promise<{
  claim_id: number;
  documents: DocumentResponse[];
}> {
  const res = await fetch(`${API_BASE}/documents/claim/${claimId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

// ── Admin ────────────────────────────────────────────────────

function getAdminHeaders(): Record<string, string> {
  return getAuthHeaders();
}

export async function getAdminDashboard(): Promise<AdminDashboardResponse> {
  const res = await fetch(`${API_BASE}/admin/dashboard`, {
    headers: getAdminHeaders(),
  });
  return handleResponse<AdminDashboardResponse>(res);
}

export async function listAdminClaims(params?: {
  member_id?: string;
  status?: string;
  decision?: string;
  claim_category?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}): Promise<AdminClaimListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.member_id) searchParams.set('member_id', params.member_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.decision) searchParams.set('decision', params.decision);
  if (params?.claim_category) searchParams.set('claim_category', params.claim_category);
  if (params?.date_from) searchParams.set('date_from', params.date_from);
  if (params?.date_to) searchParams.set('date_to', params.date_to);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const url = `${API_BASE}/admin/claims${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
  const res = await fetch(url, { headers: getAdminHeaders() });
  return handleResponse<AdminClaimListResponse>(res);
}

export async function getAdminClaim(claimId: number): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}`, {
    headers: getAdminHeaders(),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function adminOverride(
  claimId: number,
  data: { decision: string; comment?: string; approved_amount?: number }
): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}/override`, {
    method: 'POST',
    headers: getAdminHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function adminComment(
  claimId: number,
  comment: string
): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}/comment`, {
    method: 'POST',
    headers: getAdminHeaders(),
    body: JSON.stringify({ comment }),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function listMembers(): Promise<{
  members: Array<{ member_id: string; member_name: string; role: string }>;
}> {
  const res = await fetch(`${API_BASE}/admin/members`, {
    headers: getAdminHeaders(),
  });
  return handleResponse(res);
}

export async function getMemberDetail(memberId: string): Promise<MemberDetail> {
  const res = await fetch(`${API_BASE}/admin/members/${encodeURIComponent(memberId)}`, {
    headers: getAdminHeaders(),
  });
  return handleResponse<MemberDetail>(res);
}

export async function resetMemberPassword(
  memberId: string,
  newPassword: string
): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/admin/members/${encodeURIComponent(memberId)}/reset-password`, {
    method: 'POST',
    headers: getAdminHeaders(),
    body: JSON.stringify({ new_password: newPassword }),
  });
  return handleResponse(res);
}

export async function getPolicy(): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/admin/policy`, {
    headers: getAdminHeaders(),
  });
  return handleResponse(res);
}

export async function getClaimCategories(): Promise<ClaimCategoryInfo[]> {
  const res = await fetch(`${API_BASE}/claims/categories`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<ClaimCategoryInfo[]>(res);
}
