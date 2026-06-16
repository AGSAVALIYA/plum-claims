'use client';

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { FileText, CheckCircle, Clock, DollarSign, Plus } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { listClaims } from '@/lib/api';
import type { ClaimResponse } from '@/types';
import { cn } from '@/lib/utils';

// ── Helpers ──────────────────────────────────────────────────

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

function getStatusBadgeVariant(status: string) {
  switch (status) {
    case 'APPROVED':
      return 'default';
    case 'REJECTED':
    case 'PARTIAL':
    case 'DOCUMENT_ERROR':
    case 'ERROR':
      return 'destructive';
    default:
      return 'secondary';
  }
}

// ── Stat Card ─────────────────────────────────────────────────

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  accent?: 'primary' | 'success' | 'warning' | 'accent';
  isLoading?: boolean;
}

function StatCard({ title, value, icon, accent = 'primary', isLoading }: StatCardProps) {
  const accentColors: Record<string, string> = {
    primary: 'bg-primary/10 text-primary',
    success: 'bg-[#2D8B6E]/10 text-[#2D8B6E]',
    warning: 'bg-[#E8A838]/10 text-[#E8A838]',
    accent: 'bg-[#D45161]/10 text-[#D45161]',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      <Card size="sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {title}
          </CardTitle>
          <div className={cn('flex size-7 items-center justify-center rounded-md', accentColors[accent])}>
            {icon}
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="h-8 w-20 animate-pulse rounded-md bg-muted" />
          ) : (
            <p className="text-2xl font-semibold tracking-tight">{value}</p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Skeleton ──────────────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      <div className="h-8 w-72 animate-pulse rounded-md bg-muted" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} size="sm">
            <CardHeader className="pb-2">
              <div className="h-3 w-20 animate-pulse rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="h-5 w-32 animate-pulse rounded bg-muted" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} size="sm">
            <CardHeader className="pb-2">
              <div className="h-4 w-24 animate-pulse rounded bg-muted" />
              <div className="h-3 w-16 animate-pulse rounded bg-muted" />
            </CardHeader>
            <CardContent>
              <div className="h-3 w-full animate-pulse rounded bg-muted" />
              <div className="mt-2 h-5 w-20 animate-pulse rounded bg-muted" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ── Claim Card ───────────────────────────────────────────────

function ClaimCard({ claim, index }: { claim: ClaimResponse; index: number }) {
  const router = useRouter();
  const decision = claim.decision;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.08, ease: 'easeOut' }}
      onClick={() => router.push(`/claims/${claim.claim_id}`)}
    >
      <Card
        size="sm"
        className="cursor-pointer transition-shadow hover:shadow-sm"
      >
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              <span className="text-primary">#{claim.claim_id}</span>
              <span className="ml-2 text-muted-foreground">
                {claim.claim_category?.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())}
              </span>
            </CardTitle>
            <Badge
              variant={getStatusBadgeVariant(decision || claim.status)}
              className={cn(
                decision === 'APPROVED' && 'bg-[#2D8B6E]/10 text-[#2D8B6E]',
                decision === 'REJECTED' && undefined,
                !decision && claim.status === 'SUBMITTED' && 'bg-[#E8A838]/10 text-[#E8A838]'
              )}
            >
              {decision || claim.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {formatDate(claim.submitted_at)}
            </span>
            <span className="font-medium">
              {formatCurrency(claim.claimed_amount)}
            </span>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Dashboard Page ───────────────────────────────────────────

export default function DashboardPage() {
  const { user, isLoading: isAuthLoading } = useAuth();
  const router = useRouter();
  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthLoading) return;
    if (!user) {
      router.push('/login');
      return;
    }

    const memberId = user.member_id;
    let cancelled = false;

    async function fetchClaims() {
      try {
        setIsLoading(true);
        const response = await listClaims({ member_id: memberId, limit: 100 });
        if (!cancelled) {
          setClaims(response.claims ?? []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load claims');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchClaims();
    return () => { cancelled = true; };
  }, [user, isAuthLoading, router]);

  // Compute stats
  const stats = useMemo(() => {
    const total = claims.length;
    const approved = claims.filter(
      (c) => c.decision === 'APPROVED'
    ).length;
    const pending = claims.filter(
      (c) =>
        !c.decision ||
        c.decision === 'MANUAL_REVIEW' ||
        ['SUBMITTED', 'VALIDATING', 'PROCESSING'].includes(c.status)
    ).length;
    const totalAmount = claims.reduce(
      (sum, c) => sum + (c.claimed_amount ?? 0),
      0
    );
    return { total, approved, pending, totalAmount };
  }, [claims]);

  const recentClaims = useMemo(
    () => claims.slice(0, 5),
    [claims]
  );

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <FileText className="size-12 text-destructive/50" />
        <p className="text-sm text-destructive">{error}</p>
        <Button
          variant="outline"
          onClick={() => window.location.reload()}
        >
          Try Again
        </Button>
      </div>
    );
  }

  // Loading state
  if (isLoading || isAuthLoading) {
    return <DashboardSkeleton />;
  }

  const isEmpty = claims.length === 0;

  return (
    <div className="flex flex-col gap-6">
      {/* Welcome */}
      <motion.h1
        className="text-2xl font-semibold tracking-tight md:text-3xl"
        style={{ fontFamily: 'var(--font-display)' }}
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        Welcome back, {user?.member_name ?? 'Member'}
      </motion.h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Claims"
          value={stats.total}
          icon={<FileText className="size-3.5" />}
          accent="primary"
        />
        <StatCard
          title="Approved"
          value={stats.approved}
          icon={<CheckCircle className="size-3.5" />}
          accent="success"
        />
        <StatCard
          title="Pending"
          value={stats.pending}
          icon={<Clock className="size-3.5" />}
          accent="warning"
        />
        <StatCard
          title="Total Amount"
          value={formatCurrency(stats.totalAmount)}
          icon={<DollarSign className="size-3.5" />}
          accent="accent"
        />
      </div>

      {/* Recent Claims / Empty State */}
      {isEmpty ? (
        <motion.div
          className="flex flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card py-20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex size-20 items-center justify-center rounded-full bg-muted">
            <FileText className="size-10 text-muted-foreground/50" />
          </div>
          <div className="flex flex-col items-center gap-1 text-center">
            <h3 className="text-lg font-medium text-foreground">
              No claims yet
            </h3>
            <p className="max-w-xs text-sm text-muted-foreground">
              Submit your first one! It only takes a few minutes to get started.
            </p>
          </div>
          <Button
            variant="default"
            size="default"
            onClick={() => router.push('/claims/new')}
            className="mt-2"
          >
            <Plus className="size-4" />
            Submit New Claim
          </Button>
        </motion.div>
      ) : (
        <>
          {/* Section header */}
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Recent Claims
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/claims')}
            >
              View all
            </Button>
          </div>

          {/* Recent claims cards */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {recentClaims.map((claim, index) => (
              <ClaimCard key={claim.claim_id} claim={claim} index={index} />
            ))}
          </div>
        </>
      )}

      {/* Quick Actions */}
      <div className="mt-2">
        <h2 className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Quick Actions
        </h2>
        <Button
          variant="default"
          size="lg"
          onClick={() => router.push('/claims/new')}
          className="gap-2"
        >
          <Plus className="size-4" />
          Submit New Claim
        </Button>
      </div>
    </div>
  );
}
