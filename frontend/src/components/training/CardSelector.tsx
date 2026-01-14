import { useMemo, useEffect, useState, useCallback } from 'react';

interface CardSelectorProps {
  selectedCard: string | null;
  onSelect: (card: string, classId: number) => void;
  labeledCards?: Set<string>;
  disabled?: boolean;
  onQuickSelect?: (card: string, classId: number) => void; // For quick label mode
}

// Card constants
const RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'];
const SUITS = [
  { code: 's', symbol: '♠', color: 'text-gray-300', name: 'spades', key: 's' },
  { code: 'h', symbol: '♥', color: 'text-red-500', name: 'hearts', key: 'h' },
  { code: 'd', symbol: '♦', color: 'text-blue-400', name: 'diamonds', key: 'd' },
  { code: 'c', symbol: '♣', color: 'text-green-400', name: 'clubs', key: 'c' },
];

// Keyboard mappings for ranks
const RANK_KEYS: Record<string, string> = {
  'a': 'A', 'A': 'A',
  'k': 'K', 'K': 'K',
  'q': 'Q', 'Q': 'Q',
  'j': 'J', 'J': 'J',
  't': 'T', 'T': 'T', '0': 'T', // T or 0 for Ten
  '9': '9',
  '8': '8',
  '7': '7',
  '6': '6',
  '5': '5',
  '4': '4',
  '3': '3',
  '2': '2',
};

// Keyboard mappings for suits
const SUIT_KEYS: Record<string, string> = {
  's': 's', 'S': 's', // Spades
  'h': 'h', 'H': 'h', // Hearts
  'd': 'd', 'D': 'd', // Diamonds
  'c': 'c', 'C': 'c', // Clubs
};

// Build class ID mapping (same order as backend)
const CARD_CLASSES: string[] = [];
for (const suit of ['c', 'd', 'h', 's']) {
  for (const rank of ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']) {
    CARD_CLASSES.push(`${rank}${suit}`);
  }
}

const CLASS_TO_ID: Record<string, number> = {};
CARD_CLASSES.forEach((card, idx) => {
  CLASS_TO_ID[card] = idx;
});

