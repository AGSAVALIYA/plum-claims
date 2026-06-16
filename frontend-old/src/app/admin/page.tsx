'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { ClaimResponse, AdminDashboardStats } from '@/types';
import * as api from '@/lib/api';
import { isAdmin } from '@/lib/auth';
import DecisionBadge from '@/components/ui/DecisionBadge';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import MetricCard from '@/components/ui/MetricCard';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    member_id: '',
    status: '',
    decision: '',
  });

  const fetchDashboard = useCallback(async () => {
    try {
      const [dashboardData, claimsData] = await Promise.all([
        api.getAdminDashboard(),
        api.getAdminClaims({
          member_id: filters.member_id || undefined,
          status: filters.status || undefined,
          decision: filters.decision || undefined,
          limit: 50,
        }),
      ]);
      setStats(dashboardData);
      setClaims(claimsData.claims);
      setTotal(claimsData.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    if (!isAdmin()) {
      setError('Admin access required');
      setLoading(false);
      return;
    }
    fetchDashboard();
  }, [fetchDashboard]);

  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(fetchDashboard, 10000);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  if (!isAdmin()) {
    return (
      <div className="p-10 text-center">
        <span className="text-5xl block mb-4" aria-hidden="true">🔒</span>
        <h1 className="text-2xl font-bold text-[var(--color-danger-600)] mb-2">Access Denied</h1>
        <p className="text-[var(--color-text-secondary)] mb-4">
          You need admin privileges to access this page.
        </p>
        <Link
          href="/login"
          className="inline-flex items-center rounded-xl bg-[var(--color-primary-500)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--color-primary-600)] transition-colors duration-150 shadow-sm"
        >
          Login as Admin →
        </Link>
      </div>
    );
  }

  if (loading) return <LoadingSpinner message="Loading admin dashboard…" />;

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-[var(--color-danger-600)] text-lg font-semibold mb-2">Error</p>
        <p className="text-[var(--color-text-secondary)]">{error}</p>
        <button
          onClick={fetchDashboard}
          className="mt-4 text-sm font-semibold text-[var(--color-primary-600)] hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  const formatAmount = (amount?: number) =>
    amount != null ? `₹${amount.toLocaleString()}` : '—';

  const formatDate = (dateStr?: string) =>
    dateStr ? new Date(dateStr).toLocaleDateString() : '—';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">Admin Dashboard</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">
          Overview of all claims and system activity across all members.
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Total Claims" value={stats.total_claims} />
            <MetricCard
              label="Pending"
              value={stats.status_counts['SUBMITTED'] || 0}
              valueClassName="text-[var(--color-info-700)]"
            />
            <MetricCard
              label="Approved"
              value={stats.decision_counts['APPROVED'] || 0}
              valueClassName="text-[var(--color-success-700)]"
            />
            <MetricCard
              label="Rejected"
              value={stats.decision_counts['REJECTED'] || 0}
              valueClassName="text-[var(--color-danger-700)]"
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <MetricCard
              label="Manual Review"
              value={stats.manual_review_count}
              valueClassName="text-[var(--color-warning-700)]"
            />
            <MetricCard
              label="Avg Confidence"
              value={`${(stats.avg_confidence * 100).toFixed(0)}%`}
              valueClassName="text-[var(--color-primary-600)]"
            />
            <MetricCard
              label="In Processing"
              value={(stats.status_counts['PROCESSING'] || 0) + (stats.status_counts['VALIDATING'] || 0)}
              valueClassName="text-[var(--color-info-700)]"
            />
          </div>
        </>
      )}

      {/* Recent Activity */}
      {stats && stats.recent_events.length > 0 && (
        <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-5 sm:p-6">
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">Recent Activity</h2>
          <div className="space-y-2">
            {stats.recent_events.map((event) => (
              <div
                key={event.event_id}
                className="flex flex-wrap items-center gap-3 text-sm py-2.5 px-3 rounded-lg hover:bg-[var(--color-surface-muted)] transition-colors duration-150"
              >
                <span
                  className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                    event.event_type === 'STEP_FAILED'
                      ? 'bg-[var(--color-danger-500)]'
                      : event.event_type === 'DECISION_MADE'
                      ? 'bg-[var(--color-success-500)]'
                      : event.event_type === 'ADMIN_OVERRIDE'
                      ? 'bg-purple-500'
                      : 'bg-[var(--color-info-500)]'
                  }`}
                  aria-hidden="true"
                />
                <Link
                  href={`/admin/claims/${event.claim_id}`}
                  className="text-[var(--color-primary-600)] hover:text-[var(--color-primary-800)] font-semibold transition-colors duration-150"
                >
                  #{event.claim_id}
                </Link>
                <span className="text-[var(--color-text-secondary)]">
                  {event.event_type.replace(/_/g, ' ')}
                </span>
                {event.comment && (
                  <span className="text-[var(--color-text-muted)] truncate max-w-xs">
                    — {event.comment}
                  </span>
                )}
                <span className="text-[var(--color-text-muted)] ml-auto text-xs whitespace-nowrap">
                  {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-4 sm:p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label htmlFor="admin-filter-member" className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
              Member ID
            </label>
            <input
              id="admin-filter-member"
              type="text"
              value={filters.member_id}
              onChange={(e) => setFilters({ ...filters, member_id: e.target.value })}
              placeholder="e.g., EMP001"
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150"
            />
          </div>
          <div>
            <label htmlFor="admin-filter-status" className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
              Status
            </label>
            <select
              id="admin-filter-status"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150"
            >
              <option value="">All Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="PROCESSING">Processing</option>
              <option value="DECIDED">Decided</option>
              <option value="DOCUMENT_ERROR">Document Error</option>
              <option value="ERROR">Error</option>
            </select>
          </div>
          <div>
            <label htmlFor="admin-filter-decision" className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
              Decision
            </label>
            <select
              id="admin-filter-decision"
              value={filters.decision}
              onChange={(e) => setFilters({ ...filters, decision: e.target.value })}
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3 py-2 text-sm text-[var(--color-text-primary)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] transition-colors duration-150"
            >
              <option value="">All Decisions</option>
              <option value="APPROVED">Approved</option>
              <option value="PARTIAL">Partial</option>
              <option value="REJECTED">Rejected</option>
              <option value="MANUAL_REVIEW">Manual Review</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={fetchDashboard}
              className="w-full rounded-xl bg-[var(--color-primary-500)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--color-primary-600)] transition-colors duration-150 min-h-touch shadow-sm"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Claims Table */}
      <div>
        <p className="text-sm text-[var(--color-text-muted)] mb-3">{total} claim(s) found</p>

        {/* Desktop table */}
        <div className="hidden md:block bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] overflow-hidden shadow-sm">
          <table className="min-w-full divide-y divide-[var(--color-border)]">
            <thead className="bg-[var(--color-surface-muted)]">
              <tr>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Member
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Category
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Decision
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                  Date
                </th>
                <th className="px-4 py-3.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {claims.map((claim) => (
                <tr key={claim.claim_id} className="hover:bg-[var(--color-surface-muted)] transition-colors duration-150">
                  <td className="px-4 py-3.5 text-sm font-semibold text-[var(--color-text-primary)]">
                    #{claim.claim_id}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-[var(--color-text-secondary)]">
                    {claim.member_id}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-[var(--color-text-secondary)]">
                    {claim.claim_category?.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3.5 text-sm font-medium text-[var(--color-text-primary)]">
                    {formatAmount(claim.claimed_amount)}
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={claim.status} />
                  </td>
                  <td className="px-4 py-3.5">
                    <DecisionBadge decision={claim.decision || claim.status} />
                  </td>
                  <td className="px-4 py-3.5 text-sm text-[var(--color-text-secondary)]">
                    {claim.confidence_score ? `${(claim.confidence_score * 100).toFixed(0)}%` : '—'}
                  </td>
                  <td className="px-4 py-3.5 text-sm text-[var(--color-text-muted)]">
                    {formatDate(claim.submitted_at)}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <Link
                      href={`/admin/claims/${claim.claim_id}`}
                      className="text-sm font-semibold text-[var(--color-primary-600)] hover:text-[var(--color-primary-800)] transition-colors duration-150"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden space-y-3">
          {claims.map((claim) => (
            <Link
              key={claim.claim_id}
              href={`/admin/claims/${claim.claim_id}`}
              className="block bg-[var(--color-surface-raised)] rounded-xl border border-[var(--color-border)] p-4 hover:border-[var(--color-primary-300)] hover:shadow-sm transition-all duration-150"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-bold text-[var(--color-text-primary)]">
                  #{claim.claim_id}
                </span>
                <StatusBadge status={claim.status} />
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Member</span>
                  <p className="font-medium text-[var(--color-text-primary)]">{claim.member_id}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Amount</span>
                  <p className="font-medium text-[var(--color-text-primary)]">{formatAmount(claim.claimed_amount)}</p>
                </div>
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Decision</span>
                  <p><DecisionBadge decision={claim.decision || claim.status} /></p>
                </div>
                <div>
                  <span className="text-xs text-[var(--color-text-muted)]">Confidence</span>
                  <p className="text-[var(--color-text-secondary)]">
                    {claim.confidence_score ? `${(claim.confidence_score * 100).toFixed(0)}%` : '—'}
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-end">
                <span className="text-sm font-semibold text-[var(--color-primary-600)]">View Details →</span>
              </div>
            </Link>
          ))}
          {claims.length === 0 && (
            <p className="text-center text-[var(--color-text-muted)] py-8">No claims match the filters.</p>
          )}
        </div>
      </div>
    </div>
  );
}
