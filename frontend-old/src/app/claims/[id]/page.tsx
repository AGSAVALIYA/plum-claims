'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ClaimResponse } from '@/types';
import * as api from '@/lib/api';
import DecisionBadge from '@/components/ui/DecisionBadge';
import StatusBadge from '@/components/ui/StatusBadge';
import MetricCard from '@/components/ui/MetricCard';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import FailureReasonCard from '@/components/claims/FailureReasonCard';
import CustomFileUploader, { type UploadedFileEntry } from '@/components/ui/CustomFileUploader';
import LineItemsTable from '@/components/claims/LineItemsTable';
import DocumentList from '@/components/claims/DocumentList';

export default function ClaimDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [claim, setClaim] = useState<ClaimResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Retry state
  const [retryFiles, setRetryFiles] = useState<UploadedFileEntry[]>([]);
  const [retryComment, setRetryComment] = useState('');
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);
  const [retrySuccess, setRetrySuccess] = useState(false);

  const fetchClaim = useCallback(async () => {
    try {
      const claimData = await api.getClaim(parseInt(id));
      setClaim(claimData);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load claim');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;
    fetchClaim();
  }, [id, fetchClaim]);

  // Auto-poll while processing
  useEffect(() => {
    if (claim && (claim.status === 'SUBMITTED' || claim.status === 'PROCESSING' || claim.status === 'VALIDATING')) {
      const interval = setInterval(fetchClaim, 3000);
      return () => clearInterval(interval);
    }
  }, [claim?.status, fetchClaim]);

  const handleRetry = async () => {
    setRetrying(true);
    setRetryError(null);
    setRetrySuccess(false);
    try {
      if (retryFiles.length > 0) {
        await api.retryClaimWithFiles(
          parseInt(id),
          retryFiles.map((f) => f.file),
          retryFiles.map((f) => f.document_type),
          retryComment || undefined
        );
      } else {
        await api.retryClaim(parseInt(id), retryComment || undefined);
      }
      setRetrySuccess(true);
      setRetryComment('');
      setRetryFiles([]);
      await fetchClaim();
    } catch (e) {
      setRetryError(e instanceof Error ? e.message : 'Retry failed');
    } finally {
      setRetrying(false);
    }
  };

  const isRetryable =
    claim && ['DOCUMENT_ERROR', 'ERROR', 'REJECTED'].includes(claim.status);

  const formatAmount = (amount?: number) =>
    amount != null ? `₹${amount.toLocaleString()}` : '—';

  if (loading) return <LoadingSpinner message={`Loading claim #${id}…`} />;
  if (error)
    return (
      <div className="p-8 text-center">
        <p className="text-[var(--color-danger-600)] text-lg font-semibold mb-2">Error</p>
        <p className="text-[var(--color-text-secondary)]">{error}</p>
        <Link href="/claims" className="mt-4 inline-block text-sm font-semibold text-[var(--color-primary-600)] hover:underline">
          ← Back to My Claims
        </Link>
      </div>
    );
  if (!claim)
    return (
      <div className="p-8 text-center">
        <p className="text-[var(--color-text-muted)] text-lg">Claim not found</p>
        <Link href="/claims" className="mt-4 inline-block text-sm font-semibold text-[var(--color-primary-600)] hover:underline">
          ← Back to My Claims
        </Link>
      </div>
    );

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb">
        <Link
          href="/claims"
          className="text-sm text-[var(--color-primary-600)] hover:text-[var(--color-primary-800)] transition-colors duration-150 font-medium"
        >
          ← Back to My Claims
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

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <MetricCard label="Claimed Amount" value={formatAmount(claim.claimed_amount)} />
        <MetricCard
          label="Approved Amount"
          value={formatAmount(claim.approved_amount)}
          valueClassName="text-[var(--color-success-700)]"
        />
      </div>

      {/* Decision Reason (simplified, non-technical) */}
      {claim.decision_reason && (
        <div className="bg-[var(--color-info-50)] border border-[var(--color-info-100)] rounded-xl p-4 sm:p-5">
          <div className="flex items-start gap-3">
            <span className="text-lg shrink-0" aria-hidden="true">ℹ️</span>
            <div>
              <p className="text-sm font-semibold text-[var(--color-info-700)]">Decision Summary</p>
              <p className="text-sm text-[var(--color-info-700)] mt-1">{claim.decision_reason}</p>
            </div>
          </div>
        </div>
      )}

      {/* Failure Reason Card (only for failed/error claims) */}
      <FailureReasonCard
        documentErrors={claim.document_errors}
        decisionReason={
          claim.status === 'DOCUMENT_ERROR' || claim.status === 'ERROR'
            ? claim.decision_reason
            : undefined
        }
        documents={claim.documents}
      />

      {/* Retry Section with file re-upload */}
      {isRetryable && (
        <div className="bg-[var(--color-warning-50)] border-2 border-[var(--color-warning-100)] rounded-xl p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-warning-700)] mb-2">
            Resubmit Your Claim
          </h2>
          <p className="text-sm text-[var(--color-warning-700)] mb-5">
            There was a problem with your claim. You can upload new or corrected
            documents and try again. If you don&apos;t need to change documents, just
            add an optional note and click retry.
          </p>

          {retrySuccess && (
            <div className="bg-[var(--color-success-50)] border border-[var(--color-success-100)] rounded-lg p-3.5 mb-4">
              <div className="flex items-center gap-2">
                <span aria-hidden="true">✅</span>
                <p className="text-sm font-semibold text-[var(--color-success-700)]">
                  Claim resubmitted successfully! Processing has started.
                </p>
              </div>
            </div>
          )}

          {retryError && (
            <div className="bg-[var(--color-danger-50)] border border-[var(--color-danger-100)] rounded-lg p-3.5 mb-4" role="alert">
              <p className="text-sm text-[var(--color-danger-700)]">{retryError}</p>
            </div>
          )}

          <div className="space-y-4">
            {/* File re-upload */}
            <CustomFileUploader
              label="Upload Replacement Documents"
              files={retryFiles}
              onFilesChange={setRetryFiles}
              helperText="Upload corrected or missing documents. Leave empty to retry without new documents."
            />

            {/* Comment */}
            <div>
              <label
                htmlFor="retry-comment"
                className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
              >
                Note
                <span className="text-[var(--color-text-muted)] font-normal ml-1">(optional)</span>
              </label>
              <textarea
                id="retry-comment"
                value={retryComment}
                onChange={(e) => setRetryComment(e.target.value)}
                placeholder="Describe what you changed or any additional information…"
                className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:border-[var(--color-primary-500)] transition-colors duration-150 resize-y"
                rows={3}
              />
            </div>

            {/* Retry button */}
            <button
              onClick={handleRetry}
              disabled={retrying}
              className="rounded-xl bg-[var(--color-warning-500)] px-6 py-3 text-sm font-bold text-white
                hover:bg-[var(--color-warning-700)]
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-150
                min-h-[48px] flex items-center justify-center gap-2
                shadow-sm hover:shadow-md"
            >
              {retrying ? (
                <>
                  <svg
                    className="animate-spin h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Resubmitting…
                </>
              ) : (
                'Resubmit Claim'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Line Items */}
      {claim.line_items && claim.line_items.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-4 sm:p-6">
          <LineItemsTable lineItems={claim.line_items} />
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
