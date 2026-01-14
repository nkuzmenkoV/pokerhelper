import type { Recommendation } from '../types/poker';

interface ActionPanelProps {
  recommendation: Recommendation | null;
}

const actionConfig: Record<string, { label: string; icon: string; gradient: string; glow: string }> = {
  fold: { 
    label: 'FOLD', 
    icon: '✕', 
    gradient: 'from-red-600 to-red-700',
    glow: 'shadow-red-500/30'
  },
  check: { 
    label: 'CHECK', 
    icon: '✓', 
    gradient: 'from-gray-600 to-gray-700',
    glow: 'shadow-gray-500/20'
  },
  call: { 
    label: 'CALL', 
    icon: '📞', 
    gradient: 'from-blue-600 to-blue-700',
    glow: 'shadow-blue-500/30'
  },
  bet: { 
    label: 'BET', 
    icon: '💰', 
    gradient: 'from-green-600 to-green-700',
    glow: 'shadow-green-500/30'
  },
  raise: { 
    label: 'RAISE', 
    icon: '📈', 
    gradient: 'from-green-600 to-emerald-700',
    glow: 'shadow-green-500/30'
  },
  allin: { 
    label: 'ALL-IN', 
    icon: '🔥', 
    gradient: 'from-amber-500 via-orange-500 to-red-500',
    glow: 'shadow-amber-500/40'
  },
};

function CardDisplay({ hand }: { hand: string }) {
  // Parse hand like "AKs" or "QQ"
  if (!hand || hand.length < 2) return null;
  
  const rank1 = hand[0];
  const rank2 = hand[1];
  const suited = hand.endsWith('s');
  const offsuit = hand.endsWith('o');
  
  // Display cards with styling
  const isPair = rank1 === rank2;
  
  return (
    <div className="flex items-center gap-1">
      <div className="card card-large">
        <span>{rank1}</span>
        <span className="text-sm ml-0.5">{suited ? '♠' : '♥'}</span>
      </div>
      <div className={`card card-large ${!isPair && suited ? '' : 'red'}`}>
        <span>{rank2}</span>
        <span className="text-sm ml-0.5">{isPair ? '♦' : suited ? '♠' : offsuit ? '♦' : '♠'}</span>
      </div>
      {suited && <span className="text-xs text-blue-400 ml-1">suited</span>}
      {offsuit && <span className="text-xs text-gray-500 ml-1">offsuit</span>}
      {isPair && <span className="text-xs text-purple-400 ml-1">pair</span>}
    </div>
  );
}

export function ActionPanel({ recommendation }: ActionPanelProps) {
  if (!recommendation) {
    return (
      <div className="glass-elevated rounded-2xl p-6">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
          Recommendation
        </h2>
        <div className="text-center py-10">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <p className="text-gray-400 font-medium">Waiting for analysis</p>
          <p className="text-sm text-gray-600 mt-1">Capture screen and click Analyze</p>
        </div>
      </div>
    );
  }

  const { primary, alternatives, hand, position, stackBb, isPushFold, rangeStrength } = recommendation;
  const config = actionConfig[primary.action] || actionConfig.check;

  return (
    <div className="glass-elevated rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
          Recommendation
        </h2>
        {isPushFold && (
          <span className="px-2.5 py-1 bg-amber-500/20 text-amber-400 text-xs font-medium rounded-full border border-amber-500/30">
            Push/Fold Mode
          </span>
        )}
      </div>

      <div className="p-6">
        {/* Hero Hand */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="text-xs text-gray-500 mb-1">Your Hand</div>
            <CardDisplay hand={hand} />
          </div>
          <div className="text-right">
            <div className={`position-badge ${position?.toLowerCase() || ''} mb-1`}>
              {position}
            </div>
            <div className="text-sm text-gray-400 font-mono">{stackBb?.toFixed(1)} BB</div>
          </div>
        </div>

        {/* Primary Action Button */}
        <button 
          className={`w-full py-4 rounded-xl bg-gradient-to-r ${config.gradient} transform transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg ${config.glow} mb-4`}
        >
          <div className="flex items-center justify-center gap-3">
            <span className="text-2xl">{config.icon}</span>
            <div>
              <div className="text-2xl font-bold text-white tracking-wide">
                {config.label}
                {primary.size && primary.action !== 'allin' && (
                  <span className="text-lg ml-2 opacity-80">{primary.size}x</span>
                )}
              </div>
              <div className="text-xs text-white/70">
                {(primary.frequency * 100).toFixed(0)}% of the time
              </div>
            </div>
          </div>
        </button>

        {/* Reason */}
        <div className="px-4 py-3 bg-black/30 rounded-lg text-sm text-gray-300 mb-6">
          <span className="text-green-500 mr-2">→</span>
          {primary.reason}
        </div>

        {/* Range Strength */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-gray-500 uppercase tracking-wide">Hand Strength</span>
            <span className="text-sm font-mono font-semibold text-white">
              {(rangeStrength * 100).toFixed(0)}%
            </span>
          </div>
          <div className="progress-bar">
            <div
              className={`progress-bar-fill ${rangeStrength > 0.7 ? 'green' : rangeStrength > 0.4 ? 'gold' : 'red'}`}
              style={{ width: `${rangeStrength * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-gray-600 mt-1">
            <span>Weak</span>
            <span>Medium</span>
            <span>Strong</span>
          </div>
        </div>

        {/* Alternative Actions */}
        {alternatives && alternatives.length > 0 && (
          <div>
            <h4 className="text-xs text-gray-500 uppercase tracking-wide mb-2">Alternatives</h4>
            <div className="space-y-2">
              {alternatives.map((alt, index) => {
                const altConfig = actionConfig[alt.action] || actionConfig.check;
                return (
                  <div
                    key={index}
                    className="flex items-center justify-between px-4 py-2.5 bg-black/20 rounded-lg border border-white/5 hover:border-white/10 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{altConfig.icon}</span>
                      <span className="text-sm text-gray-300 font-medium">
                        {altConfig.label}
                        {alt.size && ` ${alt.size}x`}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 font-mono">
                      {((alt.frequency || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
