import { useMemo } from 'react';

interface HandRangeProps {
  position: string;
  stackBb: number;
  isPushFold: boolean;
  heroHand: string | null;
}

// All possible hand combinations in the 13x13 matrix
const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];

// Default opening ranges by position (simplified)
const OPENING_RANGES: Record<string, Set<string>> = {
  UTG: new Set([
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88',
    'AKs', 'AQs', 'AJs', 'ATs', 'KQs',
    'AKo', 'AQo',
  ]),
  MP: new Set([
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77',
    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'KQs', 'KJs', 'QJs',
    'AKo', 'AQo', 'AJo',
  ]),
  CO: new Set([
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66',
    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s',
    'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs',
    'AKo', 'AQo', 'AJo', 'ATo', 'KQo', 'KJo',
  ]),
  BTN: new Set([
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44',
    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
    'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'QJs', 'QTs', 'Q9s', 'JTs', 'J9s',
    'T9s', 'T8s', '98s', '97s', '87s', '76s', '65s', '54s',
    'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'KQo', 'KJo', 'KTo', 'QJo', 'QTo', 'JTo',
  ]),
  SB: new Set([
    'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55',
    'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s',
    'KQs', 'KJs', 'KTs', 'K9s', 'QJs', 'QTs', 'JTs', 'J9s', 'T9s', '98s', '87s', '76s',
    'AKo', 'AQo', 'AJo', 'ATo', 'KQo', 'KJo', 'QJo',
  ]),
  BB: new Set([
    'AA', 'KK', 'QQ', 'JJ', 'TT',
    'AKs', 'AQs', 'AJs',
    'AKo',
  ]),
};

// Push ranges for short stacks (simplified)
const PUSH_RANGES: Record<number, Record<string, Set<string>>> = {
  5: {
    BTN: new Set([
      'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
      'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
      'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s', 'K6s', 'K5s',
      'QJs', 'QTs', 'Q9s', 'Q8s', 'JTs', 'J9s', 'J8s', 'T9s', 'T8s', '98s', '87s', '76s', '65s', '54s',
      'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o', 'A4o',
      'KQo', 'KJo', 'KTo', 'K9o', 'QJo', 'QTo', 'JTo',
    ]),
    SB: new Set([
      'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '44', '33', '22',
      'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
      'KQs', 'KJs', 'KTs', 'K9s', 'K8s', 'K7s',
      'QJs', 'QTs', 'Q9s', 'JTs', 'J9s', 'T9s', '98s', '87s', '76s', '65s',
      'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'A8o', 'A7o', 'A6o', 'A5o',
      'KQo', 'KJo', 'KTo', 'QJo', 'QTo',
    ]),
  },
  10: {
    BTN: new Set([
      'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55',
      'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s',
      'KQs', 'KJs', 'KTs', 'K9s', 'QJs', 'QTs', 'JTs', 'T9s', '98s', '87s',
      'AKo', 'AQo', 'AJo', 'ATo', 'A9o', 'KQo', 'KJo',
    ]),
    SB: new Set([
      'AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66',
      'AKs', 'AQs', 'AJs', 'ATs', 'A9s', 'A8s', 'A7s', 'A6s', 'A5s',
      'KQs', 'KJs', 'KTs', 'QJs', 'QTs', 'JTs', '98s',
      'AKo', 'AQo', 'AJo', 'ATo', 'KQo',
    ]),
  },
};

export function HandRange({ position, stackBb, isPushFold, heroHand }: HandRangeProps) {
  // Get the appropriate range for position and stack
  const activeRange = useMemo(() => {
    if (isPushFold && stackBb <= 10) {
      const stackKey = stackBb <= 5 ? 5 : 10;
      return PUSH_RANGES[stackKey]?.[position] || new Set();
    }
    return OPENING_RANGES[position] || new Set();
  }, [position, stackBb, isPushFold]);

  // Generate the 13x13 matrix
  const matrix = useMemo(() => {
    const cells: Array<{ hand: string; inRange: boolean; isHero: boolean }> = [];
    
    for (let row = 0; row < 13; row++) {
      for (let col = 0; col < 13; col++) {
        const r1 = RANKS[row];
        const r2 = RANKS[col];
        
        let hand: string;
        if (row === col) {
          hand = `${r1}${r2}`; // Pocket pair
        } else if (row < col) {
          hand = `${r1}${r2}s`; // Suited (above diagonal)
        } else {
          hand = `${r2}${r1}o`; // Offsuit (below diagonal)
        }
        
        const inRange = activeRange.has(hand);
        const isHero = heroHand === hand;
        
        cells.push({ hand, inRange, isHero });
      }
    }
    
    return cells;
  }, [activeRange, heroHand]);

  const rangePercent = useMemo(() => {
    // Calculate approximate range percentage
    // Pairs = 6 combos each (78 total)
    // Suited = 4 combos each
    // Offsuit = 12 combos each
    let combos = 0;
    activeRange.forEach(hand => {
      if (hand.length === 2) {
        combos += 6; // Pair
      } else if (hand.endsWith('s')) {
        combos += 4; // Suited
      } else {
        combos += 12; // Offsuit
      }
    });
    return ((combos / 1326) * 100).toFixed(1);
  }, [activeRange]);

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          {isPushFold ? 'Push Range' : 'Opening Range'}
        </h3>
        <span className="text-sm text-gray-400">
          {rangePercent}% of hands
        </span>
      </div>

      {/* Matrix Grid */}
      <div className="grid grid-cols-13 gap-0.5 text-center">
        {matrix.map((cell, index) => (
          <div
            key={index}
            className={`
              range-cell
              ${cell.inRange ? 'raise' : 'fold'}
              ${cell.isHero ? 'ring-2 ring-amber-400 animate-glow' : ''}
            `}
            title={cell.hand}
          >
            {/* Show abbreviated hand name for readability */}
            <span className="text-[8px] leading-none">
              {cell.hand.replace('10', 'T')}
            </span>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-4 text-xs text-gray-400">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500/80 rounded" />
          <span>Raise</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-700/50 rounded" />
          <span>Fold</span>
        </div>
        {heroHand && (
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 bg-amber-400 rounded ring-2 ring-amber-400" />
            <span>Your Hand</span>
          </div>
        )}
      </div>
    </div>
  );
}
