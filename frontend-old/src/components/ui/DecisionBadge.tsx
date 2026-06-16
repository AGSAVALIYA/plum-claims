import { Decision } from '@/types';

const DECISION_STYLES: Record<string, string> = {
  APPROVED: 'bg-green-100 text-green-800',
  PARTIAL: 'bg-yellow-100 text-yellow-800',
  REJECTED: 'bg-red-100 text-red-800',
  MANUAL_REVIEW: 'bg-orange-100 text-orange-800',
};

interface DecisionBadgeProps {
  decision: Decision | string | null | undefined;
  className?: string;
}

export default function DecisionBadge({ decision, className = '' }: DecisionBadgeProps) {
  const label = decision || 'PENDING';
  const style = DECISION_STYLES[label] || 'bg-gray-100 text-gray-600';

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${style} ${className}`}>
      {label.replace('_', ' ')}
    </span>
  );
}
