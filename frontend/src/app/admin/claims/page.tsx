'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  Search,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  FileText,
  AlertCircle,
  FilterX,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { listAdminClaims } from '@/lib/api';
import type { ClaimResponse, ClaimStatus, Decision } from '@/types';
import { CLAIM_CATEGORIES } from '@/types';

// ── Helpers ─────────────────────────────────────────────────

const PAGE_SIZE = 20;

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'SUBMITTED', label: 'Submitted' },
  { value: 'VALIDATING', label: 'Validating' },
  { value: 'PROCESSING', label: 'Processing' },
  { value: 'DECIDED', label: 'Decided' },
  { value: 'DOCUMENT_ERROR', label: 'Document Error' },
  { value: 'ERROR', label: 'Error' },
  { value: 'CLOSED', label: 'Closed' },
];

const DECISION_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All Decisions' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'PARTIAL', label: 'Partially Approved' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'MANUAL_REVIEW', label: 'Manual Review' },
];

function statusBadgeVariant(status: ClaimStatus): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'DECIDED':
      return 'default';
    case 'ERROR':
    case 'DOCUMENT_ERROR':
      return 'destructive';
    default:
      return 'outline';
  }
}

function decisionBadgeVariant(decision: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (decision) {
    case 'APPROVED':
      return 'default';
    case 'PARTIAL':
      return 'secondary';
    case 'REJECTED':
      return 'destructive';
    case 'MANUAL_REVIEW':
      return 'outline';
    default:
      return 'outline';
  }
}

function statusBadgeClass(status: ClaimStatus): string {
  switch (status) {
    case 'SUBMITTED':
      return 'bg-status-info/10 text-status-info border-status-info/20';
    case 'VALIDATING':
    case 'PROCESSING':
      return 'bg-status-info/10 text-status-info border-status-info/20';
    case 'DECIDED':
      return 'bg-status-approved/10 text-status-approved border-status-approved/20';
    case 'DOCUMENT_ERROR':
      return 'bg-status-warning/10 text-status-warning border-status-warning/20';
    case 'ERROR':
      return 'bg-destructive/10 text-destructive border-destructive/20';
    case 'CLOSED':
      return 'bg-muted text-muted-foreground border-border';
    default:
      return '';
  }
}

function decisionBadgeClass(decision: Decision | null): string {
  switch (decision) {
    case 'APPROVED':
      return 'bg-status-approved/10 text-status-approved border-status-approved/20';
    case 'PARTIAL':
      return 'bg-status-warning/10 text-status-warning border-status-warning/20';
    case 'REJECTED':
      return 'bg-destructive/10 text-destructive border-destructive/20';
    case 'MANUAL_REVIEW':
      return 'bg-status-info/10 text-status-info border-status-info/20';
    default:
      return 'bg-muted text-muted-foreground border-border';
  }
}

function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
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
    });
  } catch {
    return iso;
  }
}

function getCategoryLabel(category: string): string {
  const found = CLAIM_CATEGORIES.find((c) => c.value === category);
  return found?.label || category;
}

function formatDateParam(date: Date | undefined): string {
  if (!date) return '';
  return date.toISOString().split('T')[0];
}

// ── Loading Skeleton ─────────────────────────────────────────

function ClaimsTableSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 w-48 bg-muted rounded-lg" />
      <div className="rounded-xl bg-card ring-1 ring-foreground/10 overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="h-4 w-40 bg-muted rounded" />
        </div>
        <div className="divide-y divide-border">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-4">
              <div className="h-4 w-16 bg-muted rounded" />
              <div className="h-4 w-20 bg-muted rounded" />
              <div className="h-4 w-24 bg-muted rounded" />
              <div className="h-4 w-16 bg-muted rounded" />
              <div className="h-5 w-20 bg-muted rounded-full" />
              <div className="h-5 w-20 bg-muted rounded-full" />
              <div className="h-4 w-24 bg-muted rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main Claims Page ─────────────────────────────────────────

function AdminClaimsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Filter state from URL params
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [decision, setDecision] = useState(searchParams.get('decision') || '');
  const [memberId, setMemberId] = useState(searchParams.get('member_id') || '');
  const [category, setCategory] = useState(searchParams.get('claim_category') || '');
  const [dateFrom, setDateFrom] = useState<Date | undefined>(undefined);
  const [dateTo, setDateTo] = useState<Date | undefined>(undefined);

  // Pagination
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchClaims = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number | undefined> = {
        limit: PAGE_SIZE,
        offset,
      };
      if (status) params.status = status;
      if (decision) params.decision = decision;
      if (memberId) params.member_id = memberId;
      if (category) params.claim_category = category;
      if (dateFrom) params.date_from = formatDateParam(dateFrom);
      if (dateTo) params.date_to = formatDateParam(dateTo);

      const result = await listAdminClaims(params);
      setClaims(result.claims);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  }, [status, decision, memberId, category, dateFrom, dateTo, offset]);

  useEffect(() => {
    fetchClaims();
  }, [fetchClaims]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [status, decision, memberId, category, dateFrom, dateTo]);

  const clearFilters = useCallback(() => {
    setStatus('');
    setDecision('');
    setMemberId('');
    setCategory('');
    setDateFrom(undefined);
    setDateTo(undefined);
  }, []);

  const hasFilters = status || decision || memberId || category || dateFrom || dateTo;

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  // ── Error State ────────────────────────────────────────────
  if (error && claims.length === 0) {
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
        <Button variant="outline" onClick={fetchClaims}>
          <RotateCcw className="size-4 mr-1.5" />
          Retry
        </Button>
      </motion.div>
    );
  }

  // ── Container Animation ────────────────────────────────────
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      {/* Page Header */}
      <motion.div variants={item}>
        <h1
          className="text-2xl sm:text-3xl font-bold tracking-tight"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Claims Management
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review, filter, and manage all submitted claims
        </p>
      </motion.div>

      {/* Filter Bar */}
      <motion.div variants={item}>
        <Card>
          <CardContent className="pt-4">
            <div className="flex flex-wrap items-end gap-3">
              {/* Status Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Status</label>
                <Select value={status} onValueChange={(v) => setStatus(v ?? '')}>
                  <SelectTrigger className="w-36">
                    <SelectValue placeholder="All Statuses" />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Decision Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Decision</label>
                <Select value={decision} onValueChange={(v) => setDecision(v ?? '')}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All Decisions" />
                  </SelectTrigger>
                  <SelectContent>
                    {DECISION_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Member ID Search */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Member ID</label>
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                  <Input
                    placeholder="Search member..."
                    value={memberId}
                    onChange={(e) => setMemberId(e.target.value)}
                    className="w-40 pl-8"
                  />
                </div>
              </div>

              {/* Category Filter */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">Category</label>
                <Select value={category} onValueChange={(v) => setCategory(v ?? '')}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Categories</SelectItem>
                    {CLAIM_CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Date From */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">From</label>
                <Popover>
                  <PopoverTrigger
                    render={
                      <Button variant="outline" className="w-32 justify-start text-sm font-normal" />
                    }
                  >
                    {dateFrom ? formatDate(dateFrom.toISOString()) : 'From date'}
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={dateFrom}
                      onSelect={setDateFrom}
                    />
                  </PopoverContent>
                </Popover>
              </div>

              {/* Date To */}
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-muted-foreground">To</label>
                <Popover>
                  <PopoverTrigger
                    render={
                      <Button variant="outline" className="w-32 justify-start text-sm font-normal" />
                    }
                  >
                    {dateTo ? formatDate(dateTo.toISOString()) : 'To date'}
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={dateTo}
                      onSelect={setDateTo}
                    />
                  </PopoverContent>
                </Popover>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pb-0.5">
                {hasFilters && (
                  <Button variant="ghost" size="sm" onClick={clearFilters}>
                    <FilterX className="size-4 mr-1" />
                    Clear
                  </Button>
                )}
                <Button variant="default" size="sm" onClick={fetchClaims}>
                  <Search className="size-4 mr-1" />
                  Apply
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Summary Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {loading ? (
            'Loading...'
          ) : (
            <>
              Showing{' '}
              <span className="font-medium text-foreground">
                {claims.length > 0 ? offset + 1 : 0}
              </span>
              {' '}to{' '}
              <span className="font-medium text-foreground">
                {Math.min(offset + claims.length, total)}
              </span>
              {' '}of{' '}
              <span className="font-medium text-foreground">{total.toLocaleString()}</span>
              {' '}claims
            </>
          )}
        </p>
      </motion.div>

      {/* Claims Table */}
      <motion.div variants={item}>
        <Card>
          <CardContent className="p-0">
            {loading ? (
              <div className="animate-pulse divide-y divide-border">
                <div className="flex items-center gap-4 p-4 border-b border-border bg-muted/30">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="h-4 bg-muted rounded flex-1" />
                  ))}
                </div>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 p-4">
                    {Array.from({ length: 8 }).map((_, j) => (
                      <div key={j} className="h-4 bg-muted rounded flex-1" />
                    ))}
                  </div>
                ))}
              </div>
            ) : claims.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <div className="size-12 rounded-full bg-muted flex items-center justify-center">
                  <FileText className="size-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground font-medium">No claims found</p>
                <p className="text-xs text-muted-foreground">
                  {hasFilters ? 'Try adjusting your filters' : 'No claims have been submitted yet'}
                </p>
                {hasFilters && (
                  <Button variant="outline" size="sm" onClick={clearFilters}>
                    <FilterX className="size-4 mr-1" />
                    Clear Filters
                  </Button>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Claim ID</TableHead>
                      <TableHead>Member</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Decision</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.map((claim) => (
                      <TableRow
                        key={claim.claim_id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/admin/claims/${claim.claim_id}`)}
                      >
                        <TableCell className="font-mono text-xs font-medium">
                          #{claim.claim_id}
                        </TableCell>
                        <TableCell className="text-sm">{claim.member_id}</TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {getCategoryLabel(claim.claim_category)}
                        </TableCell>
                        <TableCell className="font-mono text-sm tabular-nums">
                          {formatCurrency(claim.claimed_amount)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`font-medium ${statusBadgeClass(claim.status)}`}
                          >
                            {claim.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {claim.decision ? (
                            <Badge
                              variant="outline"
                              className={`font-medium ${decisionBadgeClass(claim.decision)}`}
                            >
                              {claim.decision === 'MANUAL_REVIEW' ? 'Review' : claim.decision}
                            </Badge>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground whitespace-nowrap">
                          {formatDate(claim.submitted_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Pagination */}
      {total > PAGE_SIZE && !loading && (
        <motion.div variants={item} className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {currentPage} of {totalPages || 1}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset <= 0}
              onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
            >
              <ChevronLeft className="size-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
            >
              Next
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default function AdminClaimsPage() {
  return (
    <Suspense fallback={<ClaimsTableSkeleton />}>
      <AdminClaimsPageContent />
    </Suspense>
  );
}
