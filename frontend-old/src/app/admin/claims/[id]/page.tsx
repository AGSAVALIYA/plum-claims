'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ClaimResponse, ClaimEvent, ClaimRetryAttempt } from '@/types';
import * as api from '@/lib/api';
import { isAdmin } from '@/lib/auth';
import DecisionBadge from '@/components/ui/DecisionBadge';
import StatusBadge from '@/components/ui/StatusBadge';
import MetricCard from '@/components/ui/MetricCard';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import FailureReasonCard from '@/components/claims/FailureReasonCard';
import LineItemsTable from '@/components/claims/LineItemsTable';
import ProcessingTraceViewer from '@/components/claims/ProcessingTraceViewer';
import DocumentList from '@/components/claims/DocumentList';

const STEP_NAMES = [
  'Document Verification',
  'Document Extraction',
  'Policy Evaluation',
  'Fraud Detection',
  'Decision Aggregation',
];

export default function AdminClaimDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [mounted, setMounted] = useState(false);
  const [claim, setClaim] = useState<ClaimResponse | null>(null);
  const [events, setEvents] = useState<ClaimEvent[]>([]);
  const [retries, setRetries] = useState<ClaimRetryAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Admin actions
  const [overrideDecision, setOverrideDecision] = useState('');
  const [overrideComment, setOverrideComment] = useState('');
  const [overrideAmount, setOverrideAmount] = useState('');
  const [adminComment, setAdminComment] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [rerunLoading, setRerunLoading] = useState(false);
  const [rerunSuccess, setRerunSuccess] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [claimData, eventsData, retriesData] = await Promise.all([
        api.getAdminClaimDetail(parseInt(id)),
        api.getClaimEvents(parseInt(id)),
        api.getClaimRetries(parseInt(id)),
      ]);
      setClaim(claimData);
      setEvents(eventsData);
      setRetries(retriesData);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load claim');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id || !isAdmin()) return;
    fetchAll();
  }, [id, fetchAll]);

  // Auto-poll while processing (after rerun)
  useEffect(() => {
    if (claim && (claim.status === 'SUBMITTED' || claim.status === 'PROCESSING' || claim.status === 'VALIDATING')) {
      const interval = setInterval(fetchAll, 3000);
      return () => clearInterval(interval);
    }
  }, [claim?.status, fetchAll]);

  const handleOverride = async () => {
    if (!overrideDecision) return;
    setActionLoading(true);
    setActionSuccess(null);
    setError(null);
    try {
      await api.adminOverride(
        parseInt(id),
        overrideDecision,
        overrideComment || undefined,
        overrideAmount ? parseFloat(overrideAmount) : undefined
      );
      setActionSuccess('Decision overridden successfully.');
      setOverrideDecision('');
      setOverrideComment('');
      setOverrideAmount('');
      await fetchAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Override failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleComment = async () => {
    if (!adminComment.trim()) return;
    setActionLoading(true);
    setActionSuccess(null);
    setError(null);
    try {
      await api.adminComment(parseInt(id), adminComment);
      setActionSuccess('Comment added successfully.');
      setAdminComment('');
      await fetchAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comment failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRerun = async () => {
    setRerunLoading(true);
    setRerunSuccess(false);
    setError(null);
    try {
      await api.adminRerunClaim(parseInt(id));
      setRerunSuccess(true);
      await fetchAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Rerun failed');
    } finally {
      setRerunLoading(false);
    }
  };

  const formatAmount = (amount?: number) =>
    amount != null ? `₹${amount.toLocaleString()}` : '—';

  // Prevent hydration mismatch: don't render auth-dependent content until mounted
  if (!mounted) {
    return <LoadingSpinner message={`Loading claim #${id}…`} />;
  }

  if (!isAdmin()) {
    return (
      <div className="p-10 text-center">
        <span className="text-5xl block mb-4" aria-hidden="true">🔒</span>
        <h1 className="text-2xl font-bold text-[var(--color-danger-600)] mb-2">Access Denied</h1>
        <p className="text-[var(--color-text-secondary)]">Admin access required.</p>
      </div>
    );
  }

  if (loading) return <LoadingSpinner message={`Loading claim #${id}…`} />;
  if (error)
    return (
      <div className="p-8 text-center">
        <p className="text-[var(--color-danger-600)] text-lg font-semibold mb-2">Error</p>
        <p className="text-[var(--color-text-secondary)]">{error}</p>
        <Link href="/admin" className="mt-4 inline-block text-sm font-semibold text-[var(--color-primary-600)] hover:underline">
          ← Back to Admin Dashboard
        </Link>
      </div>
    );
  if (!claim)
    return (
      <div className="p-8 text-center">
        <p className="text-[var(--color-text-muted)] text-lg">Claim not found</p>
        <Link href="/admin" className="mt-4 inline-block text-sm font-semibold text-[var(--color-primary-600)] hover:underline">
          ← Back to Admin Dashboard
        </Link>
      </div>
    );

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb">
        <Link
          href="/admin"
          className="text-sm text-[var(--color-primary-600)] hover:text-[var(--color-primary-800)] transition-colors duration-150 font-medium"
        >
          ← Back to Admin Dashboard
        </Link>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            Claim #{claim.claim_id}
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">
            {claim.member_id} — {claim.claim_category?.replace(/_/g, ' ')}
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <StatusBadge status={claim.status} />
          <DecisionBadge decision={claim.decision || claim.status} />
        </div>
      </div>

      {/* Success message */}
      {actionSuccess && (
        <div className="bg-[var(--color-success-50)] border border-[var(--color-success-100)] rounded-xl p-4">
          <div className="flex items-center gap-2">
            <span aria-hidden="true">✅</span>
            <p className="text-sm font-semibold text-[var(--color-success-700)]">{actionSuccess}</p>
          </div>
        </div>
      )}

      {/* Metrics — admin keeps all 3 including confidence */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard label="Claimed Amount" value={formatAmount(claim.claimed_amount)} />
        <MetricCard
          label="Approved Amount"
          value={formatAmount(claim.approved_amount)}
          valueClassName="text-[var(--color-success-700)]"
        />
        <MetricCard
          label="Confidence"
          value={`${((claim.confidence_score ?? 0) * 100).toFixed(0)}%`}
          valueClassName="text-[var(--color-primary-600)]"
        />
      </div>

      {/* Decision Reason */}
      {claim.decision_reason && (
        <div className="bg-[var(--color-info-50)] border border-[var(--color-info-100)] rounded-xl p-4 sm:p-5">
          <div className="flex items-start gap-3">
            <span className="text-lg shrink-0" aria-hidden="true">ℹ️</span>
            <div>
              <p className="text-sm font-semibold text-[var(--color-info-700)]">Decision Reason</p>
              <p className="text-sm text-[var(--color-info-700)] mt-1">{claim.decision_reason}</p>
            </div>
          </div>
        </div>
      )}

      {/* Document Errors (admin sees technical details) */}
      <FailureReasonCard
        documentErrors={claim.document_errors}
        decisionReason={
          claim.status === 'DOCUMENT_ERROR' || claim.status === 'ERROR'
            ? claim.decision_reason
            : undefined
        }
        documents={claim.documents}
      />

      {/* Admin Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rerun Full Flow */}
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-warning-200)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-2">Rerun Full Pipeline</h2>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">
            Reset this claim and re-process it through the entire pipeline from scratch.
            All existing processing steps, decisions, and extracted data will be cleared.
          </p>
          {rerunSuccess && (
            <div className="bg-[var(--color-success-50)] border border-[var(--color-success-100)] rounded-lg p-3.5 mb-4">
              <div className="flex items-center gap-2">
                <span aria-hidden="true">✅</span>
                <p className="text-sm font-semibold text-[var(--color-success-700)]">
                  Claim queued for re-processing. The page will auto-refresh.
                </p>
              </div>
            </div>
          )}
          <button
            onClick={handleRerun}
            disabled={rerunLoading}
            className="w-full rounded-xl bg-amber-600 px-5 py-3 text-sm font-bold text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 min-h-[48px] flex items-center justify-center gap-2 shadow-sm"
          >
            {rerunLoading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Rerunning…
              </>
            ) : (
              <>
                <span aria-hidden="true">🔄</span>
                Rerun Full Flow
              </>
            )}
          </button>
        </div>

        {/* Override Decision */}
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">Override Decision</h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="override-decision" className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
                New Decision
              </label>
              <select
                id="override-decision"
                value={overrideDecision}
                onChange={(e) => setOverrideDecision(e.target.value)}
                className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150"
              >
                <option value="">Select decision…</option>
                <option value="APPROVED">Approved</option>
                <option value="REJECTED">Rejected</option>
                <option value="MANUAL_REVIEW">Manual Review</option>
              </select>
            </div>
            <div>
              <label htmlFor="override-amount" className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
                Approved Amount
                <span className="text-[var(--color-text-muted)] font-normal ml-1">(optional)</span>
              </label>
              <input
                id="override-amount"
                type="number"
                value={overrideAmount}
                onChange={(e) => setOverrideAmount(e.target.value)}
                placeholder="Override amount"
                className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150"
              />
            </div>
            <div>
              <label htmlFor="override-comment" className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
                Comment
              </label>
              <textarea
                id="override-comment"
                value={overrideComment}
                onChange={(e) => setOverrideComment(e.target.value)}
                placeholder="Reason for override…"
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150 resize-y"
                rows={3}
              />
            </div>
            <button
              onClick={handleOverride}
              disabled={!overrideDecision || actionLoading}
              className="w-full rounded-xl bg-purple-600 px-5 py-3 text-sm font-bold text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 min-h-[48px] flex items-center justify-center gap-2 shadow-sm"
            >
              {actionLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Processing…
                </>
              ) : (
                'Override Decision'
              )}
            </button>
          </div>
        </div>

        {/* Add Comment */}
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">Add Internal Note</h2>
          <div className="space-y-4">
            <textarea
              value={adminComment}
              onChange={(e) => setAdminComment(e.target.value)}
              placeholder="Add an internal note or comment about this claim…"
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150 resize-y"
              rows={6}
            />
            <button
              onClick={handleComment}
              disabled={!adminComment.trim() || actionLoading}
              className="w-full rounded-xl bg-[var(--color-primary-500)] px-5 py-3 text-sm font-bold text-white hover:bg-[var(--color-primary-600)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 min-h-[48px] flex items-center justify-center gap-2 shadow-sm"
            >
              {actionLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Adding…
                </>
              ) : (
                'Add Comment'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Processing Progress Timeline — admin keeps this */}
      {claim.processing_trace?.steps && claim.processing_trace.steps.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">Processing Progress</h2>
          <div className="space-y-3">
            {STEP_NAMES.map((stepName, index) => {
              const step = claim.processing_trace?.steps?.find((s) => s.step_index === index);
              const status = step?.status || 'PENDING';
              const isCurrent = claim.status === 'PROCESSING' && !step;
              const statusIcon =
                status === 'COMPLETED' ? '✅' :
                status === 'FAILED' ? '❌' :
                isCurrent ? '⏳' : '⏸️';
              const statusColor =
                status === 'COMPLETED' ? 'border-[var(--color-success-100)] bg-[var(--color-success-50)]' :
                status === 'FAILED' ? 'border-[var(--color-danger-100)] bg-[var(--color-danger-50)]' :
                isCurrent ? 'border-[var(--color-warning-100)] bg-[var(--color-warning-50)] animate-pulse' :
                'border-[var(--color-border)] bg-[var(--color-surface-muted)]';

              return (
                <div key={index} className={`flex items-center gap-3 p-3 rounded-lg border ${statusColor}`}>
                  <span className="text-lg" aria-hidden="true">{statusIcon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-[var(--color-text-primary)]">{stepName}</p>
                    {step?.duration_ms && (
                      <p className="text-xs text-[var(--color-text-muted)] font-mono">{step.duration_ms}ms</p>
                    )}
                    {step?.error_message && (
                      <p className="text-xs text-[var(--color-danger-600)] mt-1">{step.error_message}</p>
                    )}
                  </div>
                  <span className="text-xs font-medium text-[var(--color-text-muted)]">{status}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Complete Event History — admin keeps this */}
      {events.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">Complete Event History</h2>
          <div className="space-y-3">
            {events.map((event, i) => (
              <div key={event.event_id} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-3 h-3 rounded-full mt-1.5 shrink-0 ${
                      event.event_type === 'STEP_FAILED' ? 'bg-[var(--color-danger-500)]' :
                      event.event_type === 'DECISION_MADE' ? 'bg-[var(--color-success-500)]' :
                      event.event_type === 'ADMIN_OVERRIDE' ? 'bg-purple-500' :
                      event.event_type === 'COMMENT_ADDED' ? 'bg-[var(--color-primary-500)]' :
                      'bg-[var(--color-info-500)]'
                    }`}
                    aria-hidden="true"
                  />
                  {i < events.length - 1 && <div className="w-0.5 flex-1 bg-[var(--color-border)] mt-1" />}
                </div>
                <div className={`pb-4 flex-1 ${i === events.length - 1 ? 'pb-0' : ''}`}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                      {event.event_type.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                    </span>
                  </div>
                  {event.previous_status && event.new_status && (
                    <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                      {event.previous_status} → {event.new_status}
                    </p>
                  )}
                  {event.comment && (
                    <p className="text-sm text-[var(--color-text-secondary)] mt-1.5 bg-[var(--color-surface-muted)] rounded-lg p-2.5">
                      {event.comment}
                    </p>
                  )}
                  {event.actor_type && (
                    <p className="text-xs text-[var(--color-text-muted)] mt-1">
                      by {event.actor_type}
                      {event.actor_id ? ` (${event.actor_id})` : ''}
                    </p>
                  )}
                  {event.metadata && Object.keys(event.metadata).length > 0 && (
                    <pre className="text-xs text-[var(--color-text-muted)] mt-1.5 bg-[var(--color-surface-muted)] rounded-lg p-2.5 overflow-x-auto border border-[var(--color-border)]">
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retry History — admin keeps this */}
      {retries.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">Retry History</h2>
          <div className="space-y-3">
            {retries.map((retry) => (
              <div key={retry.retry_id} className="border border-[var(--color-border)] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                    Attempt #{retry.attempt_number}
                  </span>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                      retry.result_status === 'SUCCEEDED' ? 'bg-[var(--color-success-100)] text-[var(--color-success-700)]' :
                      retry.result_status === 'FAILED' ? 'bg-[var(--color-danger-100)] text-[var(--color-danger-700)]' :
                      retry.result_status === 'PROCESSING' ? 'bg-[var(--color-warning-100)] text-[var(--color-warning-700)]' :
                      'bg-[var(--color-surface-muted)] text-[var(--color-text-muted)]'
                    }`}
                  >
                    {retry.result_status}
                  </span>
                </div>
                {retry.retry_reason && (
                  <p className="text-sm text-[var(--color-text-secondary)]">{retry.retry_reason}</p>
                )}
                <div className="flex gap-4 mt-2 text-xs text-[var(--color-text-muted)]">
                  <span>By: {retry.requested_by}</span>
                  <span>At: {retry.requested_at ? new Date(retry.requested_at).toLocaleString() : '—'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Line Items */}
      {claim.line_items && claim.line_items.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-4 sm:p-6">
          <LineItemsTable lineItems={claim.line_items} />
        </div>
      )}

      {/* Processing Trace (detailed) — admin keeps this */}
      {claim.processing_trace?.steps && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-4 sm:p-6">
          <ProcessingTraceViewer steps={claim.processing_trace.steps} />
        </div>
      )}

      {/* Documents */}
      {claim.documents && claim.documents.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-4 sm:p-6">
          <DocumentList documents={claim.documents} />
        </div>
      )}
    </div>
  );
}
