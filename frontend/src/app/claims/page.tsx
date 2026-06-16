'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Search, FileText, Loader2, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { listClaims } from '@/lib/api';
import type { ClaimResponse, ClaimStatus, Decision } from '@/types';
import { cn } from '@/lib/utils';

// ── Helpers ──────────────────────────────────────────────────

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

function getCategoryLabel(category: string | null | undefined): string {
  if (!category) return '—';
  return category
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function getStatusBadgeConfig(status: ClaimStatus | Decision | null | undefined): {
  variant: 'default' | 'secondary' | 'destructive' | 'outline';
  className: string;
} {
  if (!status) return { variant: 'outline', className: '' };

  if (status === 'APPROVED') {
    return {
      variant: 'default',
      className: 'bg-[#2D8B6E]/10 text-[#2D8B6E] border-[#2D8B6E]/20',
    };
  }

  if (status === 'REJECTED' || status === 'PARTIAL') {
    return {
      variant: 'destructive',
      className: '',
    };
  }

  if (status === 'MANUAL_REVIEW' || status === 'DOCUMENT_ERROR' || status === 'ERROR') {
    return {
      variant: 'destructive',
      className: '',
    };
  }

  // PENDING / SUBMITTED / VALIDATING / PROCESSING
  return {
    variant: 'secondary',
    className: 'bg-[#E8A838]/10 text-[#E8A838] border-[#E8A838]/20',
  };
}

function getDisplayStatus(claim: ClaimResponse): string {
  return claim.decision ?? claim.status;
}

// ── Skeleton ──────────────────────────────────────────────────

function ClaimsListSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      <div className="h-8 w-48 animate-pulse rounded bg-muted" />
      <div className="h-9 w-full animate-pulse rounded bg-muted" />
      <Card>
        <CardContent className="p-0">
          <div className="flex flex-col">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className={cn(
                  'flex items-center gap-4 px-4 py-3',
                  i !== 0 && 'border-t border-border'
                )}
              >
                <div className="h-4 w-12 animate-pulse rounded bg-muted" />
                <div className="h-4 w-24 animate-pulse rounded bg-muted" />
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
                <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                <div className="ml-auto h-5 w-20 animate-pulse rounded bg-muted" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ── Claims Page ──────────────────────────────────────────────

export default function ClaimsPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();

  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Pagination
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const LIMIT = 20;

  const fetchClaims = useCallback(
    async (append = false) => {
      if (!user) return;
      try {
        if (append) {
          setIsLoadingMore(true);
        } else {
          setIsLoading(true);
        }

        const params: {
          member_id: string;
          status?: string;
          limit: number;
          offset: number;
        } = {
          member_id: user.member_id,
          limit: LIMIT,
          offset: append ? offset : 0,
        };

        if (statusFilter) {
          params.status = statusFilter;
        }

        const response = await listClaims(params);
        const newClaims = response.claims ?? [];

        if (append) {
          setClaims((prev) => [...prev, ...newClaims]);
        } else {
          setClaims(newClaims);
        }
        setTotal(response.total ?? newClaims.length);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load claims');
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [user, statusFilter, offset]
  );

  // Initial load
  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) {
      router.push('/login');
      return;
    }
    setOffset(0);
    fetchClaims(false);
  }, [user, isAuthLoading, statusFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLoadMore = useCallback(() => {
    const newOffset = offset + LIMIT;
    setOffset(newOffset);
    fetchClaims(true);
  }, [offset, fetchClaims]);

  // Filter by search query (client-side)
  const filteredClaims = useMemo(() => {
    if (!searchQuery.trim()) return claims;
    const q = searchQuery.toLowerCase();
    return claims.filter(
      (c) =>
        String(c.claim_id).includes(q) ||
        (c.claim_category ?? '').toLowerCase().includes(q) ||
        (c.hospital_name ?? '').toLowerCase().includes(q) ||
        (c.decision ?? '').toLowerCase().includes(q) ||
        c.status.toLowerCase().includes(q)
    );
  }, [claims, searchQuery]);

  const hasMore = offset + LIMIT < total;

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <FileText className="size-12 text-destructive/50" />
        <p className="text-sm text-destructive">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Try Again
        </Button>
      </div>
    );
  }

  if (isAuthLoading) {
    return <ClaimsListSkeleton />;
  }

  return (
    <motion.div
      className="flex flex-col gap-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1
          className="text-2xl font-semibold tracking-tight md:text-3xl"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          My Claims
        </h1>
        <Button variant="default" onClick={() => router.push('/claims/new')}>
          Submit New Claim
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-3 sm:flex-row">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search claims..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-9 pl-8"
          />
        </div>

        {/* Status filter */}
        <div className="w-full sm:w-44">
          <Select
            value={statusFilter}
            onValueChange={(value: string | null) => {
              if (value !== null) setStatusFilter(value);
            }}
          >
            <SelectTrigger className="h-9 w-full">
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
      </div>

      {/* Loading state */}
      {isLoading && !isLoadingMore ? (
        <ClaimsListSkeleton />
      ) : filteredClaims.length === 0 ? (
        /* Empty state */
        <motion.div
          className="flex flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card py-20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          <div className="flex size-20 items-center justify-center rounded-full bg-muted">
            <FileText className="size-10 text-muted-foreground/50" />
          </div>
          <div className="flex flex-col items-center gap-1 text-center">
            <h3 className="text-lg font-medium text-foreground">
              {searchQuery || statusFilter
                ? 'No matching claims found'
                : 'No claims yet'}
            </h3>
            <p className="max-w-xs text-sm text-muted-foreground">
              {searchQuery || statusFilter
                ? 'Try adjusting your search or filters.'
                : 'Submit your first health insurance claim.'}
            </p>
          </div>
          {!searchQuery && !statusFilter && (
            <Button
              variant="default"
              onClick={() => router.push('/claims/new')}
              className="mt-2"
            >
              Submit New Claim
            </Button>
          )}
        </motion.div>
      ) : (
        /* Claims Table */
        <Card>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">Claim ID</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Decision</TableHead>
                  <TableHead className="w-[40px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredClaims.map((claim, index) => {
                  const displayStatus = getDisplayStatus(claim);
                  const badgeConfig = getStatusBadgeConfig(
                    claim.decision ?? claim.status
                  );

                  return (
                    <TableRow
                      key={claim.claim_id}
                      className="cursor-pointer transition-colors hover:bg-muted/50"
                      onClick={() => router.push(`/claims/${claim.claim_id}`)}
                    >
                      <TableCell className="font-medium text-primary">
                        #{claim.claim_id}
                      </TableCell>
                      <TableCell>
                        {getCategoryLabel(claim.claim_category)}
                      </TableCell>
                      <TableCell>
                        {formatCurrency(claim.claimed_amount)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(claim.submitted_at)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={badgeConfig.variant}
                          className={badgeConfig.className}
                        >
                          {displayStatus}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {claim.decision ? (
                          <Badge
                            variant={badgeConfig.variant}
                            className={badgeConfig.className}
                          >
                            {claim.decision}
                          </Badge>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            Pending
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <ChevronRight className="size-4 text-muted-foreground" />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}

      {/* Load More */}
      {hasMore && filteredClaims.length > 0 && (
        <div className="flex justify-center">
          <Button
            variant="outline"
            onClick={handleLoadMore}
            disabled={isLoadingMore}
            className="min-w-[140px]"
          >
            {isLoadingMore ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Loading...
              </>
            ) : (
              `Load More (${filteredClaims.length} of ${total})`
            )}
          </Button>
        </div>
      )}
    </motion.div>
  );
}
