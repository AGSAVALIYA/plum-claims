'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import {
  ArrowLeft,
  Calendar,
  Building,
  ChevronDown,
  DollarSign,
  FileText,
  Clock,
  AlertCircle,
  RefreshCw,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  RotateCcw,
} from 'lucide-react';
import { motion } from 'framer-motion';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
// Tooltip imports removed — using Button title attribute instead
import { getClaim, getClaimDocuments, getDocumentViewUrl, retryClaim } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';
import type {
  ClaimResponse,
  DocumentResponse,
  ProcessingCheck,
  ProcessingStepResponse,
  LineItemResponse,
  DocumentType,
} from '@/types';

// ── Helpers ──────────────────────────────────────────────────

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  PRESCRIPTION: 'Prescription',
  HOSPITAL_BILL: 'Hospital Bill',
  LAB_REPORT: 'Lab Report',
  PHARMACY_BILL: 'Pharmacy Bill',
  DENTAL_REPORT: 'Dental Report',
  DIAGNOSTIC_REPORT: 'Diagnostic Report',
  DISCHARGE_SUMMARY: 'Discharge Summary',
  UNKNOWN: 'Document',
};

const EXTENSION_MAP: Record<string, string> = {
  pdf: 'PDF',
  jpg: 'JPG',
  jpeg: 'JPEG',
  png: 'PNG',
  doc: 'DOC',
  docx: 'DOCX',
  xls: 'XLS',
  xlsx: 'XLSX',
  txt: 'TXT',
};

