import { useEffect, useState } from 'react';

interface DatasetStats {
  total_images: number;
  total_boxes: number;
  cards_count: Record<string, number>;
  coverage: number;
  missing_cards: string[];
  balanced: boolean;
}

interface DatasetProgressProps {
  stats: DatasetStats | null;
  onRefresh: () => void;
  targetPerCard?: number;
}

const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUITS = [
  { code: 's', symbol: '♠', color: 'text-gray-300' },
  { code: 'h', symbol: '♥', color: 'text-red-500' },
  { code: 'd', symbol: '♦', color: 'text-blue-400' },
  { code: 'c', symbol: '♣', color: 'text-green-400' },
];

export function DatasetProgress({ stats, onRefresh, targetPerCard = 100 }: DatasetProgressProps) {
  const totalTarget = 52 * targetPerCard;
  
  if (!stats) {
    return (
      <div className="glass rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Dataset Progress</h3>
          <button
            onClick={onRefresh}
            className="text-poker-green-400 hover:text-poker-green-300 text-sm"
          >
            Refresh
          </button>
        </div>
        <div className="text-center py-8 text-gray-500">
          Loading statistics...
        </div>
      </div>
    );
  }

  const progressPercent = Math.min((stats.total_boxes / totalTarget) * 100, 100);
  
  // Calculate color based on count
  const getCountColor = (count: number): string => {
    if (count === 0) return 'bg-gray-700';
    if (count < targetPerCard * 0.25) return 'bg-red-500/50';
    if (count < targetPerCard * 0.5) return 'bg-amber-500/50';
    if (count < targetPerCard) return 'bg-blue-500/50';
    return 'bg-green-500/50';
  };

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Dataset Progress</h3>
        <button
          onClick={onRefresh}
          className="text-poker-green-400 hover:text-poker-green-300 text-sm"
        >
          Refresh
        </button>
      </div>

      {/* Overall progress */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">Overall Progress</span>
          <span className="text-white font-medium">
            {stats.total_boxes} / {totalTarget} samples
          </span>
        </div>
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-poker-green-600 to-poker-green-400 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="text-right text-xs text-gray-500 mt-1">
          {progressPercent.toFixed(1)}%
        </div>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-white">{stats.total_images}</div>
          <div className="text-xs text-gray-400">Images</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-white">{stats.total_boxes}</div>
          <div className="text-xs text-gray-400">Labels</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className={`text-2xl font-bold ${stats.coverage === 100 ? 'text-green-400' : 'text-amber-400'}`}>
            {stats.coverage.toFixed(0)}%
          </div>
          <div className="text-xs text-gray-400">Coverage</div>
        </div>
      </div>

      {/* Per-card heatmap */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-400 mb-2">Samples per Card</h4>
        <div className="space-y-1">
          {SUITS.map(suit => (
            <div key={suit.code} className="flex items-center gap-1">
              <span className={`w-5 text-sm ${suit.color}`}>{suit.symbol}</span>
              <div className="flex gap-0.5 flex-1">
                {RANKS.map(rank => {
                  const card = `${rank}${suit.code}`;
                  const count = stats.cards_count[card] || 0;
                  return (
                    <div
                      key={card}
                      className={`flex-1 h-6 rounded-sm ${getCountColor(count)} flex items-center justify-center`}
                      title={`${card}: ${count} samples`}
                    >
                      <span className="text-[9px] text-white/70">
                        {count > 0 ? count : ''}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
          
          {/* Rank labels */}
          <div className="flex items-center gap-1 mt-1">
            <span className="w-5" />
            <div className="flex gap-0.5 flex-1">
              {RANKS.map(rank => (
                <div key={rank} className="flex-1 text-center text-[9px] text-gray-500">
                  {rank}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-500 border-t border-gray-700/50 pt-3">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-gray-700 rounded-sm" />
          <span>0</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-red-500/50 rounded-sm" />
          <span>1-{Math.floor(targetPerCard * 0.25)}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-amber-500/50 rounded-sm" />
          <span>{Math.floor(targetPerCard * 0.25)}-{Math.floor(targetPerCard * 0.5)}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500/50 rounded-sm" />
          <span>{Math.floor(targetPerCard * 0.5)}-{targetPerCard}</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-green-500/50 rounded-sm" />
          <span>{targetPerCard}+</span>
        </div>
      </div>

      {/* Missing cards warning */}
      {stats.missing_cards.length > 0 && (
        <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <div className="text-amber-400 text-sm font-medium mb-1">
            Missing samples for {stats.missing_cards.length} cards:
          </div>
          <div className="text-amber-300/70 text-xs">
            {stats.missing_cards.slice(0, 10).join(', ')}
            {stats.missing_cards.length > 10 && ` and ${stats.missing_cards.length - 10} more...`}
          </div>
        </div>
      )}

      {/* Ready indicator */}
      {stats.total_boxes >= 100 && (
        <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <div className="text-green-400 text-sm">
            ✓ Dataset ready for training ({stats.total_boxes} samples)
          </div>
        </div>
      )}
    </div>
  );
}
