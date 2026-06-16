'use client';

import { useState } from 'react';
import { getDocumentViewUrl } from '@/lib/api';
import StatusBadge from '@/components/ui/StatusBadge';

interface DocumentListProps {
  documents: Array<{
    document_id: number;
    file_name: string;
    document_type?: string;
    verification_status: string;
    quality_score?: number;
    error_message?: string;
  }>;
}

function isImageFile(fileName: string): boolean {
  const ext = fileName.toLowerCase().split('.').pop();
  return ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp'].includes(ext || '');
}

function isPdfFile(fileName: string): boolean {
  return fileName.toLowerCase().endsWith('.pdf');
}

export default function DocumentList({ documents }: DocumentListProps) {
  const [expandedDocId, setExpandedDocId] = useState<number | null>(null);

  if (!documents || documents.length === 0) return null;

  const toggleExpand = (docId: number) => {
    setExpandedDocId((prev) => (prev === docId ? null : docId));
  };

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-3">
        Uploaded Documents
      </h3>
      <div className="space-y-3">
        {documents.map((doc) => {
          const isImage = isImageFile(doc.file_name);
          const isPdf = isPdfFile(doc.file_name);
          const canPreview = isImage || isPdf;
          const isExpanded = expandedDocId === doc.document_id;
          const viewUrl = getDocumentViewUrl(doc.document_id);

          return (
            <div
              key={doc.document_id}
              className="border rounded-lg overflow-hidden bg-white"
            >
              {/* Document header row */}
              <div className="flex items-center justify-between p-3">
                <div className="flex items-center gap-3 min-w-0">
                  {/* Thumbnail for images */}
                  {isImage && (
                    <img
                      src={viewUrl}
                      alt={doc.file_name}
                      className="w-10 h-10 rounded-md object-cover border shrink-0"
                      loading="lazy"
                    />
                  )}
                  {isPdf && (
                    <div className="w-10 h-10 rounded-md border bg-red-50 flex items-center justify-center shrink-0">
                      <span className="text-lg">📄</span>
                    </div>
                  )}
                  {!canPreview && (
                    <div className="w-10 h-10 rounded-md border bg-gray-50 flex items-center justify-center shrink-0">
                      <span className="text-lg">📎</span>
                    </div>
                  )}

                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate" title={doc.file_name}>
                      {doc.file_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {doc.document_type && doc.document_type !== 'UNKNOWN'
                        ? doc.document_type.replace(/_/g, ' ')
                        : (() => {
                            const ext = doc.file_name.split('.').pop()?.toUpperCase();
                            return ext ? `${ext} Document` : 'Document';
                          })()}
                      {doc.quality_score != null && (
                        <span className="ml-2 text-gray-400">
                          Quality: {(doc.quality_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </p>
                    {doc.error_message && (
                      <p className="text-xs text-red-600 mt-0.5 truncate" title={doc.error_message}>
                        ⚠ {doc.error_message}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <StatusBadge status={doc.verification_status} />
                  {canPreview && (
                    <button
                      onClick={() => toggleExpand(doc.document_id)}
                      className="text-xs text-[var(--color-primary-600)] hover:text-[var(--color-primary-800)] font-medium transition-colors"
                      aria-expanded={isExpanded}
                      aria-label={isExpanded ? 'Hide preview' : 'Show preview'}
                    >
                      {isExpanded ? 'Hide' : 'View'}
                    </button>
                  )}
                </div>
              </div>

              {/* Expanded preview */}
              {isExpanded && canPreview && (
                <div className="border-t bg-gray-50 p-3">
                  {isImage && (
                    <a href={viewUrl} target="_blank" rel="noopener noreferrer">
                      <img
                        src={viewUrl}
                        alt={doc.file_name}
                        className="max-w-full max-h-96 rounded-md border object-contain mx-auto"
                        loading="lazy"
                      />
                    </a>
                  )}
                  {isPdf && (
                    <div className="space-y-2">
                      <iframe
                        src={viewUrl}
                        title={doc.file_name}
                        className="w-full h-96 rounded-md border"
                      />
                      <a
                        href={viewUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block text-xs text-[var(--color-primary-600)] hover:underline"
                      >
                        Open PDF in new tab
                      </a>
                    </div>
                  )}
                  <p className="text-xs text-gray-400 mt-2">
                    Click the image/PDF to open full-size in a new tab.
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
