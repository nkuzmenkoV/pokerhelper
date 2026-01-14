import { useState, useEffect } from 'react';

interface EquityDisplayProps {
  heroCards: string[];
  boardCards: string[];
  isCalculating?: boolean;
}

interface EquityResult {
  equity: number;
  winPct: number;
  tiePct: number;
  losePct: number;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Card suit symbols for display
const SUIT_DISPLAY: Record<string, { symbol: string; color: string }> = {
  s: { symbol: '♠', color: 'text-gray-300' },
  h: { symbol: '♥', color: 'text-red-500' },
  d: { symbol: '♦', color: 'text-blue-400' },
  c: { symbol: '♣', color: 'text-green-400' },
};

function CardBadge({ card }: { card: string }) {
  if (card.length < 2) return null;
  
  const rank = card[0];
  const suit = card[1];
  const suitInfo = SUIT_DISPLAY[suit] || { symbol: suit, color: 'text-white' };

  return (
    <span className={`inline-flex items-center ${suitInfo.color}`}>
      {rank}{suitInfo.symbol}
    </span>
  );
}

export function EquityDisplay({ heroCards, boardCards, isCalculating }: EquityDisplayProps) {
  const [equity, setEquity] = useState<EquityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Calculate equity when cards change
  useEffect(() => {
    if (heroCards.length !== 2) {
      setEquity(null);
      return;
    }

    const calculateEquity = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_URL}/api/equity/calculate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            hero_cards: heroCards,
            board: boardCards,
            num_villains: 1,
            num_simulations: 5000,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to calculate equity');
        }

        const data = await response.json();
        setEquity({
          equity: data.equity * 100,
          winPct: data.win_pct,
          tiePct: data.tie_pct,
          losePct: data.lose_pct,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error calculating equity');
      } finally {
        setLoading(false);
      }
    };

    calculateEquity();
  }, [heroCards.join(','), boardCards.join(',')]);

  // Don't show if no hero cards
  if (heroCards.length !== 2) {
    return null;
  }

  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-lg font-semibold text-white mb-3">Equity Calculator</h3>

      {/* Hero Hand */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">Hand:</span>
          <div className="flex gap-1 text-xl font-bold font-mono">
            {heroCards.map((card, i) => (
              <CardBadge key={i} card={card} />
            ))}
          </div>
        </div>

        {boardCards.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Board:</span>
            <div className="flex gap-1 text-lg font-mono">
              {boardCards.map((card, i) => (
                <CardBadge key={i} card={card} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Equity Display */}
      {loading || isCalculating ? (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin h-6 w-6 border-2 border-poker-green-500 border-t-transparent rounded-full" />
          <span className="ml-2 text-gray-400">Calculating...</span>
        </div>
      ) : error ? (
        <div className="text-red-400 text-sm py-2">{error}</div>
      ) : equity ? (
        <div className="space-y-3">
          {/* Main Equity */}
          <div className="text-center">
            <div className="text-4xl font-bold text-white mb-1">
              {equity.equity.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-400">vs Random Hand</div>
          </div>

          {/* Progress Bar */}
          <div className="h-4 rounded-full overflow-hidden flex">
            <div
              className="bg-green-500 transition-all duration-300"
              style={{ width: `${equity.winPct}%` }}
              title={`Win: ${equity.winPct.toFixed(1)}%`}
            />
            <div
              className="bg-yellow-500 transition-all duration-300"
              style={{ width: `${equity.tiePct}%` }}
              title={`Tie: ${equity.tiePct.toFixed(1)}%`}
            />
            <div
              className="bg-red-500 transition-all duration-300"
              style={{ width: `${equity.losePct}%` }}
              title={`Lose: ${equity.losePct.toFixed(1)}%`}
            />
          </div>

          {/* Breakdown */}
          <div className="flex justify-between text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-500 rounded" />
              <span className="text-gray-300">Win {equity.winPct.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-yellow-500 rounded" />
              <span className="text-gray-300">Tie {equity.tiePct.toFixed(1)}%</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-500 rounded" />
              <span className="text-gray-300">Lose {equity.losePct.toFixed(1)}%</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-gray-500 text-center py-4">
          Enter hero cards to calculate equity
        </div>
      )}
    </div>
  );
}

// Compact equity badge for inline display
export function EquityBadge({ equity }: { equity: number }) {
  const bgColor = equity >= 60 ? 'bg-green-500' : equity >= 45 ? 'bg-yellow-500' : 'bg-red-500';
  
  return (
    <span className={`px-2 py-0.5 rounded ${bgColor} text-white text-xs font-bold`}>
      {equity.toFixed(0)}%
    </span>
  );
}
