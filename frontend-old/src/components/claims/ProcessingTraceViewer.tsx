import { ProcessingStep } from '@/types';

interface ProcessingTraceViewerProps {
  steps: ProcessingStep[];
}

const STATUS_COLORS: Record<string, string> = {
  COMPLETED: 'bg-green-500',
  FAILED: 'bg-red-500',
  SKIPPED: 'bg-gray-400',
  STARTED: 'bg-yellow-500',
};

export default function ProcessingTraceViewer({ steps }: ProcessingTraceViewerProps) {
  if (!steps || steps.length === 0) return null;

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-2">Processing Trace</h3>
      <div className="space-y-2">
        {steps.map((step) => (
          <details key={step.step_index} className="border rounded-lg">
            <summary className="px-4 py-3 cursor-pointer hover:bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span
                  className={`w-2 h-2 rounded-full ${STATUS_COLORS[step.status] || 'bg-gray-400'}`}
                />
                <span className="font-medium text-sm">{step.step_name}</span>
                <span className="text-xs text-gray-500">({step.agent_name})</span>
              </div>
              <span className="text-xs text-gray-400">{step.status}</span>
            </summary>
            <div className="px-4 pb-3 text-sm text-gray-700 space-y-2">
              {step.error_message && (
                <div className="text-red-600">Error: {step.error_message}</div>
              )}
              {step.confidence_score !== undefined && step.confidence_score !== null && (
                <p>Confidence: {(step.confidence_score * 100).toFixed(0)}%</p>
              )}
              {step.duration_ms && <p>Duration: {step.duration_ms}ms</p>}
              {step.checks_performed && step.checks_performed.length > 0 && (
                <div className="mt-1">
                  <p className="font-medium text-xs text-gray-500 mb-1">Checks:</p>
                  {step.checks_performed.map((c, ci) => (
                    <div
                      key={ci}
                      className={`text-xs px-2 py-1 rounded mb-1 ${
                        c.passed ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                      }`}
                    >
                      {c.passed ? '✓' : '✗'} {c.check}: {c.reason}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
