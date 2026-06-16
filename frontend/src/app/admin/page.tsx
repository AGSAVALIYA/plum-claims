'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, AlertCircle, FileText, CheckCircle2, XCircle, Eye, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { getAdminDashboard } from '@/lib/api';
import type { AdminDashboardResponse } from '@/types';

// ── Helpers ─────────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
  SUBMITTED: 'Submitted',
  VALIDATING: 'Validating',
  PROCESSING: 'Processing',
  DECIDED: 'Decided',
  DOCUMENT_ERROR: 'Document Error',
  ERROR: 'Error',
  CLOSED: 'Closed',
};

const STATUS_COLORS: Record<string, string> = {
  SUBMITTED: 'bg-status-info',
  VALIDATING: 'bg-[#3EC1C5]',
  PROCESSING: 'bg-status-info',
  DECIDED: 'bg-status-approved',
  DOCUMENT_ERROR: 'bg-status-warning',
  ERROR: 'bg-status-rejected',
  CLOSED: 'bg-[#6B6560]',
};

const DECISION_LABELS: Record<string, string> = {
  APPROVED: 'Approved',
  PARTIAL: 'Partially Approved',
  REJECTED: 'Rejected',
  MANUAL_REVIEW: 'Manual Review',
};

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

function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(amount);
}

// ── Animation Variants ──────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const } },
};

// ── Loading Skeleton ─────────────────────────────────────────

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-48 bg-muted rounded-lg" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
            <div className="h-10 w-24 bg-muted rounded mb-2" />
            <div className="h-4 w-20 bg-muted rounded" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
          <div className="h-5 w-40 bg-muted rounded mb-4" />
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-4 bg-muted rounded w-full" />
            ))}
          </div>
        </div>
        <div className="rounded-xl bg-card p-6 ring-1 ring-foreground/10">
          <div className="h-5 w-40 bg-muted rounded mb-4" />
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <div className="h-5 w-5 bg-muted rounded-full" />
                <div className="flex-1">
                  <div className="h-4 bg-muted rounded w-3/4 mb-1" />
                  <div className="h-3 bg-muted rounded w-1/4" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Stat Card ────────────────────────────────────────────────

function StatCard({
  title,
  value,
  color,
  icon: Icon,
  delay = 0,
}: {
  title: string;
  value: string | number;
  color: string;
  icon: React.ElementType;
  delay?: number;
}) {
  return (
    <motion.div variants={itemVariants}>
      <Card className="relative overflow-hidden">
        <div className={`absolute left-0 top-0 bottom-0 w-1 ${color}`} />
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-muted-foreground font-normal text-sm">
            <Icon className="size-4" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p
            className="text-3xl sm:text-4xl font-bold tracking-tight"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            {value}
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ── Status Bar ───────────────────────────────────────────────

function StatusBar({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 text-sm text-muted-foreground truncate shrink-0">{label}</span>
      <div className="flex-1 h-5 rounded-full bg-muted overflow-hidden relative">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] as const, delay: 0.2 }}
        />
      </div>
      <span className="w-16 text-right text-sm font-medium tabular-nums shrink-0">
        {count.toLocaleString()}
      </span>
    </div>
  );
}

// ── Recent Event Item ────────────────────────────────────────

function RecentEventItem({
  event,
  index,
}: {
  event: Record<string, unknown>;
  index: number;
}) {
  const description = (event.description as string) || (event.event as string) || (event.message as string) || '';
  const timestamp = (event.timestamp as string) || (event.created_at as string) || (event.date as string) || '';
  const type = (event.type as string) || (event.event_type as string) || '';

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="flex items-start gap-3 py-2.5 border-b border-border last:border-0"
    >
      <div className="size-2 rounded-full bg-primary mt-1.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-foreground truncate">{description || 'Event'}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {type && (
            <Badge variant="outline" className="text-[10px] px-1 py-0 h-4">
              {type}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">{formatDate(timestamp) || ''}</span>
        </div>
      </div>
    </motion.div>
  );
}

// ── Main Dashboard Component ─────────────────────────────────

export default function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getAdminDashboard();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ── Loading State ──────────────────────────────────────────
  if (loading && !data) {
    return <DashboardSkeleton />;
  }

  // ── Error State ────────────────────────────────────────────
  if (error && !data) {
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
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="size-4 mr-1.5" />
          Retry
        </Button>
      </motion.div>
    );
  }

  if (!data) return null;

  const totalClaims = data.total_claims;
  const statusCounts = data.status_counts || {};
  const decisionCounts = data.decision_counts || {};
  const totalDecisions = Object.values(decisionCounts).reduce((a, b) => a + b, 0);
  const avgConfidence = data.avg_confidence ?? 0;
  const manualReviewCount = data.manual_review_count ?? 0;
  const events = data.recent_events || [];

  const approvedCount = decisionCounts['APPROVED'] ?? 0;
  const rejectedCount = decisionCounts['REJECTED'] ?? 0;
  const partialCount = decisionCounts['PARTIAL'] ?? 0;

  const statusEntries = Object.entries(statusCounts).sort(([a], [b]) => a.localeCompare(b));

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      {/* Page Title */}
      <motion.div variants={itemVariants}>
        <h1
          className="text-2xl sm:text-3xl font-bold tracking-tight"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Admin Dashboard
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Overview of claims processing activity
        </p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <StatCard
          title="Total Claims"
          value={totalClaims.toLocaleString()}
          color="bg-status-info"
          icon={FileText}
        />
        <StatCard
          title="Approved"
          value={approvedCount.toLocaleString()}
          color="bg-status-approved"
          icon={CheckCircle2}
        />
        <StatCard
          title="Rejected"
          value={rejectedCount.toLocaleString()}
          color="bg-status-rejected"
          icon={XCircle}
        />
        <StatCard
          title="Manual Review"
          value={manualReviewCount.toLocaleString()}
          color="bg-status-warning"
          icon={Eye}
        />
      </div>

      {/* Bottom Row: Confidence + Status + Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Average Confidence */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                <BarChart3 className="size-4 text-primary" />
                Average Confidence
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <BarChart3 className="size-3.5" />
                  Confidence Score
                </div>
                <span className="text-sm font-medium tabular-nums">
                  {(avgConfidence * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={avgConfidence * 100} />
              <p className="text-xs text-muted-foreground">
                Based on {totalClaims.toLocaleString()} processed claims
              </p>
            </CardContent>
          </Card>
        </motion.div>

        {/* Status Distribution */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                Status Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {statusEntries.length === 0 ? (
                <p className="text-sm text-muted-foreground">No status data available</p>
              ) : (
                statusEntries.map(([status, count]) => (
                  <StatusBar
                    key={status}
                    label={STATUS_LABELS[status] || status}
                    count={count}
                    total={totalClaims}
                    color={STATUS_COLORS[status] || 'bg-muted-foreground'}
                  />
                ))
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Events */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm font-medium">
                Recent Events
              </CardTitle>
              <CardDescription>Latest claim activity</CardDescription>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <p className="text-sm text-muted-foreground py-4 text-center">No recent events</p>
              ) : (
                <div className="divide-y divide-border">
                  {events.slice(0, 10).map((event, i) => (
                    <RecentEventItem key={i} event={event} index={i} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
