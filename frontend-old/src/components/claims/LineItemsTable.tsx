import { LineItemResult } from '@/types';

interface LineItemsTableProps {
  lineItems: LineItemResult[];
}

export default function LineItemsTable({ lineItems }: LineItemsTableProps) {
  if (!lineItems || lineItems.length === 0) return null;

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-2">Line Items</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="py-2">Description</th>
            <th className="py-2 text-right">Amount</th>
            <th className="py-2 text-right">Approved</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {lineItems.map((li, i) => (
            <tr key={i} className="border-b last:border-0">
              <td className="py-2">{li.description}</td>
              <td className="py-2 text-right">₹{li.amount.toLocaleString()}</td>
              <td className="py-2 text-right">₹{(li.approved_amount ?? 0).toLocaleString()}</td>
              <td className="py-2">
                {li.is_covered === false ? (
                  <span className="text-xs text-red-600" title={li.rejection_reason || ''}>
                    ✗ {li.rejection_reason || 'Excluded'}
                  </span>
                ) : (
                  <span className="text-xs text-green-600">✓ Covered</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
