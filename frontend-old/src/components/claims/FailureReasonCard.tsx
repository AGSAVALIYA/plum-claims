'use client';

import type { DocumentError } from '@/types';

interface DocumentInfo {
  document_id: number;
  file_name: string;
  document_type?: string;
  verification_status: string;
  quality_score?: number;
  error_message?: string;
}

interface FailureReasonCardProps {
  documentErrors?: DocumentError[] | null;
  decisionReason?: string | null;
  documents?: DocumentInfo[] | null;
  className?: string;
}

/**
 * Maps technical error types to human-readable, non-technical messages.
 * These are shown to normal users who don't need to know internal error codes.
 */
const ERROR_TYPE_MESSAGES: Record<string, { heading: string; icon: string }> = {
  MISSING_REQUIRED: {
    heading: 'A required document was missing',
    icon: '📄',
  },
  MISSING_DOCUMENT: {
    heading: 'A required document was not uploaded',
    icon: '📄',
  },
  WRONG_TYPE: {
    heading: 'The uploaded document does not match the required type',
    icon: '🔄',
  },
  WRONG_DOC_TYPE: {
    heading: 'The uploaded document does not match the required type',
    icon: '🔄',
  },
  INVALID_DOC_TYPE: {
    heading: "We couldn't identify the type of document",
    icon: '❓',
  },
  UNREADABLE: {
    heading: 'The document was blurry or unreadable',
    icon: '👁️',
  },
  PATIENT_MISMATCH: {
    heading: "The name on the document doesn't match your records",
    icon: '👤',
  },
  PATIENT_NAME_MISMATCH: {
    heading: "The name on the document doesn't match your records",
    icon: '👤',
  },
  EXPIRED_DOCUMENT: {
    heading: 'The document has expired',
    icon: '📅',
  },
  DUPLICATE_DOCUMENT: {
    heading: 'The same document was uploaded more than once',
    icon: '📋',
  },
  CORRUPTED_FILE: {
    heading: 'The file appears to be damaged or corrupted',
    icon: '💾',
  },
  EXTRACTION_FAILED: {
    heading: 'We had trouble reading the information from your document',
    icon: '🔍',
  },
  VERIFICATION_FAILED: {
    heading: 'Your document could not be verified',
    icon: '⚠️',
  },
};

const FALLBACK_FAILURE = {
  heading: 'There was an issue with your documents',
  icon: '⚠️',
};

/**
 * Build synthetic document errors from the documents array when the backend
 * didn't provide explicit document_errors. This handles the edge case where
 * document failures are stored on individual document records but not
 * aggregated at the claim level.
 */
function deriveErrorsFromDocuments(documents: DocumentInfo[]): DocumentError[] {
  const errors: DocumentError[] = [];
  for (const doc of documents) {
    if (doc.error_message) {
      errors.push({
        error_type: 'VERIFICATION_FAILED',
        document_id: doc.document_id,
        file_name: doc.file_name,
        message: doc.error_message,
      });
    } else if (doc.verification_status === 'FAILED') {
      errors.push({
        error_type: 'VERIFICATION_FAILED',
        document_id: doc.document_id,
        file_name: doc.file_name,
        message: `"${doc.file_name}" could not be verified. Please check and re-upload.`,
      });
    } else if (doc.verification_status === 'UNREADABLE') {
      errors.push({
        error_type: 'UNREADABLE',
        document_id: doc.document_id,
        file_name: doc.file_name,
        message: `"${doc.file_name}" is blurry or unreadable. Please upload a clearer version.`,
      });
    } else if (doc.verification_status === 'WRONG_TYPE') {
      errors.push({
        error_type: 'WRONG_TYPE',
        document_id: doc.document_id,
        file_name: doc.file_name,
        message: `"${doc.file_name}" is not the correct type of document for this claim.`,
      });
    } else if (doc.verification_status === 'PATIENT_MISMATCH') {
      errors.push({
        error_type: 'PATIENT_MISMATCH',
        document_id: doc.document_id,
        file_name: doc.file_name,
        message: `The name on "${doc.file_name}" doesn't match the claim member.`,
      });
    }
  }
  return errors;
}

export default function FailureReasonCard({
  documentErrors,
  decisionReason,
  documents,
  className = '',
}: FailureReasonCardProps) {
  // Use explicit document_errors if available; otherwise derive from document records
  const effectiveErrors: DocumentError[] = (() => {
    if (documentErrors && documentErrors.length > 0) return documentErrors;
    if (documents && documents.length > 0) return deriveErrorsFromDocuments(documents);
    return [];
  })();

  const hasErrors = effectiveErrors.length > 0;
  const hasReason = !!decisionReason;

  if (!hasErrors && !hasReason) return null;

  return (
    <div
      className={`rounded-xl border-2 border-[var(--color-danger-100)] bg-[var(--color-danger-50)] p-5 sm:p-6 ${className}`}
      role="alert"
      aria-live="polite"
      aria-label="Claim could not be processed"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl" aria-hidden="true">⚠️</span>
        <h2 className="text-lg font-bold text-[var(--color-danger-700)]">
          Claim could not be processed
        </h2>
      </div>

      {/* Document errors with non-technical explanations */}
      {hasErrors && (
        <div className="space-y-3 mb-4">
          <p className="text-sm font-semibold text-[var(--color-danger-700)]">
            What went wrong with your documents:
          </p>
          <ul className="space-y-2.5">
            {effectiveErrors.map((de, i) => {
              const mapping = ERROR_TYPE_MESSAGES[de.error_type] || FALLBACK_FAILURE;
              return (
                <li
                  key={i}
                  className="bg-[var(--color-surface-raised)] rounded-lg border border-[var(--color-danger-100)] p-3.5"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-lg shrink-0 mt-0.5" aria-hidden="true">
                      {mapping.icon}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-[var(--color-text-primary)]">
                        {mapping.heading}
                      </p>
                      {de.file_name && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                          File: {de.file_name}
                        </p>
                      )}
                      <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                        {de.message}
                      </p>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Decision reason — simplified */}
      {hasReason && (
        <div className="bg-[var(--color-surface-raised)] rounded-lg border border-[var(--color-warning-100)] p-3.5">
          <div className="flex items-start gap-3">
            <span className="text-lg shrink-0 mt-0.5" aria-hidden="true">ℹ️</span>
            <div>
              <p className="text-sm font-semibold text-[var(--color-text-primary)]">
                Why this happened
              </p>
              <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                {decisionReason}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action hint */}
      <p className="mt-4 text-sm text-[var(--color-text-secondary)]">
        You can upload new or corrected documents below to try again.
      </p>
    </div>
  );
}
