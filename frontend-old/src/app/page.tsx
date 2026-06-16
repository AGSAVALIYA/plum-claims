'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import CustomSelect from '@/components/ui/CustomSelect';
import CustomFileUploader, { type UploadedFileEntry } from '@/components/ui/CustomFileUploader';

const CATEGORIES = [
  { value: 'CONSULTATION', label: 'Consultation (Doctor Visit)' },
  { value: 'DIAGNOSTIC', label: 'Diagnostic (Lab Tests, Scans)' },
  { value: 'PHARMACY', label: 'Pharmacy (Medicines)' },
  { value: 'DENTAL', label: 'Dental' },
  { value: 'VISION', label: 'Vision (Eye Care)' },
  { value: 'ALTERNATIVE_MEDICINE', label: 'Alternative Medicine (AYUSH)' },
];

const DOC_TYPES = [
  'PRESCRIPTION',
  'HOSPITAL_BILL',
  'LAB_REPORT',
  'PHARMACY_BILL',
  'DENTAL_REPORT',
  'DIAGNOSTIC_REPORT',
  'DISCHARGE_SUMMARY',
];

export default function HomePage() {
  const { isAuthenticated, memberId } = useAuth();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const [form, setForm] = useState({
    member_id: 'EMP001',
    claim_category: 'CONSULTATION',
    treatment_date: new Date().toISOString().split('T')[0],
    claimed_amount: '',
    hospital_name: '',
    ytd_claims_amount: '',
  });

  // Sync member_id from auth after mount
  useEffect(() => {
    if (mounted && memberId) {
      setForm((f) => ({ ...f, member_id: memberId }));
    }
  }, [mounted, memberId]);

  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [submittedClaimId, setSubmittedClaimId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSubmittedClaimId(null);

    try {
      if (uploadedFiles.length === 0) {
        throw new Error('Please upload at least one document to submit your claim.');
      }

      const { submitClaimWithFiles } = await import('@/lib/api');

      const formData = new FormData();
      formData.append('member_id', form.member_id);
      formData.append('claim_category', form.claim_category);
      formData.append('treatment_date', form.treatment_date);
      formData.append('claimed_amount', form.claimed_amount || '0');
      formData.append('hospital_name', form.hospital_name);
      formData.append('ytd_claims_amount', form.ytd_claims_amount || '0');
      formData.append('claims_history', '[]');
      formData.append(
        'document_types',
        JSON.stringify(uploadedFiles.map((f) => f.document_type))
      );

      for (const uf of uploadedFiles) {
        formData.append('files', uf.file);
      }

      const response = await submitClaimWithFiles(formData);
      setSubmittedClaimId(response.claim_id);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const formErrors: Partial<Record<string, string>> = {};
  if (uploadedFiles.length === 0) {
    formErrors.files = 'At least one document is required';
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--color-text-primary)]">
          Submit a Health Insurance Claim
        </h1>
        <p className="mt-2 text-[var(--color-text-secondary)] max-w-2xl">
          Upload your medical documents and submit a claim. We&apos;ll verify your documents
          and let you know the decision.
        </p>
        {mounted && !isAuthenticated && (
          <div className="mt-3 bg-[var(--color-warning-50)] border border-[var(--color-warning-100)] rounded-lg p-3">
            <p className="text-sm text-[var(--color-warning-700)]">
              <a href="/login" className="underline font-semibold">
                Sign in
              </a>{' '}
              to submit claims tied to your account.
            </p>
          </div>
        )}
      </div>

      {/* Claim form */}
      <form
        onSubmit={handleSubmit}
        className="space-y-6 bg-[var(--color-surface-raised)] rounded-xl shadow-sm border border-[var(--color-border)] p-5 sm:p-6 lg:p-8"
      >
        {/* Member ID + Category */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label
              htmlFor="member_id"
              className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
            >
              Member ID
            </label>
            <input
              id="member_id"
              type="text"
              value={form.member_id}
              onChange={(e) => setForm({ ...form, member_id: e.target.value })}
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:border-[var(--color-primary-500)] transition-colors duration-150"
              required
              placeholder="e.g., EMP001"
            />
          </div>

          <CustomSelect
            label="Claim Category"
            options={CATEGORIES}
            value={form.claim_category}
            onChange={(v) => setForm({ ...form, claim_category: v })}
            helperText="The type of medical expense you're claiming"
            required
          />
        </div>

        {/* Amount + Date + YTD */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div>
            <label
              htmlFor="claimed_amount"
              className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
            >
              Claimed Amount (₹)
            </label>
            <input
              id="claimed_amount"
              type="number"
              value={form.claimed_amount}
              onChange={(e) => setForm({ ...form, claimed_amount: e.target.value })}
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:border-[var(--color-primary-500)] transition-colors duration-150"
              required
              min="1"
              placeholder="e.g., 1500"
            />
          </div>

          <div>
            <label
              htmlFor="treatment_date"
              className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
            >
              Treatment Date
            </label>
            <input
              id="treatment_date"
              type="date"
              value={form.treatment_date}
              onChange={(e) => setForm({ ...form, treatment_date: e.target.value })}
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text-primary)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:border-[var(--color-primary-500)] transition-colors duration-150"
              required
            />
          </div>

          <div>
            <label
              htmlFor="ytd_claims_amount"
              className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
            >
              Year-to-Date Claims (₹)
            </label>
            <input
              id="ytd_claims_amount"
              type="number"
              value={form.ytd_claims_amount}
              onChange={(e) => setForm({ ...form, ytd_claims_amount: e.target.value })}
              className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:border-[var(--color-primary-500)] transition-colors duration-150"
              min="0"
              placeholder="e.g., 5000"
            />
            <p className="mt-1 text-xs text-[var(--color-text-muted)]">
              Total claims submitted this policy year
            </p>
          </div>
        </div>

        {/* Hospital name */}
        <div>
          <label
            htmlFor="hospital_name"
            className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5"
          >
            Hospital / Clinic Name
            <span className="text-[var(--color-text-muted)] font-normal ml-1">(optional)</span>
          </label>
          <input
            id="hospital_name"
            type="text"
            value={form.hospital_name}
            onChange={(e) => setForm({ ...form, hospital_name: e.target.value })}
            placeholder="e.g., Apollo Hospitals"
            className="w-full min-h-touch rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-3.5 py-2.5 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] hover:border-[var(--color-border-hover)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:border-[var(--color-primary-500)] transition-colors duration-150"
          />
        </div>

        {/* File Uploader */}
        <CustomFileUploader
          label="Upload Documents"
          documentTypes={DOC_TYPES}
          files={uploadedFiles}
          onFilesChange={setUploadedFiles}
          helperText="Upload your prescription, hospital bill, lab reports, or any supporting documents. Accepted: PDF, JPG, PNG (max 10 MB each)."
          error={formErrors.files}
          required
        />

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-[var(--color-primary-500)] px-6 py-3.5 text-white font-semibold text-base
            hover:bg-[var(--color-primary-600)]
            active:bg-[var(--color-primary-700)]
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-all duration-150
            min-h-[48px] flex items-center justify-center gap-2
            shadow-sm hover:shadow-md"
        >
          {loading ? (
            <>
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing Your Claim…
            </>
          ) : (
            'Submit Claim'
          )}
        </button>
      </form>

      {/* Error state */}
      {error && (
        <div
          className="bg-[var(--color-danger-50)] border-2 border-[var(--color-danger-100)] rounded-xl p-5 sm:p-6"
          role="alert"
        >
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xl" aria-hidden="true">❌</span>
            <h2 className="text-lg font-bold text-[var(--color-danger-700)]">
              Submission Failed
            </h2>
          </div>
          <p className="text-sm text-[var(--color-danger-700)]">{error}</p>
        </div>
      )}

      {/* Success state */}
      {submittedClaimId && (
        <div
          className="bg-[var(--color-success-50)] border-2 border-[var(--color-success-100)] rounded-xl p-5 sm:p-6"
          role="status"
        >
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl" aria-hidden="true">✅</span>
            <h2 className="text-lg font-bold text-[var(--color-success-700)]">
              Claim Submitted Successfully
            </h2>
          </div>
          <p className="text-sm text-[var(--color-success-700)] mb-5">
            Your claim <strong>#{submittedClaimId}</strong> is now being processed.
            You can check its status anytime from your claims dashboard.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href={`/claims/${submittedClaimId}`}
              className="inline-flex items-center justify-center rounded-xl bg-[var(--color-success-500)] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[var(--color-success-700)] transition-colors duration-150 min-h-touch shadow-sm"
            >
              View Claim #{submittedClaimId} →
            </Link>
            <Link
              href="/claims"
              className="inline-flex items-center justify-center rounded-xl border-2 border-[var(--color-success-500)] px-5 py-2.5 text-sm font-semibold text-[var(--color-success-700)] hover:bg-[var(--color-success-100)] transition-colors duration-150 min-h-touch"
            >
              My Claims
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