function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    return new Intl.DateTimeFormat('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return '—';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

function getCategoryLabel(category: string | null | undefined): string {
  if (!category) return 'Claim';
  return category
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function deriveDocumentTypeLabel(doc: DocumentResponse): string {
  if (doc.document_type && doc.document_type !== 'UNKNOWN') {
    return DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type;
  }
  // Derive from file extension
  const ext = doc.file_name.split('.').pop()?.toLowerCase() ?? '';
  const mappedExt = EXTENSION_MAP[ext] ?? ext.toUpperCase();
  return `${mappedExt} Document`;
}

const USER_FRIENDLY_ERROR_MESSAGES: Record<string, string> = {
  PATIENT_MISMATCH:
    "The name on this document doesn't match your records. Please upload documents that clearly show your name as registered in the system.",
  WRONG_DOC_TYPE:
    'This document type is not accepted for this claim. Please check the required document list and upload the correct type.',
  UNREADABLE:
    "We could not read this document clearly. Please upload a clearer, well-lit version so all text is legible.",
  MISSING_REQUIRED:
    'A required document is missing from your submission. Please upload all documents listed as needed for this claim type.',
  EXPIRED:
    'This document appears to be expired. Please upload a current, valid version of the document.',
  FORGED_OR_ALTERED:
    'This document appears to have been altered. Please upload an original, unmodified version.',
  DUPLICATE:
    'A duplicate document was detected. Please upload each document only once.',
  DOCUMENT_ERROR:
    'There was an issue processing this document. Please review and re-upload a corrected version.',
};

function getStatusBadgeConfig(status: string): {
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
  className: string;
} {
  switch (status) {
    case 'APPROVED':
    case 'VERIFIED':
      return {
        variant: 'default',
        className: 'bg-status-approved/10 text-status-approved border-status-approved/20',
      };
    case 'REJECTED':
    case 'PARTIAL':
    case 'FAILED':
    case 'ERROR':
    case 'DOCUMENT_ERROR':
      return { variant: 'destructive', className: '' };
    case 'MANUAL_REVIEW':
      return {
        variant: 'secondary',
        className: 'bg-status-warning/10 text-status-warning border-status-warning/20',
      };
    case 'SKIPPED':
      return { variant: 'outline', className: '' };
    default:
      // PENDING / SUBMITTED / VALIDATING / PROCESSING
      return {
        variant: 'secondary',
        className: 'bg-status-warning/10 text-status-warning border-status-warning/20',
      };
  }
}

function getStepStatusIcon(status: string) {
  switch (status) {
    case 'completed':
    case 'success':
      return CheckCircle2;
    case 'failed':
    case 'error':
      return XCircle;
    default:
      return Clock;
  }
}

function getStepStatusColor(status: string) {
  switch (status) {
    case 'completed':
    case 'success':
      return 'text-status-approved';
    case 'failed':
    case 'error':
      return 'text-destructive';
    default:
      return 'text-status-warning';
  }
}

// ── Skeleton ──────────────────────────────────────────────────

function ClaimDetailSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <div className="h-4 w-16 animate-pulse rounded bg-muted" />
        <div className="h-6 w-48 animate-pulse rounded bg-muted" />
      </div>

      <Card>
        <CardHeader>
          <div className="h-5 w-36 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-4 w-24 animate-pulse rounded bg-muted" />
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-1">
                <div className="h-3 w-16 animate-pulse rounded bg-muted" />
                <div className="h-4 w-24 animate-pulse rounded bg-muted" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="h-5 w-28 animate-pulse rounded bg-muted" />
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-3"
              >
                <div className="size-8 animate-pulse rounded-full bg-muted" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 w-32 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-20 animate-pulse rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Claim Detail Page ────────────────────────────────────────

export default function ClaimDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();

  const claimId = Number(params.id);

  const [claim, setClaim] = useState<ClaimResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryFiles, setRetryFiles] = useState<File[]>([]);
  const [retryComment, setRetryComment] = useState('');
  const [previewDocId, setPreviewDocId] = useState<number | null>(null);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const fetchClaimData = useCallback(async () => {
    if (!user || !claimId) return;
    try {
      setIsLoading(true);
      setError(null);
      setNotFound(false);

      const [claimData, docsData] = await Promise.all([
        getClaim(claimId),
        getClaimDocuments(claimId).catch(() => null),
      ]);

      setClaim(claimData);
      setDocuments(docsData?.documents ?? claimData.documents ?? []);
    } catch (err) {
      if (err instanceof Error) {
        const message = err.message;
        if (
          message.toLowerCase().includes('not found') ||
          message.toLowerCase().includes('404')
        ) {
          setNotFound(true);
        } else {
          setError(message);
        }
      } else {
        setError('Failed to load claim');
      }
    } finally {
      setIsLoading(false);
    }
  }, [user, claimId]);

  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) {
      router.push('/login');
      return;
    }
    if (!claimId || isNaN(claimId)) {
      setNotFound(true);
      setIsLoading(false);
      return;
    }
    fetchClaimData();
  }, [user, isAuthLoading, claimId, router, fetchClaimData]);

  // Auto-polling for in-progress claims
  const POLL_INTERVAL_MS = 3000;
  const MAX_POLLS = 60;
  const pollCountRef = { current: 0 };
  useEffect(() => {
    if (isAuthLoading || !user || !claimId || isNaN(claimId)) return;

    const isInProgress =
      claim?.status === 'SUBMITTED' ||
      claim?.status === 'VALIDATING' ||
      claim?.status === 'PROCESSING';

    if (!isInProgress) return;

    const intervalId = setInterval(async () => {
      pollCountRef.current += 1;
      if (pollCountRef.current >= MAX_POLLS) {
        clearInterval(intervalId);
        return;
      }
      try {
        const [claimData, docsData] = await Promise.all([
          getClaim(claimId),
          getClaimDocuments(claimId).catch(() => null),
        ]);
        setClaim(claimData);
        setDocuments(docsData?.documents ?? claimData.documents ?? []);
        // Stop polling if claim is no longer in progress
        const stillInProgress =
          claimData.status === 'SUBMITTED' ||
          claimData.status === 'VALIDATING' ||
          claimData.status === 'PROCESSING';
        if (!stillInProgress) {
          clearInterval(intervalId);
        }
      } catch {
        // Silently retry on next interval
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, [user, claimId, isAuthLoading, claim?.status]);

  const handleRetry = useCallback(async () => {
    if (!claim) return;
    try {
      setIsRetrying(true);
      // Send retry with comment and document info
      const documents = retryFiles.map((f) => ({
        file_name: f.name,
        file_size: f.size,
        file_type: f.type,
      }));
      await retryClaim(claim.claim_id, {
        comment: retryComment || undefined,
        documents: documents.length > 0 ? documents : undefined,
      });
      setRetryFiles([]);
      setRetryComment('');
      await fetchClaimData();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to retry claim'
      );
    } finally {
      setIsRetrying(false);
    }
  }, [claim, fetchClaimData, retryFiles, retryComment]);

  const togglePreview = useCallback((docId: number) => {
    setPreviewDocId((prev) => (prev === docId ? null : docId));
  }, []);

  const isFailedClaim =
    claim?.status === 'ERROR' ||
    claim?.status === 'DOCUMENT_ERROR';

  // Loading
  if (isLoading || isAuthLoading) {
    return <ClaimDetailSkeleton />;
  }

  // Not found
  if (notFound || (!claim && !error)) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div className="flex size-20 items-center justify-center rounded-full bg-muted">
          <FileText className="size-10 text-muted-foreground/50" />
        </div>
        <div className="flex flex-col items-center gap-1 text-center">
          <h3 className="text-lg font-medium text-foreground">
            Claim not found
          </h3>
          <p className="max-w-xs text-sm text-muted-foreground">
            The claim you are looking for does not exist or has been removed.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => router.push('/claims')}
          className="mt-2"
        >
          Back to Claims
        </Button>
      </div>
    );
  }

  // Error
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <AlertCircle className="size-12 text-destructive/50" />
        <p className="text-sm text-destructive">{error}</p>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push('/claims')}>
            Back to Claims
          </Button>
          <Button variant="default" onClick={fetchClaimData}>
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (!claim) return null;

  const displayStatus = claim.decision ?? claim.status;
  const statusBadgeConfig = getStatusBadgeConfig(claim.decision ?? claim.status);

  return (
    <motion.div
      className="flex flex-col gap-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Back navigation */}
      <button
        onClick={() => router.push('/claims')}
        className="flex w-fit items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-4" />
        Back to Claims
      </button>

      {/* ── Claim Header Card ─────────────────────────────── */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <CardTitle
                className="text-xl font-semibold md:text-2xl"
                style={{ fontFamily: 'var(--font-display)' }}
              >
                Claim #{claim.claim_id}
              </CardTitle>
              <Badge
                variant={statusBadgeConfig.variant}
                className={cn('text-xs', statusBadgeConfig.className)}
              >
                {displayStatus}
              </Badge>
            </div>

            {isFailedClaim && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                disabled={isRetrying}
                className="gap-1.5"
                title="Re-submit this claim for processing"
              >
                <RotateCcw
                  className={cn('size-3.5', isRetrying && 'animate-spin')}
                />
                Retry
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-y-4 gap-x-6 sm:grid-cols-4">
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Category</span>
              <span className="text-sm font-medium">
                {getCategoryLabel(claim.claim_category)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Claimed Amount</span>
              <span className="text-sm font-medium">
                {formatCurrency(claim.claimed_amount)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Approved Amount</span>
              <span className="text-sm font-medium">
                {formatCurrency(claim.approved_amount)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Hospital</span>
              <span className="text-sm font-medium">
                {claim.hospital_name || '—'}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Submitted</span>
              <span className="text-sm font-medium">
                {formatDateTime(claim.submitted_at)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Processed</span>
              <span className="text-sm font-medium">
                {formatDateTime(claim.processed_at)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Treatment Date</span>
              <span className="text-sm font-medium">
                {formatDate(claim.treatment_date)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted-foreground">Confidence</span>
              <span className="text-sm font-medium">
                {claim.confidence_score != null
                  ? `${(claim.confidence_score * 100).toFixed(0)}%`
                  : '—'}
              </span>
            </div>
          </div>

          {/* Decision reason */}
          {claim.decision_reason && (
            <div className="mt-4 rounded-md bg-muted p-3 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Decision reason:</span>{' '}
              {claim.decision_reason}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Processing Indicator ──────────────────────────── */}
      {(claim.status === 'SUBMITTED' ||
        claim.status === 'VALIDATING' ||
        claim.status === 'PROCESSING') && (
        <Card className="border-status-info/30">
          <CardContent className="flex items-center gap-3 py-4">
            <div className="relative flex size-8 shrink-0 items-center justify-center">
              <div className="absolute inset-0 animate-ping rounded-full bg-status-info/30" />
              <RefreshCw className="relative size-4 animate-spin text-status-info" />
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-medium text-foreground">
                Processing your claim...
              </span>
              <span className="text-xs text-muted-foreground">
                Your claim is being reviewed. This page refreshes automatically.
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Error Messages ────────────────────────────────── */}
      {(claim.error_messages && claim.error_messages.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="size-4" />
              Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2">
              {claim.error_messages.map((msg, i) => (
                <li
                  key={i}
                  className="rounded-md bg-destructive/5 px-3 py-2 text-sm text-destructive"
                >
                  {msg}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Document Errors */}
      {claim.document_errors && claim.document_errors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="size-4" />
              Document Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {claim.document_errors.map((docErr, i) => {
                const friendlyMessage =
                  USER_FRIENDLY_ERROR_MESSAGES[docErr.error_type] ||
                  USER_FRIENDLY_ERROR_MESSAGES.DOCUMENT_ERROR;
                return (
                  <div
                    key={i}
                    className="rounded-md border border-destructive/20 bg-destructive/5 p-4 text-sm"
                  >
                    <div className="flex items-start gap-3">
                      <AlertCircle className="size-5 shrink-0 mt-0.5 text-destructive" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          {docErr.file_name && (
                            <span className="font-medium text-foreground">
                              {docErr.file_name}
                            </span>
                          )}
                          {docErr.error_type && (
                            <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">
                              {docErr.error_type}
                            </span>
                          )}
                        </div>
                        <p className="mt-1.5 text-foreground/90 leading-relaxed">
                          {friendlyMessage}
                        </p>
                        {docErr.message && (
                          <p className="mt-1 text-xs text-muted-foreground">
                            {docErr.message}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Retry Section — Document Re-upload */}
      {claim.status === 'DOCUMENT_ERROR' && !isRetrying && (
        <Card className="border-status-warning/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-status-warning">
              <RotateCcw className="size-4" />
              Re-upload Corrected Documents
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Please upload corrected versions of the documents listed above.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* File Upload */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Corrected Documents
              </label>
              <div className="flex flex-col gap-2">
                <input
                  type="file"
                  multiple
                  onChange={(e) => {
                    const files = Array.from(e.target.files || []);
                    setRetryFiles((prev) => [...prev, ...files]);
                  }}
                  className="block w-full text-sm text-muted-foreground
                    file:mr-3 file:py-2 file:px-4
                    file:rounded-lg file:border-0
                    file:text-sm file:font-medium
                    file:bg-primary file:text-primary-foreground
                    hover:file:bg-primary/90
                    file:cursor-pointer"
                  accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                />
                {retryFiles.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-1">
                    {retryFiles.map((f, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-1.5 rounded-md bg-muted px-2.5 py-1 text-xs text-muted-foreground"
                      >
                        <FileText className="size-3" />
                        <span className="truncate max-w-[150px]">{f.name}</span>
                        <button
                          type="button"
                          onClick={() =>
                            setRetryFiles((prev) => prev.filter((_, i) => i !== idx))
                          }
                          className="ml-1 text-destructive hover:text-destructive/80"
                        >
                          &times;
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Comment */}
            <div className="space-y-2">
              <label
                htmlFor="retry-comment"
                className="text-sm font-medium text-foreground"
              >
                Notes (optional)
              </label>
              <textarea
                id="retry-comment"
                rows={3}
                value={retryComment}
                onChange={(e) => setRetryComment(e.target.value)}
                placeholder="Add any notes about the corrected documents..."
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 pt-1">
              <Button
                variant="default"
                size="sm"
                onClick={handleRetry}
                disabled={isRetrying}
                className="gap-1.5"
              >
                <RotateCcw className="size-3.5" />
                Submit Corrected Documents
              </Button>
              {retryFiles.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRetryFiles([])}
                >
                  Clear Files
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Documents Section ─────────────────────────────── */}
      {documents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="size-4 text-muted-foreground" />
              Documents ({documents.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2">
              {documents.map((doc) => {
                const docBadge = getStatusBadgeConfig(doc.verification_status);
                const docTypeLabel = deriveDocumentTypeLabel(doc);
                const isPreviewing = previewDocId === doc.document_id;
                const viewUrl = getDocumentViewUrl(doc.document_id);

                return (
                  <div
                    key={doc.document_id}
                    className="flex flex-col rounded-lg border border-border"
                  >
                    {/* Document row */}
                    <div className="flex items-center gap-3 px-4 py-3">
                      <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted">
                        <FileText className="size-4 text-muted-foreground" />
                      </div>

                      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
                        <span className="truncate text-sm font-medium text-foreground">
                          {doc.file_name}
                        </span>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{docTypeLabel}</span>
                          {doc.quality_score != null && (
                            <>
                              <span>&middot;</span>
                              <span>Quality: {Math.round(doc.quality_score * 100)}%</span>
                            </>
                          )}
                        </div>
                      </div>

                      <Badge
                        variant={docBadge.variant}
                        className={cn('text-xs shrink-0', docBadge.className)}
                      >
                        {doc.verification_status}
                      </Badge>

                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => togglePreview(doc.document_id)}
                        title={isPreviewing ? 'Hide preview' : 'Preview document'}
                      >
                        {isPreviewing ? (
                          <EyeOff className="size-3.5" />
                        ) : (
                          <Eye className="size-3.5" />
                        )}
                      </Button>
                    </div>

                    {/* Document preview */}
                    {isPreviewing && (
                      <div className="border-t border-border p-4">
                        <div className="relative flex aspect-[3/4] max-h-[500px] w-full max-w-[400px] items-center justify-center overflow-hidden rounded-lg bg-muted">
                          {/* Use an img tag since getDocumentViewUrl returns a direct URL */}
                          {/* Note: Next.js Image requires configured domains for external URLs */}
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={viewUrl}
                            alt={`Document preview: ${docTypeLabel}`}
                            loading="lazy"
                            className="max-h-full max-w-full object-contain"
                            onError={(e) => {
                              const target = e.currentTarget;
                              target.style.display = 'none';
                              const fallback = target.parentElement?.querySelector(
                                '.fallback'
                              );
                              if (fallback) {
                                (fallback as HTMLElement).style.display = 'flex';
                              }
                            }}
                          />
                          <div className="fallback hidden absolute inset-0 flex-col items-center justify-center gap-2 text-muted-foreground">
                            <FileText className="size-10" />
                            <span className="text-sm">Preview not available</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Processing Trace Timeline ─────────────────────── */}
      {claim.processing_trace && claim.processing_trace.steps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="size-4 text-muted-foreground" />
              Processing Timeline
            </CardTitle>
            {claim.processing_trace.degraded && (
              <p className="mt-1 text-xs text-status-warning">
                Some components ran in degraded mode
              </p>
            )}
          </CardHeader>
          <CardContent>
            <div className="relative flex flex-col">
              {/* Vertical line */}
              <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" />

              {claim.processing_trace.steps.map((step, index) => {
                const StepIcon = getStepStatusIcon(step.status);
                const stepStatusColor = getStepStatusColor(step.status);
                const isExpanded = expandedStep === index;
                const checks = step.checks_performed as ProcessingCheck[] | undefined;

                return (
                  <motion.div
                    key={step.step_index ?? index}
                    className="relative flex gap-4 pb-6 last:pb-0"
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{
                      duration: 0.3,
                      delay: index * 0.08,
                      ease: 'easeOut',
                    }}
                  >
                    {/* Step icon */}
                    <div className="relative z-10 flex size-[30px] shrink-0 items-center justify-center rounded-full bg-card">
                      <StepIcon
                        className={cn('size-4', stepStatusColor)}
                      />
                    </div>

                    {/* Step content */}
                    <div className="flex min-w-0 flex-1 flex-col gap-0.5 pt-1">
                      {/* Clickable header row */}
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedStep(isExpanded ? null : index)
                        }
                        className="flex w-full items-center justify-between gap-2 text-left"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm font-medium text-foreground">
                            {step.step_name}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-[10px]',
                              step.status === 'completed' ||
                                step.status === 'success'
                                ? 'border-status-approved/20 text-status-approved'
                                : step.status === 'failed' ||
                                    step.status === 'error'
                                  ? 'border-destructive/20 text-destructive'
                                  : 'border-status-warning/20 text-status-warning'
                            )}
                          >
                            {step.status}
                          </Badge>
                        </div>
                        <ChevronDown
                          className={cn(
                            'size-4 shrink-0 text-muted-foreground transition-transform duration-200',
                            isExpanded && 'rotate-180'
                          )}
                        />
                      </button>

                      {/* Meta info row */}
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        {step.agent_name && (
                          <span>{step.agent_name}</span>
                        )}
                        {step.duration_ms != null && (
                          <>
                            <span>&middot;</span>
                            <span>{formatDuration(step.duration_ms)}</span>
                          </>
                        )}
                        {step.started_at && (
                          <>
                            <span>&middot;</span>
                            <span>{formatDateTime(step.started_at)}</span>
                          </>
                        )}
                      </div>

                      {step.error_message && (
                        <p className="mt-1 text-xs text-destructive">
                          {step.error_message}
                        </p>
                      )}

                      {step.confidence_score != null && (
                        <p className="mt-0.5 text-[11px] text-muted-foreground">
                          Confidence: {(step.confidence_score * 100).toFixed(0)}%
                        </p>
                      )}

                      {/* Expanded checks section */}
                      <div
                        className="grid transition-[grid-template-rows] duration-300 ease-in-out"
                        style={{
                          gridTemplateRows: isExpanded ? '1fr' : '0fr',
                        }}
                      >
                        <div className="overflow-hidden">
                          <div className="space-y-2 pt-3">
                            {checks && checks.length > 0 ? (
                              checks.map((check, ci) => {
                                const checkName =
                                  check.rule || check.check || 'Check';
                                return (
                                  <div
                                    key={ci}
                                    className={cn(
                                      'rounded-lg border p-3 text-sm',
                                      check.passed
                                        ? 'border-green-200 bg-green-50/30 dark:border-green-800 dark:bg-green-950/20'
                                        : 'border-red-200 bg-red-50/30 dark:border-red-800 dark:bg-red-950/20'
                                    )}
                                  >
                                    <div className="flex items-start gap-2.5">
                                      {check.passed ? (
                                        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-green-600 dark:text-green-400" />
                                      ) : (
                                        <XCircle className="mt-0.5 size-4 shrink-0 text-red-600 dark:text-red-400" />
                                      )}
                                      <div className="min-w-0 flex-1">
                                        <span className="font-medium text-foreground">
                                          {checkName}
                                        </span>
                                        {check.reason && (
                                          <p className="mt-1 whitespace-pre-wrap leading-relaxed text-muted-foreground">
                                            {check.reason}
                                          </p>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                );
                              })
                            ) : (
                              <p className="px-1 text-xs italic text-muted-foreground">
                                No detailed checks for this step.
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── Line Items ────────────────────────────────────── */}
      {claim.line_items && claim.line_items.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="size-4 text-muted-foreground" />
              Line Items ({claim.line_items.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Description</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Approved</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Reason</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {claim.line_items.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">
                      {item.description}
                    </TableCell>
                    <TableCell>{formatCurrency(item.amount)}</TableCell>
                    <TableCell>
                      {item.approved_amount != null
                        ? formatCurrency(item.approved_amount)
                        : '—'}
                    </TableCell>
                    <TableCell>
                      {item.is_covered != null ? (
                        <Badge
                          variant={item.is_covered ? 'default' : 'destructive'}
                          className={cn(
                            'text-xs',
                            item.is_covered &&
                              'bg-status-approved/10 text-status-approved border-status-approved/20'
                          )}
                        >
                          {item.is_covered ? 'Covered' : 'Not Covered'}
                        </Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          Pending
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate text-xs text-muted-foreground">
                      {item.rejection_reason || '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Manual review notice */}
      {claim.manual_review_recommended && (
        <Card className="border-status-warning/30 bg-status-warning/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-status-warning">
              <AlertCircle className="size-4" />
              Manual Review Recommended
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              This claim has been flagged for manual review by a claims
              adjuster. Check back for updates after review.
            </p>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}
