import type { Recommendation } from '../types/poker';

interface ActionPanelProps {
  recommendation: Recommendation | null;
}

const actionStyles: Record<string, string> = {
  fold: 'action-fold',
  check: 'action-check',
  call: 'action-call',
  bet: 'action-raise',
  raise: 'action-raise',
  allin: 'action-allin',
};

const actionLabels: Record<string, string> = {
  fold: 'FOLD',
  check: 'CHECK',
  call: 'CALL',
  bet: 'BET',
  raise: 'RAISE',
  allin: 'ALL-IN',
};

export function ActionPanel({ recommendation }: ActionPanelProps) {
  if (!recommendation) {
    return (
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Recommendation</h2>
        <div className="text-center py-8 text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <p>Waiting for analysis...</p>
          <p className="text-sm mt-1 opacity-70">Start screen capture and click Analyze</p>
        </div>
      </div>
    );
  }

  const { primary, alternatives, hand, position, stackBb, isPushFold, rangeStrength } = recommendation;

  return (
    <div className="glass rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Recommendation</h2>
        {isPushFold && (
          <span className="px-2 py-1 bg-amber-500/20 text-amber-400 text-xs rounded-full">
            Push/Fold
          </span>
        )}
      </div>

      {/* Hero Hand Display */}
      <div className="mb-6 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg">
          <span className="text-gray-400 text-sm">Hand:</span>
          <span className="text-2xl font-bold font-mono text-white">{hand}</span>
        </div>
        <div className="flex justify-center gap-4 mt-2 text-sm text-gray-400">
          <span>{position}</span>
          <span>•</span>
          <span>{stackBb.toFixed(1)} BB</span>
        </div>
      </div>

      {/* Primary Action */}
      <div className={`${actionStyles[primary.action]} rounded-xl p-4 text-center mb-4`}>
        <div className="text-2xl font-bold text-white mb-1">
          {actionLabels[primary.action]}
          {primary.size && (
            <span className="ml-2 text-lg opacity-90">
              {primary.action === 'allin' ? '' : `${primary.size}x`}
            </span>
          )}
        </div>
        <div className="text-sm text-white/80">
          {(primary.frequency * 100).toFixed(0)}% frequency
        </div>
      </div>

      {/* Reason */}
      <div className="text-sm text-gray-300 mb-4 p-3 bg-gray-800/50 rounded-lg">
        {primary.reason}
      </div>

      {/* Range Strength Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Range Strength</span>
          <span>{(rangeStrength * 100).toFixed(0)}%</span>
        </div>
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-red-500 via-amber-500 to-green-500"
            style={{ width: `${rangeStrength * 100}%` }}
          />
        </div>
      </div>

      {/* Alternative Actions */}
      {alternatives.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-gray-400 uppercase mb-2">Alternatives</h4>
          <div className="space-y-2">
            {alternatives.map((alt, index) => (
              <div
                key={index}
                className="flex items-center justify-between px-3 py-2 bg-gray-800/50 rounded-lg text-sm"
              >
                <span className="text-gray-300">
                  {actionLabels[alt.action]}
                  {alt.size && ` ${alt.size}x`}
                </span>
                <span className="text-gray-500">
                  {(alt.frequency * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
