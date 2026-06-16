'use client';

import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { ClaimResponse } from '@/types';
import * as api from '@/lib/api';
import { getMemberId } from '@/lib/auth';
import DecisionBadge from '@/components/ui/DecisionBadge';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

type Tab = 'all' | 'processing' | 'completed' | 'failed';

const TABS: { key: Tab; label: string; statuses?: string[] }[] = [
  { key: 'all', label: 'All Claims' },
  { key: 'processing', label: 'Processing', statuses: ['SUBMITTED', 'VALIDATING', 'PROCESSING'] },
  { key: 'completed', label: 'Completed', statuses: ['DECIDED'] },
  { key: 'failed', label: 'Failed', statuses: ['DOCUMENT_ERROR', 'ERROR'] },
];

export default function ClaimsListPage() {
  const [claims, setClaims] = useState<ClaimResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('all');

  const fetchClaims = useCallback(async () => {
    setLoading(true);
    setError(null);
    const memberId = getMemberId();
    try {
      const params: Record<string, string> = {};
      if (memberId) params.member_id = memberId;

      // Apply tab filter
      const tab = TABS.find((t) => t.key === activeTab);
      if (tab?.statuses) {
        const data = await api.listClaims({ ...params, limit: 100 });
        const filtered = data.claims.filter((c) => tab.statuses!.includes(c.status));
        setClaims(filtered);
        setTotal(filtered.length);
      } else {
        const data = await api.listClaims(params);
        setClaims(data.claims);
        setTotal(data.total);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchClaims();
  }, [fetchClaims]);

  // Auto-refresh for processing claims
  useEffect(() => {
    if (activeTab === 'processing' || activeTab === 'all') {
      const interval = setInterval(fetchClaims, 5000);
      return () => clearInterval(interval);
    }
  }, [activeTab, fetchClaims]);

  const formatAmount = (amount?: number) =>
    amount != null ? `₹${amount.toLocaleString()}` : '—';

  const formatDate = (dateStr?: string) =>
    dateStr ? new Date(dateStr).toLocaleDateString() : '—';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">My Claims</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">
          Track and manage your health insurance claims.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-[var(--color-border)] overflow-x-auto">
        <nav className="flex gap-1 min-w-max" role="tablist" aria-label="Claim status filters">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeTab === tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 px-2 text-sm font-semibold border-b-2 transition-colors duration-150 whitespace-nowrap ${
                activeTab === tab.key
                  ? 'border-[var(--color-primary-500)] text-[var(--color-primary-600)]'
                  : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:border-[var(--color-border-hover)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      {loading ? (
        <LoadingSpinner message="Loading claims…" />
      ) : error ? (
        <div className="bg-[var(--color-danger-50)] border border-[var(--color-danger-100)] rounded-xl p-6" role="alert">
          <p className="text-sm text-[var(--color-danger-700)]">{error}</p>
          <button onClick={fetchClaims} className="mt-2 text-sm font-semibold text-[var(--color-danger-600)] hover:underline">
            Try again
          </button>
        </div>
      ) : claims.length === 0 ? (
        <div className="bg-[var(--color-surface-muted)] rounded-xl p-10 text-center border border-[var(--color-border)]">
          <span className="text-4xl block mb-3" aria-hidden="true">📭</span>
          <p className="text-[var(--color-text-secondary)] text-lg font-medium mb-1">No claims found</p>
          <p className="text-[var(--color-text-muted)] text-sm mb-4">
            {activeTab === 'all'
              ? "You haven't submitted any claims yet."
              : `No claims in this category.`}
          </p>
          <Link
            href="/"
            className="inline-flex items-center rounded-xl bg-[var(--color-primary-500)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--color-primary-600)] transition-colors duration-150 shadow-sm"
          >
            Submit a New Claim →
          </Link>
        </div>
      ) : (
        <>
          <p className="text-sm text-[var(--color-text-muted)]">
            {total} claim{total !== 1 ? 's' : ''} found
          </p>

          {/* Desktop table (≥md) */}
          <div className="hidden md:block bg-[var(--color-surface-raised)] rounded-xl shadow-sm border border-[var(--color-border)] overflow-hidden">
            <table className="min-w-full divide-y divide-[var(--color-border)]">
              <thead className="bg-[var(--color-surface-muted)]">
                <tr>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
                    Claim ID
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
                    <td className="px-4 py-3.5 text-sm text-[var(--color-text-muted)]">
                      {formatDate(claim.submitted_at)}
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <Link
                        href={`/claims/${claim.claim_id}`}
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

          {/* Mobile cards (<md) */}
          <div className="md:hidden space-y-3">
            {claims.map((claim) => (
              <Link
                key={claim.claim_id}
                href={`/claims/${claim.claim_id}`}
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
                    <span className="text-xs text-[var(--color-text-muted)]">Category</span>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {claim.claim_category?.replace(/_/g, ' ')}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-[var(--color-text-muted)]">Amount</span>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {formatAmount(claim.claimed_amount)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-[var(--color-text-muted)]">Decision</span>
                    <p>
                      <DecisionBadge decision={claim.decision || claim.status} />
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-[var(--color-text-muted)]">Date</span>
                    <p className="text-[var(--color-text-secondary)]">{formatDate(claim.submitted_at)}</p>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <span className="text-sm font-semibold text-[var(--color-primary-600)]">
                    View Details →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
