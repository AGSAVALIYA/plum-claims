// API client for Plum Claims backend

const API_BASE = '/api/v1';

interface ApiError {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('plum_token');
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const err = (body as ApiError).error || (body as { detail?: unknown }).detail;
    const message = typeof err === 'string' ? err : (err as Record<string, unknown>)?.message || 'Request failed';
    throw new Error(String(message));
  }
  return response.json() as Promise<T>;
}

import type { ClaimResponse, ClaimSubmitRequest, ProcessingTrace } from '@/types';

export async function submitClaim(request: ClaimSubmitRequest): Promise<{ claim_id: number; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/claims`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(request),
  });
  return handleResponse<{ claim_id: number; status: string; message: string }>(res);
}

export async function submitClaimWithFiles(formData: FormData): Promise<{ claim_id: number; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/claims/upload`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: formData,
  });
  return handleResponse<{ claim_id: number; status: string; message: string }>(res);
}

export async function uploadDocument(file: File, documentType: string): Promise<{
  file_id: string;
  file_name: string;
  file_path: string;
  content_type: string;
  size_bytes: number;
}> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: formData,
  });
  return handleResponse(res);
}

export async function getClaim(claimId: number): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/claims/${claimId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function getClaimTrace(claimId: number): Promise<ProcessingTrace> {
  const res = await fetch(`${API_BASE}/claims/${claimId}/trace`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<ProcessingTrace>(res);
}

export async function listClaims(params?: {
  member_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ claims: ClaimResponse[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.member_id) searchParams.set('member_id', params.member_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const qs = searchParams.toString();
  const res = await fetch(`${API_BASE}/claims${qs ? `?${qs}` : ''}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<{ claims: ClaimResponse[]; total: number }>(res);
}

export async function retryClaim(
  claimId: number,
  comment?: string,
  documents?: Array<{ file_id: string; file_name: string; actual_type: string; quality?: string }>
): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/claims/${claimId}/retry`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ comment, documents: documents || [] }),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function retryClaimWithFiles(
  claimId: number,
  files: File[],
  documentTypes: string[],
  comment?: string
): Promise<ClaimResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  formData.append('document_types', JSON.stringify(documentTypes));
  if (comment) {
    formData.append('comment', comment);
  }

  const res = await fetch(`${API_BASE}/claims/${claimId}/retry/upload`, {
    method: 'POST',
    headers: {
      ...getAuthHeaders(),
    },
    body: formData,
  });
  return handleResponse<ClaimResponse>(res);
}

export async function getClaimEvents(claimId: number): Promise<import('@/types').ClaimEvent[]> {
  const res = await fetch(`${API_BASE}/claims/${claimId}/events`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<import('@/types').ClaimEvent[]>(res);
}

export async function getClaimRetries(claimId: number): Promise<import('@/types').ClaimRetryAttempt[]> {
  const res = await fetch(`${API_BASE}/claims/${claimId}/retries`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<import('@/types').ClaimRetryAttempt[]>(res);
}

// Admin API functions

export async function getAdminDashboard(): Promise<import('@/types').AdminDashboardStats> {
  const res = await fetch(`${API_BASE}/admin/dashboard`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<import('@/types').AdminDashboardStats>(res);
}

export async function getAdminClaims(params?: {
  member_id?: string;
  status?: string;
  decision?: string;
  date_from?: string;
  date_to?: string;
  claim_category?: string;
  limit?: number;
  offset?: number;
}): Promise<{ claims: ClaimResponse[]; total: number }> {
  const searchParams = new URLSearchParams();
  if (params?.member_id) searchParams.set('member_id', params.member_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.decision) searchParams.set('decision', params.decision);
  if (params?.date_from) searchParams.set('date_from', params.date_from);
  if (params?.date_to) searchParams.set('date_to', params.date_to);
  if (params?.claim_category) searchParams.set('claim_category', params.claim_category);
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.offset) searchParams.set('offset', String(params.offset));

  const qs = searchParams.toString();
  const res = await fetch(`${API_BASE}/admin/claims${qs ? `?${qs}` : ''}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<{ claims: ClaimResponse[]; total: number }>(res);
}

export async function getAdminClaimDetail(claimId: number): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function adminOverride(
  claimId: number,
  decision: string,
  comment?: string,
  approvedAmount?: number
): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}/override`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({
      decision,
      comment,
      approved_amount: approvedAmount,
    }),
  });
  return handleResponse<ClaimResponse>(res);
}

export async function adminComment(claimId: number, comment: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}/comment`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ comment }),
  });
  return handleResponse<{ message: string }>(res);
}

/**
 * Get the URL to view/download a document's actual file content by its database document_id.
 * Use this as an <img src={...}> or <a href={...}> to display uploaded documents.
 */
export function getDocumentViewUrl(documentId: number): string {
  return `${API_BASE}/documents/db/${documentId}/view`;
}

export async function adminRerunClaim(claimId: number): Promise<ClaimResponse> {
  const res = await fetch(`${API_BASE}/admin/claims/${claimId}/rerun`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
  });
  return handleResponse<ClaimResponse>(res);
}

export async function getAdminMembers(): Promise<Array<{ member_id: string; name: string; role: string; claim_count: number }>> {
  const res = await fetch(`${API_BASE}/admin/members`, {
    headers: getAuthHeaders(),
  });
  return handleResponse<Array<{ member_id: string; name: string; role: string; claim_count: number }>>(res);
}