export function CardSelector({
  selectedCard,
  onSelect,
  labeledCards = new Set(),
  disabled = false,
  onQuickSelect,
}: CardSelectorProps) {
  // Pending rank for two-key combo
  const [pendingRank, setPendingRank] = useState<string | null>(null);
  const [lastKeyTime, setLastKeyTime] = useState(0);
  
  // Build card grid
  const cardGrid = useMemo(() => {
    return SUITS.map(suit => ({
      suit,
      cards: RANKS.map(rank => ({
        card: `${rank}${suit.code}`,
        rank,
        classId: CLASS_TO_ID[`${rank}${suit.code}`],
      })),
    }));
  }, []);

  // Handle card selection via keyboard
  const handleKeyboardSelect = useCallback((card: string) => {
    const classId = CLASS_TO_ID[card];
    if (classId !== undefined) {
      onSelect(card, classId);
      if (onQuickSelect) {
        onQuickSelect(card, classId);
      }
    }
  }, [onSelect, onQuickSelect]);

  // Keyboard event handler
  useEffect(() => {
    if (disabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      const key = e.key;
      const now = Date.now();
      
      // Check if it's a rank key
      if (RANK_KEYS[key]) {
        const rank = RANK_KEYS[key];
        setPendingRank(rank);
        setLastKeyTime(now);
        return;
      }
      
      // Check if it's a suit key and we have a pending rank
      if (SUIT_KEYS[key] && pendingRank) {
        // Only accept if within 2 seconds of rank press
        if (now - lastKeyTime < 2000) {
          const suit = SUIT_KEYS[key];
          const card = `${pendingRank}${suit}`;
          handleKeyboardSelect(card);
        }
        setPendingRank(null);
        return;
      }
      
      // Escape clears pending
      if (key === 'Escape') {
        setPendingRank(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [disabled, pendingRank, lastKeyTime, handleKeyboardSelect]);

  // Clear pending rank after timeout
  useEffect(() => {
    if (!pendingRank) return;
    
    const timeout = setTimeout(() => {
      setPendingRank(null);
    }, 2000);
    
    return () => clearTimeout(timeout);
  }, [pendingRank]);

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">Select Card</h3>
        
        {/* Pending rank indicator */}
        {pendingRank && (
          <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/20 rounded-full animate-pulse">
            <span className="text-amber-400 font-bold text-lg">{pendingRank}</span>
            <span className="text-amber-300 text-sm">+ suit?</span>
          </div>
        )}
      </div>
      
      {/* Card Grid */}
      <div className="space-y-2">
        {cardGrid.map(({ suit, cards }) => (
          <div key={suit.code} className="flex items-center gap-1">
            {/* Suit symbol with keyboard hint */}
            <div className={`w-6 text-center relative group ${suit.color}`}>
              <span className="text-xl">{suit.symbol}</span>
              <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[10px] text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                {suit.key.toUpperCase()}
              </span>
            </div>
            
            {/* Cards row */}
            <div className="flex gap-1 flex-1">
              {cards.map(({ card, rank, classId }) => {
                const isSelected = selectedCard === card;
                const isLabeled = labeledCards.has(card);
                const isPendingMatch = pendingRank === rank;
                
                return (
                  <button
                    key={card}
                    onClick={() => onSelect(card, classId)}
                    disabled={disabled}
                    className={`
                      w-8 h-10 rounded flex items-center justify-center
                      font-bold text-sm transition-all relative
                      ${isSelected 
                        ? 'bg-poker-green-500 text-white ring-2 ring-poker-green-300 scale-110' 
                        : isPendingMatch
                          ? 'bg-amber-500/30 text-amber-300 ring-1 ring-amber-500/50'
                          : isLabeled
                            ? 'bg-blue-500/30 text-blue-300 border border-blue-500/50'
                            : 'bg-gray-700/50 text-gray-300 hover:bg-gray-600/50'
                      }
                      ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                    title={`${rank}${suit.symbol} (${card}) - Press ${rank.toLowerCase()} then ${suit.key}`}
                  >
                    <span className={isSelected ? 'text-white' : isPendingMatch ? 'text-amber-300' : suit.color}>
                      {rank}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Selected card display */}
      {selectedCard && (
        <div className="mt-4 pt-3 border-t border-gray-700/50">
          <div className="flex items-center justify-between">
            <span className="text-gray-400 text-sm">Selected:</span>
            <div className="flex items-center gap-2">
              <span className={`text-2xl ${
                SUITS.find(s => s.code === selectedCard[1])?.color || 'text-white'
              }`}>
                {selectedCard[0]}
                {SUITS.find(s => s.code === selectedCard[1])?.symbol}
              </span>
              <span className="text-gray-500 text-sm">
                (class: {CLASS_TO_ID[selectedCard]})
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-gray-700/50 flex flex-wrap gap-3 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-poker-green-500 rounded" />
          <span>Selected</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-amber-500/30 ring-1 ring-amber-500/50 rounded" />
          <span>Pending</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500/30 border border-blue-500/50 rounded" />
          <span>Labeled</span>
        </div>
      </div>

      {/* Keyboard shortcuts help */}
      <div className="mt-3 p-2 bg-gray-800/50 rounded text-xs text-gray-400">
        <div className="font-medium text-gray-300 mb-1">⌨️ Keyboard Shortcuts</div>
        <div className="grid grid-cols-2 gap-1">
          <div><kbd className="kbd">A-K-Q-J-T-9-2</kbd> Rank</div>
          <div><kbd className="kbd">S-H-D-C</kbd> Suit</div>
        </div>
        <div className="mt-1 text-gray-500">
          Example: <kbd className="kbd">A</kbd> then <kbd className="kbd">S</kbd> = A♠
        </div>
      </div>
    </div>
  );
}

// Export class mapping for use elsewhere
export { CARD_CLASSES, CLASS_TO_ID, RANKS, SUITS };
