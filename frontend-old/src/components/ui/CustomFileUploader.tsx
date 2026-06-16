'use client';

import { useState, useRef, useCallback, useId } from 'react';

export interface UploadedFileEntry {
  file: File;
  document_type: string;
}

interface CustomFileUploaderProps {
  label: string;
  accept?: string;
  multiple?: boolean;
  maxFileSizeBytes?: number;
  documentTypes?: string[];
  files: UploadedFileEntry[];
  onFilesChange: (files: UploadedFileEntry[]) => void;
  helperText?: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

const DEFAULT_ACCEPT = '.pdf,.jpg,.jpeg,.png';
const DEFAULT_MAX_SIZE = 10 * 1024 * 1024; // 10 MB

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function CustomFileUploader({
  label,
  accept = DEFAULT_ACCEPT,
  multiple = true,
  maxFileSizeBytes = DEFAULT_MAX_SIZE,
  documentTypes = ['PRESCRIPTION', 'HOSPITAL_BILL', 'LAB_REPORT', 'PHARMACY_BILL', 'DENTAL_REPORT', 'DIAGNOSTIC_REPORT', 'DISCHARGE_SUMMARY'],
  files,
  onFilesChange,
  helperText,
  error,
  required = false,
  disabled = false,
}: CustomFileUploaderProps) {
  const id = useId();
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      const allowedExtensions = accept.split(',').map((ext) => ext.trim().replace('.', '').toLowerCase());
      const fileExt = file.name.split('.').pop()?.toLowerCase() || '';
      const isValidExt = allowedExtensions.some((allowed) => {
        if (allowed === 'jpg' || allowed === 'jpeg') return fileExt === 'jpg' || fileExt === 'jpeg';
        return fileExt === allowed;
      });
      if (!isValidExt) {
        return `"${file.name}" is not an accepted file type (${accept}).`;
      }
      if (file.size > maxFileSizeBytes) {
        return `"${file.name}" is too large (${formatBytes(file.size)}). Maximum is ${formatBytes(maxFileSizeBytes)}.`;
      }
      return null;
    },
    [accept, maxFileSizeBytes]
  );

  const addFiles = useCallback(
    (newFiles: FileList | File[]) => {
      setValidationError(null);
      const entries: UploadedFileEntry[] = [];
      for (const file of newFiles) {
        const err = validateFile(file);
        if (err) {
          setValidationError(err);
          return;
        }
        entries.push({ file, document_type: documentTypes[0] });
      }
      if (multiple) {
        onFilesChange([...files, ...entries]);
      } else {
        onFilesChange(entries.slice(0, 1));
      }
    },
    [files, multiple, onFilesChange, validateFile, documentTypes]
  );

  const removeFile = useCallback(
    (index: number) => {
      onFilesChange(files.filter((_, i) => i !== index));
    },
    [files, onFilesChange]
  );

  const updateDocumentType = useCallback(
    (index: number, docType: string) => {
      const updated = [...files];
      updated[index] = { ...updated[index], document_type: docType };
      onFilesChange(updated);
    },
    [files, onFilesChange]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files);
      // Reset so the same file can be re-selected
      e.target.value = '';
    }
  };

  const errorId = `${id}-error`;
  const helperId = `${id}-helper`;
  const describedBy = [error || validationError ? errorId : null, helperText ? helperId : null]
    .filter(Boolean)
    .join(' ') || undefined;

  const displayError = error || validationError;

  return (
    <div>
      <label className="block text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
        {label}
        {required && <span className="text-[var(--color-danger-500)] ml-0.5" aria-hidden="true">*</span>}
      </label>

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-describedby={describedBy}
        aria-invalid={!!displayError}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        className={`
          relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer
          transition-all duration-150 min-h-[120px] flex flex-col items-center justify-center gap-2
          ${disabled ? 'opacity-50 cursor-not-allowed bg-[var(--color-surface-muted)]' : ''}
          ${isDragOver
            ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] scale-[1.01]'
            : displayError
            ? 'border-[var(--color-danger-500)] bg-[var(--color-danger-50)]'
            : 'border-[var(--color-border)] hover:border-[var(--color-primary-300)] hover:bg-[var(--color-primary-50)]'
          }
          focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] focus-visible:ring-offset-1 outline-none
        `}
      >
        <svg
          className={`w-10 h-10 mb-1 transition-colors duration-150 ${
            isDragOver ? 'text-[var(--color-primary-500)]' : 'text-[var(--color-text-muted)]'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="text-sm text-[var(--color-text-secondary)]">
          <span className="font-semibold text-[var(--color-primary-600)]">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-[var(--color-text-muted)]">
          {accept.replace(/\./g, '').toUpperCase()} (max {formatBytes(maxFileSizeBytes)})
        </p>
        <input
          ref={inputRef}
          type="file"
          id={`${id}-input`}
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          disabled={disabled}
          className="sr-only"
          tabIndex={-1}
        />
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="mt-3 space-y-2" aria-label="Uploaded files">
          {files.map((entry, i) => (
            <li
              key={`${entry.file.name}-${i}`}
              className="flex flex-col sm:flex-row sm:items-center gap-2 bg-[var(--color-surface-muted)] rounded-lg p-3 border border-[var(--color-border)]"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                  {entry.file.name}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {formatBytes(entry.file.size)}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <select
                  value={entry.document_type}
                  onChange={(e) => updateDocumentType(i, e.target.value)}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-raised)] px-2.5 py-1.5 text-xs text-[var(--color-text-primary)] focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)] min-h-touch"
                  aria-label={`Document type for ${entry.file.name}`}
                >
                  {documentTypes.map((dt) => (
                    <option key={dt} value={dt}>
                      {dt.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="p-1.5 rounded-lg text-[var(--color-danger-500)] hover:bg-[var(--color-danger-50)] transition-colors duration-150 min-w-touch min-h-touch flex items-center justify-center"
                  aria-label={`Remove ${entry.file.name}`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {helperText && !displayError && (
        <p id={helperId} className="mt-1.5 text-xs text-[var(--color-text-secondary)]">
          {helperText}
        </p>
      )}
      {displayError && (
        <p id={errorId} className="mt-1.5 text-xs text-[var(--color-danger-600)]" role="alert">
          {displayError}
        </p>
      )}
    </div>
  );
}
