interface MetricCardProps {
  label: string;
  value: string | number;
  valueClassName?: string;
}

export default function MetricCard({ label, value, valueClassName = '' }: MetricCardProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-lg font-bold ${valueClassName}`}>{value}</p>
    </div>
  );
}
