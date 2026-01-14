import { useMemo } from 'react';

interface RangeVisualizerProps {
  range: string[];
  heroHand?: string;
  title?: string;
  showLabels?: boolean;
  compact?: boolean;
}

// All 13 ranks in order
const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];

// Generate all 169 unique starting hands in matrix format
function generateHandMatrix(): string[][] {
  const matrix: string[][] = [];
  
  for (let i = 0; i < 13; i++) {
    const row: string[] = [];
    for (let j = 0; j < 13; j++) {
      if (i === j) {
        // Pair (diagonal)
        row.push(`${RANKS[i]}${RANKS[j]}`);
      } else if (i < j) {
        // Suited (above diagonal)
        row.push(`${RANKS[i]}${RANKS[j]}s`);
      } else {
        // Offsuit (below diagonal)
        row.push(`${RANKS[j]}${RANKS[i]}o`);
      }
    }
    matrix.push(row);
  }
  
  return matrix;
}

function normalizeHand(hand: string): string {
  if (!hand || hand.length < 2) return '';
  
  const r1 = hand[0].toUpperCase();
  const r2 = hand[1].toUpperCase();
  const suffix = hand.length > 2 ? hand[2].toLowerCase() : '';
  
  const rank1Idx = RANKS.indexOf(r1);
  const rank2Idx = RANKS.indexOf(r2);
  
  if (rank1Idx === -1 || rank2Idx === -1) return hand;
  
  if (r1 === r2) {
    return `${r1}${r2}`;
  } else if (rank1Idx < rank2Idx) {
    return `${r1}${r2}${suffix}`;
  } else {
    return `${r2}${r1}${suffix}`;
  }
}

export function RangeVisualizer({ 
  range, 
  heroHand, 
  title = 'Range', 
  showLabels = true,
  compact = false 
}: RangeVisualizerProps) {
  const matrix = useMemo(() => generateHandMatrix(), []);
  
  const normalizedRange = useMemo(() => {
    return new Set(range.map(h => normalizeHand(h)));
  }, [range]);
  
  const normalizedHeroHand = heroHand ? normalizeHand(heroHand) : null;
  
  // Calculate range percentage
  const rangePercentage = useMemo(() => {
    if (range.includes('any')) return 100;
    
    let combos = 0;
    for (const hand of range) {
      const normalized = normalizeHand(hand);
      if (normalized.length === 2) {
        combos += 6; // Pair
      } else if (normalized.endsWith('s')) {
        combos += 4; // Suited
      } else if (normalized.endsWith('o')) {
        combos += 12; // Offsuit
      }
    }
    return (combos / 1326) * 100;
  }, [range]);

  const cellSize = compact ? 'w-4 h-4 text-[8px]' : 'w-6 h-6 text-[10px]';

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">{title}</h3>
        <span className="text-xs font-mono text-green-400">{rangePercentage.toFixed(1)}%</span>
      </div>
      
      <div className="overflow-x-auto">
        <div className="inline-block">
          {/* Column labels */}
          {showLabels && (
            <div className="flex mb-0.5">
              <div className={`${compact ? 'w-4' : 'w-6'}`}></div>
              {RANKS.map(rank => (
                <div 
                  key={rank} 
                  className={`${cellSize} flex items-center justify-center text-gray-500 font-mono`}
                >
                  {rank}
                </div>
              ))}
            </div>
          )}
          
          {/* Matrix */}
          {matrix.map((row, i) => (
            <div key={i} className="flex">
              {/* Row label */}
              {showLabels && (
                <div className={`${cellSize} flex items-center justify-center text-gray-500 font-mono`}>
                  {RANKS[i]}
                </div>
              )}
              
              {/* Cells */}
              {row.map((hand, j) => {
                const inRange = normalizedRange.has(hand);
                const isHero = normalizedHeroHand === hand;
                const isPair = i === j;
                const isSuited = i < j;
                
                return (
                  <div
                    key={j}
                    className={`
                      ${cellSize} 
                      flex items-center justify-center 
                      font-mono font-medium rounded-sm
                      transition-all duration-150
                      ${isHero 
                        ? 'bg-gradient-to-br from-yellow-400 to-amber-500 text-black ring-2 ring-yellow-400 ring-offset-1 ring-offset-black z-10' 
                        : inRange 
                          ? 'bg-green-500/80 text-white' 
                          : 'bg-gray-800/40 text-gray-600'
                      }
                      ${isPair ? 'font-bold' : ''}
                      ${!compact ? 'hover:scale-110 cursor-pointer' : ''}
                    `}
                    title={`${hand}${isPair ? ' (pair)' : isSuited ? ' (suited)' : ' (offsuit)'}`}
                  >
                    {compact ? '' : hand.slice(0, 2)}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
      
      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-3 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-green-500/80"></div>
          <span>In Range</span>
        </div>
        {heroHand && (
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-gradient-to-br from-yellow-400 to-amber-500"></div>
            <span>Your Hand</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-gray-800/40"></div>
          <span>Fold</span>
        </div>
      </div>
    </div>
  );
}
