'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Eye,
  FileText,
  ImageIcon,
  FileIcon,
  MessageSquare,
  Send,
  RotateCcw,
  Clock,
  Loader2,
  RefreshCw,
  DollarSign,
  Building,
  CalendarDays,
  User,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { getAdminClaim, adminOverride, adminComment, getDocumentViewUrl, retryClaim } from '@/lib/api';
import type { ClaimResponse, DocumentResponse, ProcessingStepResponse, LineItemResponse } from '@/types';
import { CLAIM_CATEGORIES } from '@/types';

// ── Helpers ─────────────────────────────────────────────────

function statusBadgeClass(status: string): string {
  switch (status) {
    case 'SUBMITTED':
      return 'bg-[#0D6B6E]/10 text-[#0D6B6E] border-[#0D6B6E]/20';
    case 'VALIDATING':
    case 'PROCESSING':
      return 'bg-[#0D6B6E]/10 text-[#0D6B6E] border-[#0D6B6E]/20';
    case 'DECIDED':
      return 'bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20';
    case 'DOCUMENT_ERROR':
      return 'bg-[#E8A838]/10 text-[#E8A838] border-[#E8A838]/20';
    case 'ERROR':
      return 'bg-destructive/10 text-destructive border-destructive/20';
    case 'CLOSED':
      return 'bg-muted text-muted-foreground border-border';
    default:
      return 'bg-muted text-muted-foreground border-border';
  }
}

function decisionBadgeClass(decision: string | null): string {
  switch (decision) {
    case 'APPROVED':
      return 'bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20';
    case 'PARTIAL':
      return 'bg-[#E8A838]/10 text-[#E8A838] border-[#E8A838]/20';
    case 'REJECTED':
      return 'bg-destructive/10 text-destructive border-destructive/20';
    case 'MANUAL_REVIEW':
      return 'bg-[#0D6B6E]/10 text-[#0D6B6E] border-[#0D6B6E]/20';
    default:
      return 'bg-muted text-muted-foreground border-border';
  }
}

const decisionLabel: Record<string, string> = {
  APPROVED: 'Approved',
  PARTIAL: 'Partially Approved',
  REJECTED: 'Rejected',
  MANUAL_REVIEW: 'Manual Review',
};

const decisionColors: Record<string, string> = {
  APPROVED: 'bg-[#2D8B6E]',
  PARTIAL: 'bg-[#E8A838]',
  REJECTED: 'bg-[#D45161]',
  MANUAL_REVIEW: 'bg-[#0D6B6E]',
};

function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount);
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function formatDateShort(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

function getCategoryLabel(category: string): string {
  const found = CLAIM_CATEGORIES.find((c) => c.value === category);
  return found?.label || category;
}

function getDocumentTypeLabel(doc: DocumentResponse): string {
  if (doc.document_type && doc.document_type !== 'UNKNOWN') {
    return doc.document_type.replace(/_/g, ' ');
  }
  // Derive from file extension
  const ext = doc.file_name.split('.').pop()?.toUpperCase() || '';
  return `${ext} Document`;
}

function getDocumentIcon(doc: DocumentResponse): React.ElementType {
  const ext = doc.file_name.split('.').pop()?.toLowerCase() || '';
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
    return ImageIcon;
  }
  if (['pdf'].includes(ext)) {
    return FileText;
  }
  return FileIcon;
}

function isImageFile(fileName: string): boolean {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext);
}

function isPdfFile(fileName: string): boolean {
  return fileName.split('.').pop()?.toLowerCase() === 'pdf';
}

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return '';
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

// ── Animation Variants ──────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] as const } },
};

// ── Loading Skeleton ─────────────────────────────────────────

function ClaimDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="h-8 w-8 bg-muted rounded-lg" />
        <div className="h-6 w-48 bg-muted rounded-lg" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
            <div className="h-5 w-32 bg-muted rounded mb-4" />
            <div className="space-y-3">
              <div className="h-4 w-full bg-muted rounded" />
              <div className="h-4 w-3/4 bg-muted rounded" />
              <div className="h-4 w-1/2 bg-muted rounded" />
            </div>
          </div>
          <div className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
            <div className="h-5 w-40 bg-muted rounded mb-4" />
            <div className="grid grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i}>
                  <div className="h-3 w-16 bg-muted rounded mb-1" />
                  <div className="h-5 w-28 bg-muted rounded" />
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="space-y-6">
          <div className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
            <div className="h-5 w-28 bg-muted rounded mb-4" />
            <div className="space-y-3">
              <div className="h-10 w-full bg-muted rounded-lg" />
              <div className="h-10 w-full bg-muted rounded-lg" />
              <div className="h-10 w-full bg-muted rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Processing Step ──────────────────────────────────────────

function ProcessingStepItem({ step }: { step: ProcessingStepResponse }) {
  const isCompleted = step.status === 'completed';
  const isRunning = step.status === 'running' || step.status === 'processing';
  const isFailed = step.status === 'failed' || step.status === 'error';

  return (
    <div className="flex gap-3">
      {/* Timeline dot */}
      <div className="flex flex-col items-center">
        <div
          className={`size-3 rounded-full ring-2 ring-background shrink-0 ${
            isCompleted
              ? 'bg-[#2D8B6E]'
              : isFailed
              ? 'bg-destructive'
              : isRunning
              ? 'bg-[#E8A838] animate-pulse'
              : 'bg-muted-foreground'
          }`}
        />
        <div className="w-px flex-1 bg-border mt-1" />
      </div>

      {/* Content */}
      <div className="flex-1 pb-5">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{step.step_name || step.agent_name || `Step ${step.step_index}`}</span>
          <Badge
            variant="outline"
            className={`text-[10px] px-1.5 py-0 h-4 ${
              isCompleted
                ? 'bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20'
                : isFailed
                ? 'bg-destructive/10 text-destructive border-destructive/20'
                : isRunning
                ? 'bg-[#E8A838]/10 text-[#E8A838] border-[#E8A838]/20'
                : ''
            }`}
          >
            {step.status}
          </Badge>
        </div>
        {step.agent_name && step.step_name !== step.agent_name && (
          <p className="text-xs text-muted-foreground mt-0.5">Agent: {step.agent_name}</p>
        )}
        {step.error_message && (
          <p className="text-xs text-destructive mt-1">{step.error_message}</p>
        )}
        {step.confidence_score != null && (
          <div className="mt-1.5">
            <div
              className={`h-1 rounded-full max-w-48 ${
                step.confidence_score >= 0.8
                  ? 'bg-[#2D8B6E]/20'
                  : step.confidence_score >= 0.5
                  ? 'bg-[#E8A838]/20'
                  : 'bg-destructive/20'
              }`}
            >
              <div
                className={`h-full rounded-full transition-all ${
                  step.confidence_score >= 0.8
                    ? 'bg-[#2D8B6E]'
                    : step.confidence_score >= 0.5
                    ? 'bg-[#E8A838]'
                    : 'bg-destructive'
                }`}
                style={{ width: `${step.confidence_score * 100}%` }}
              />
            </div>
            <span className="text-[10px] text-muted-foreground mt-0.5 block">
              Confidence: {(step.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
        <div className="flex items-center gap-3 mt-1.5 text-[10px] text-muted-foreground">
          {step.started_at && <span>Started: {formatDate(step.started_at)}</span>}
          {step.duration_ms != null && (
            <span className="tabular-nums">Duration: {formatDuration(step.duration_ms)}</span>
          )}
        </div>
        {step.checks_performed && step.checks_performed.length > 0 && (
          <details className="mt-1.5">
            <summary className="text-[11px] text-muted-foreground cursor-pointer hover:text-foreground">
              Checks performed ({step.checks_performed.length})
            </summary>
            <ul className="mt-1 space-y-0.5">
              {step.checks_performed.map((check, i) => (
                <li key={i} className="text-[11px] text-muted-foreground">
                  {Object.entries(check).map(([k, v]) => `${k}: ${String(v)}`).join(', ')}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}

// ── Override Dialog Content ─────────────────────────────────

function OverrideDialogContent({
  decision,
  onConfirm,
  onCancel,
  loading,
}: {
  decision: 'APPROVED' | 'PARTIAL' | 'REJECTED' | 'MANUAL_REVIEW';
  onConfirm: (comment: string, amount?: number) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [comment, setComment] = useState('');
  const [amount, setAmount] = useState('');

  const handleConfirm = () => {
    const parsedAmount = amount ? parseFloat(amount) : undefined;
    onConfirm(comment, parsedAmount);
  };

  const labels: Record<string, { title: string; desc: string; showAmount: boolean }> = {
    APPROVED: {
      title: 'Approve Claim',
      desc: 'Are you sure you want to approve this claim? This will mark it as fully approved.',
      showAmount: false,
    },
    PARTIAL: {
      title: 'Partially Approve Claim',
      desc: 'Set the approved amount for this claim. The claim will be partially approved.',
      showAmount: true,
    },
    REJECTED: {
      title: 'Reject Claim',
      desc: 'Are you sure you want to reject this claim? This will mark it as denied.',
      showAmount: false,
    },
    MANUAL_REVIEW: {
      title: 'Send to Manual Review',
      desc: 'Send this claim for manual review. A human reviewer will evaluate the claim.',
      showAmount: false,
    },
  };

  const showAmount = labels[decision]?.showAmount ?? false;

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{labels[decision]?.title || 'Override Decision'}</DialogTitle>
        <DialogDescription>
          {labels[decision]?.desc || 'Are you sure you want to override the current decision?'}
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4 py-2">
        {showAmount && (
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Approved Amount (required for partial approval)
            </label>
            <div className="relative">
              <DollarSign className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-muted-foreground">
            Comment (optional)
          </label>
          <Textarea
            placeholder="Add a note about this decision..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={3}
          />
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          disabled={loading}
          className={
            decision === 'APPROVED'
              ? 'bg-[#2D8B6E] hover:bg-[#2D8B6E]/80'
              : decision === 'REJECTED'
              ? 'bg-destructive hover:bg-destructive/80'
              : ''
          }
        >
          {loading ? <Loader2 className="size-4 animate-spin mr-1.5" /> : null}
          Confirm {labels[decision]?.title || 'Override'}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}

// ── Document Preview ─────────────────────────────────────────

function DocumentPreview({ doc }: { doc: DocumentResponse }) {
  const [open, setOpen] = useState(false);

  const url = getDocumentViewUrl(doc.document_id);
  const Icon = getDocumentIcon(doc);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <div className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors cursor-pointer">
          <div className="size-8 rounded-md bg-[#0D6B6E]/10 flex items-center justify-center shrink-0">
            <Icon className="size-4 text-[#0D6B6E]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{doc.file_name}</p>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                {getDocumentTypeLabel(doc)}
              </Badge>
              {doc.quality_score != null && (
                <span
                  className={`text-[10px] tabular-nums ${
                    doc.quality_score >= 0.8
                      ? 'text-[#2D8B6E]'
                      : doc.quality_score >= 0.5
                      ? 'text-[#E8A838]'
                      : 'text-destructive'
                  }`}
                >
                  {Math.round(doc.quality_score * 100)}% quality
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`text-[10px] ${
                  doc.verification_status === 'VERIFIED'
                    ? 'text-[#2D8B6E]'
                    : doc.verification_status === 'FAILED'
                    ? 'text-destructive'
                    : 'text-muted-foreground'
                }`}
              >
                {doc.verification_status}
              </span>
            </div>
          </div>
        </div>
      </DialogTrigger>

      <DialogContent className="max-w-3xl w-[calc(100%-2rem)] sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{doc.file_name}</DialogTitle>
          <DialogDescription>
            {getDocumentTypeLabel(doc)}
            {doc.quality_score != null && ` — ${Math.round(doc.quality_score * 100)}% quality`}
          </DialogDescription>
        </DialogHeader>

        <div className="min-h-[300px] max-h-[70vh] rounded-lg overflow-hidden bg-muted flex items-center justify-center">
          {isImageFile(doc.file_name) ? (
            <img
              src={url}
              alt={doc.file_name}
              className="max-w-full max-h-[70vh] object-contain"
            />
          ) : isPdfFile(doc.file_name) ? (
            <iframe
              src={url}
              className="w-full h-[70vh]"
              title={doc.file_name}
            />
          ) : (
            <div className="flex flex-col items-center gap-3 py-12">
              <FileIcon className="size-12 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Preview not available</p>
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary underline"
              >
                Download file
              </a>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Main Claim Detail Page ───────────────────────────────────

export default function AdminClaimDetailPage() {
  const params = useParams();
  const router = useRouter();
  const claimId = Number(params.id);

  const [claim, setClaim] = useState<ClaimResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  // Override dialog state
  const [overrideTarget, setOverrideTarget] = useState<'APPROVED' | 'PARTIAL' | 'REJECTED' | 'MANUAL_REVIEW' | null>(null);
  const [overriding, setOverriding] = useState(false);

  // Comment state
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  // Retry state
  const [retrying, setRetrying] = useState(false);

  const fetchClaim = useCallback(async () => {
    if (!claimId || isNaN(claimId)) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    setNotFound(false);
    try {
      const result = await getAdminClaim(claimId);
      setClaim(result);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load claim';
      if (msg.includes('404') || msg.includes('not found')) {
        setNotFound(true);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, [claimId]);

  useEffect(() => {
    fetchClaim();
  }, [fetchClaim]);

  // ── Override Handler ───────────────────────────────────────
  const handleOverride = useCallback(
    async (comment: string, approvedAmount?: number) => {
      if (!claim || !overrideTarget) return;
      setOverriding(true);
      try {
        const updated = await adminOverride(claim.claim_id, {
          decision: overrideTarget,
          comment: comment || undefined,
          approved_amount: overrideTarget === 'PARTIAL' ? approvedAmount : undefined,
        });
        setClaim(updated);
        setOverrideTarget(null);
        toast.success(
          `Claim #${claim.claim_id} ${overrideTarget === 'APPROVED' ? 'approved' : overrideTarget === 'PARTIAL' ? 'partially approved' : overrideTarget === 'REJECTED' ? 'rejected' : 'sent to manual review'}`
        );
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Failed to override decision');
      } finally {
        setOverriding(false);
      }
    },
    [claim, overrideTarget]
  );

  // ── Comment Handler ────────────────────────────────────────
  const handleSubmitComment = useCallback(async () => {
    if (!claim || !commentText.trim()) return;
    setSubmittingComment(true);
    try {
      const updated = await adminComment(claim.claim_id, commentText.trim());
      setClaim(updated);
      setCommentText('');
      toast.success('Comment added');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add comment');
    } finally {
      setSubmittingComment(false);
    }
  }, [claim, commentText]);

  // ── Retry Handler ──────────────────────────────────────────
  const handleRetry = useCallback(async () => {
    if (!claim) return;
    setRetrying(true);
    try {
      const updated = await retryClaim(claim.claim_id, {});
      setClaim(updated);
      toast.success('Claim retry initiated');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to retry claim');
    } finally {
      setRetrying(false);
    }
  }, [claim]);

  // ── Loading State ──────────────────────────────────────────
  if (loading) {
    return <ClaimDetailSkeleton />;
  }

  // ── Not Found State ────────────────────────────────────────
  if (notFound) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-24 gap-4"
      >
        <div className="size-12 rounded-full bg-muted flex items-center justify-center">
          <AlertCircle className="size-6 text-muted-foreground" />
        </div>
        <h2 className="text-lg font-medium">Claim not found</h2>
        <p className="text-sm text-muted-foreground">
          Claim #{claimId} does not exist or has been removed.
        </p>
        <Button variant="outline" onClick={() => router.push('/admin/claims')}>
          <ArrowLeft className="size-4 mr-1.5" />
          Back to Claims
        </Button>
      </motion.div>
    );
  }

  // ── Error State ────────────────────────────────────────────
  if (error && !claim) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-24 gap-4"
      >
        <div className="size-12 rounded-full bg-destructive/10 flex items-center justify-center">
          <AlertCircle className="size-6 text-destructive" />
        </div>
        <p className="text-muted-foreground text-sm max-w-md text-center">{error}</p>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => router.push('/admin/claims')}>
            <ArrowLeft className="size-4 mr-1.5" />
            Back to Claims
          </Button>
          <Button variant="default" onClick={fetchClaim}>
            <RefreshCw className="size-4 mr-1.5" />
            Retry
          </Button>
        </div>
      </motion.div>
    );
  }

  if (!claim) return null;

  const hasErrors =
    claim.status === 'ERROR' ||
    claim.status === 'DOCUMENT_ERROR' ||
    (claim.error_messages && claim.error_messages.length > 0) ||
    (claim.document_errors && claim.document_errors.length > 0);

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Back Button */}
      <motion.div variants={itemVariants}>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/admin/claims')}
          className="text-muted-foreground"
        >
          <ArrowLeft className="size-4 mr-1.5" />
          Back to Claims
        </Button>
      </motion.div>

      {/* Header Section */}
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1
            className="text-2xl sm:text-3xl font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            Claim #{claim.claim_id}
          </h1>
          <Badge variant="outline" className={`font-medium ${statusBadgeClass(claim.status)}`}>
            {claim.status}
          </Badge>
          {claim.decision && (
            <Badge variant="outline" className={`font-medium ${decisionBadgeClass(claim.decision)}`}>
              {decisionLabel[claim.decision] || claim.decision}
            </Badge>
          )}
        </div>

        {hasErrors && (
          <div className="flex items-center gap-2">
            <Button
              variant="destructive"
              size="sm"
              onClick={handleRetry}
              disabled={retrying}
            >
              {retrying ? (
                <Loader2 className="size-4 animate-spin mr-1.5" />
              ) : (
                <RotateCcw className="size-4 mr-1.5" />
              )}
              Retry Processing
            </Button>
          </div>
        )}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Claim Details */}
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm font-medium">
                  <FileText className="size-4 text-primary" />
                  Claim Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Member ID</p>
                    <p className="text-sm font-medium">{claim.member_id}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Policy ID</p>
                    <p className="text-sm font-medium">{claim.policy_id}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Category</p>
                    <p className="text-sm font-medium">{getCategoryLabel(claim.claim_category)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Hospital</p>
                    <p className="text-sm font-medium">{claim.hospital_name || '—'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Treatment Date</p>
                    <p className="text-sm font-medium">{formatDateShort(claim.treatment_date)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Submitted</p>
                    <p className="text-sm font-medium">{formatDate(claim.submitted_at)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Claimed Amount</p>
                    <p className="text-sm font-mono font-medium">{formatCurrency(claim.claimed_amount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Approved Amount</p>
                    <p className="text-sm font-mono font-medium">{formatCurrency(claim.approved_amount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Confidence</p>
                    <p className="text-sm font-medium tabular-nums">
                      {claim.confidence_score != null
                        ? `${(claim.confidence_score * 100).toFixed(1)}%`
                        : '—'}
                    </p>
                  </div>
                </div>

                {claim.decision_reason && (
                  <div className="mt-4 pt-4 border-t border-border">
                    <p className="text-xs text-muted-foreground mb-1">Decision Reason</p>
                    <p className="text-sm">{claim.decision_reason}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Line Items */}
          {claim.line_items && claim.line_items.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-medium">
                    <DollarSign className="size-4 text-primary" />
                    Line Items
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Description</TableHead>
                          <TableHead>Amount</TableHead>
                          <TableHead>Approved</TableHead>
                          <TableHead>Covered</TableHead>
                          <TableHead>Reason</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {claim.line_items.map((item, i) => (
                          <TableRow key={i}>
                            <TableCell className="text-sm">{item.description}</TableCell>
                            <TableCell className="font-mono text-sm tabular-nums">
                              {formatCurrency(item.amount)}
                            </TableCell>
                            <TableCell className="font-mono text-sm tabular-nums">
                              {formatCurrency(item.approved_amount)}
                            </TableCell>
                            <TableCell>
                              {item.is_covered == null ? (
                                '—'
                              ) : item.is_covered ? (
                                <Badge
                                  variant="outline"
                                  className="bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20"
                                >
                                  Yes
                                </Badge>
                              ) : (
                                <Badge
                                  variant="outline"
                                  className="bg-destructive/10 text-destructive border-destructive/20"
                                >
                                  No
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {item.rejection_reason || '—'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Documents */}
          {claim.documents && claim.documents.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-medium">
                    <FileText className="size-4 text-primary" />
                    Documents ({claim.documents.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {claim.documents.map((doc) => (
                      <DocumentPreview key={doc.document_id} doc={doc} />
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Document Errors */}
          {claim.document_errors && claim.document_errors.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-medium text-destructive">
                    <AlertCircle className="size-4" />
                    Document Errors
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {claim.document_errors.map((err, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-destructive/5 border border-destructive/20"
                    >
                      <p className="text-sm font-medium">{err.error_type}</p>
                      {err.file_name && (
                        <p className="text-xs text-muted-foreground mt-0.5">{err.file_name}</p>
                      )}
                      <p className="text-sm mt-1">{err.message}</p>
                      {err.details && Object.keys(err.details).length > 0 && (
                        <pre className="mt-1 text-[10px] text-muted-foreground overflow-x-auto">
                          {JSON.stringify(err.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Processing Trace */}
          {claim.processing_trace && claim.processing_trace.steps && claim.processing_trace.steps.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-medium">
                    <Clock className="size-4 text-primary" />
                    Processing Trace
                  </CardTitle>
                  {claim.processing_trace.degraded && (
                    <CardDescription className="text-[#E8A838]">
                      Some components ran in degraded mode
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="space-y-0">
                    {claim.processing_trace.steps.map((step) => (
                      <ProcessingStepItem key={step.step_index} step={step} />
                    ))}
                  </div>

                  {claim.processing_trace.failed_components &&
                    claim.processing_trace.failed_components.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-border">
                        <p className="text-xs font-medium text-destructive mb-2">Failed Components</p>
                        <div className="flex flex-wrap gap-2">
                          {claim.processing_trace.failed_components.map((comp, i) => (
                            <Badge key={i} variant="outline" className="bg-destructive/10 text-destructive border-destructive/20">
                              {comp}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Error Messages */}
          {claim.error_messages && claim.error_messages.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm font-medium text-destructive">
                    <AlertCircle className="size-4" />
                    Errors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {claim.error_messages.map((msg, i) => (
                      <li key={i} className="text-sm text-destructive flex items-start gap-2">
                        <span className="size-1.5 rounded-full bg-destructive mt-1.5 shrink-0" />
                        {msg}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Admin Comments */}
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm font-medium">
                  <MessageSquare className="size-4 text-primary" />
                  Admin Comments
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Comments list — using a fallback since the type doesn't include a comments field */}
                <p className="text-xs text-muted-foreground">
                  Add an internal note about this claim.
                </p>

                {/* Add comment form */}
                <div className="flex gap-2">
                  <Textarea
                    placeholder="Type your comment..."
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    rows={2}
                    className="flex-1 min-h-0"
                  />
                  <Button
                    size="sm"
                    className="self-end"
                    disabled={!commentText.trim() || submittingComment}
                    onClick={handleSubmitComment}
                  >
                    {submittingComment ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Send className="size-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column: Decision Panel */}
        <div className="space-y-6">
          <motion.div variants={itemVariants}>
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm font-medium">
                  <Eye className="size-4 text-primary" />
                  Decision
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Current Decision */}
                <div>
                  <p className="text-xs text-muted-foreground mb-1.5">Current Decision</p>
                  {claim.decision ? (
                    <div className="flex items-center gap-2">
                      <div
                        className={`size-2 rounded-full ${
                          decisionColors[claim.decision] || 'bg-muted-foreground'
                        }`}
                      />
                      <span
                        className={`text-sm font-medium ${
                          claim.decision === 'APPROVED'
                            ? 'text-[#2D8B6E]'
                            : claim.decision === 'REJECTED'
                            ? 'text-destructive'
                            : claim.decision === 'PARTIAL'
                            ? 'text-[#E8A838]'
                            : ''
                        }`}
                      >
                        {decisionLabel[claim.decision] || claim.decision}
                      </span>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No decision made yet</p>
                  )}
                </div>

                <Separator />

                {/* Override Buttons */}
                <div className="space-y-2">
                  <p className="text-xs font-medium text-muted-foreground">Override Decision</p>

                  <Dialog
                    open={overrideTarget === 'APPROVED'}
                    onOpenChange={(open) => setOverrideTarget(open ? 'APPROVED' : null)}
                  >
                    <DialogTrigger>
                      <Button
                        className="w-full justify-start bg-[#2D8B6E] hover:bg-[#2D8B6E]/80 text-white"
                        size="sm"
                        onClick={() => setOverrideTarget('APPROVED')}
                      >
                        <CheckCircle2 className="size-4 mr-1.5" />
                        Approve
                      </Button>
                    </DialogTrigger>
                    <OverrideDialogContent
                      decision="APPROVED"
                      onConfirm={(comment) => handleOverride(comment)}
                      onCancel={() => setOverrideTarget(null)}
                      loading={overriding}
                    />
                  </Dialog>

                  <Dialog
                    open={overrideTarget === 'PARTIAL'}
                    onOpenChange={(open) => setOverrideTarget(open ? 'PARTIAL' : null)}
                  >
                    <DialogTrigger>
                      <Button
                        className="w-full justify-start bg-[#E8A838] hover:bg-[#E8A838]/80 text-white"
                        size="sm"
                        onClick={() => setOverrideTarget('PARTIAL')}
                      >
                        <DollarSign className="size-4 mr-1.5" />
                        Partial
                      </Button>
                    </DialogTrigger>
                    <OverrideDialogContent
                      decision="PARTIAL"
                      onConfirm={(comment, amount) => handleOverride(comment, amount)}
                      onCancel={() => setOverrideTarget(null)}
                      loading={overriding}
                    />
                  </Dialog>

                  <Dialog
                    open={overrideTarget === 'REJECTED'}
                    onOpenChange={(open) => setOverrideTarget(open ? 'REJECTED' : null)}
                  >
                    <DialogTrigger>
                      <Button
                        className="w-full justify-start bg-destructive hover:bg-destructive/80 text-white"
                        size="sm"
                        onClick={() => setOverrideTarget('REJECTED')}
                      >
                        <XCircle className="size-4 mr-1.5" />
                        Reject
                      </Button>
                    </DialogTrigger>
                    <OverrideDialogContent
                      decision="REJECTED"
                      onConfirm={(comment) => handleOverride(comment)}
                      onCancel={() => setOverrideTarget(null)}
                      loading={overriding}
                    />
                  </Dialog>

                  <Dialog
                    open={overrideTarget === 'MANUAL_REVIEW'}
                    onOpenChange={(open) => setOverrideTarget(open ? 'MANUAL_REVIEW' : null)}
                  >
                    <DialogTrigger>
                      <Button
                        className="w-full justify-start bg-[#E8A838] hover:bg-[#E8A838]/80 text-white"
                        size="sm"
                        onClick={() => setOverrideTarget('MANUAL_REVIEW')}
                      >
                        <Eye className="size-4 mr-1.5" />
                        Manual Review
                      </Button>
                    </DialogTrigger>
                    <OverrideDialogContent
                      decision="MANUAL_REVIEW"
                      onConfirm={(comment) => handleOverride(comment)}
                      onCancel={() => setOverrideTarget(null)}
                      loading={overriding}
                    />
                  </Dialog>
                </div>

                {/* Claim Info Summary */}
                <Separator />
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Claimed</span>
                    <span className="font-mono font-medium">{formatCurrency(claim.claimed_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Approved</span>
                    <span className="font-mono font-medium">{formatCurrency(claim.approved_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Confidence</span>
                    <span className="font-mono font-medium tabular-nums">
                      {claim.confidence_score != null
                        ? `${(claim.confidence_score * 100).toFixed(1)}%`
                        : '—'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
