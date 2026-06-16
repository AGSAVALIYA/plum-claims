'use client';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

const STATUS_CONFIG: Record<string, { bg: string; text: string; icon: string; label: string }> = {
  SUBMITTED: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    icon: '📥',
    label: 'Submitted',
  },
  VALIDATING: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    icon: '🔍',
    label: 'Validating',
  },
  PROCESSING: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    icon: '⚙️',
    label: 'Processing',
  },
  DECIDED: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    icon: '✅',
    label: 'Completed',
  },
  DOCUMENT_ERROR: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    icon: '📄',
    label: 'Document Issue',
  },
  ERROR: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    icon: '❌',
    label: 'Error',
  },
  CLOSED: {
    bg: 'bg-gray-100',
    text: 'text-gray-700',
    icon: '🔒',
    label: 'Closed',
  },
};

const FALLBACK = {
  bg: 'bg-gray-100',
  text: 'text-gray-700',
  icon: '•',
  label: 'Unknown',
};

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status] || FALLBACK;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${config.bg} ${config.text} ${className}`}
      role="status"
      aria-label={`Status: ${config.label}`}
    >
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}
