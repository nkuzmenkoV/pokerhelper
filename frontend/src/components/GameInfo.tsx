import type { GameState } from '../types/poker';

interface GameInfoProps {
  gameState: GameState;
}

// Card suit symbols and colors
const SUIT_SYMBOLS: Record<string, { symbol: string; color: string }> = {
  s: { symbol: '♠', color: 'text-gray-300' },
  h: { symbol: '♥', color: 'text-red-500' },
  d: { symbol: '♦', color: 'text-blue-400' },
  c: { symbol: '♣', color: 'text-green-400' },
};

function CardDisplay({ card }: { card: string }) {
  if (card.length < 2) return null;
  
  const rank = card[0];
  const suit = card[1];
  const suitInfo = SUIT_SYMBOLS[suit] || { symbol: suit, color: 'text-white' };

  return (
    <div className="inline-flex items-center justify-center w-10 h-14 bg-white rounded-lg shadow-lg">
      <div className="text-center">
        <div className="text-lg font-bold text-gray-900">{rank}</div>
        <div className={`text-xl ${suitInfo.color}`}>{suitInfo.symbol}</div>
      </div>
    </div>
  );
}

export function GameInfo({ gameState }: GameInfoProps) {
  return (
    <div className="glass rounded-xl p-4">
      <h3 className="text-lg font-semibold text-white mb-4">Game State</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Pot */}
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-400 uppercase">Pot</div>
          <div className="text-xl font-bold text-poker-green-400">
            {gameState.potBb.toFixed(1)} BB
          </div>
        </div>

        {/* Blinds */}
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-400 uppercase">Blinds</div>
          <div className="text-lg font-semibold text-white">
            {gameState.smallBlind}/{gameState.bigBlind}
            {gameState.ante > 0 && <span className="text-gray-400">/{gameState.ante}</span>}
          </div>
        </div>

        {/* Hero Stack */}
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-400 uppercase">Your Stack</div>
          <div className="text-xl font-bold text-white">
            {gameState.heroStackBb.toFixed(1)} BB
          </div>
        </div>

        {/* Position */}
        <div className="bg-gray-800/50 rounded-lg p-3 text-center">
          <div className="text-xs text-gray-400 uppercase">Position</div>
          <div className="text-xl font-bold text-amber-400">
            {gameState.heroPosition}
          </div>
        </div>
      </div>

      {/* Cards Section */}
      <div className="flex flex-wrap gap-6 justify-center">
        {/* Hero Cards */}
        <div className="text-center">
          <div className="text-xs text-gray-400 uppercase mb-2">Your Cards</div>
          <div className="flex gap-2 justify-center">
            {gameState.heroCards.length > 0 ? (
              gameState.heroCards.map((card, i) => (
                <CardDisplay key={i} card={card} />
              ))
            ) : (
              <div className="text-gray-500">No cards detected</div>
            )}
          </div>
        </div>

        {/* Board Cards */}
        {gameState.boardCards.length > 0 && (
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase mb-2">Board</div>
            <div className="flex gap-2 justify-center">
              {gameState.boardCards.map((card, i) => (
                <CardDisplay key={i} card={card} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Street Indicator */}
      <div className="mt-4 flex justify-center">
        <div className="inline-flex rounded-lg bg-gray-800/50 p-1">
          {['preflop', 'flop', 'turn', 'river'].map((street) => (
            <div
              key={street}
              className={`
                px-3 py-1 rounded text-xs font-medium capitalize transition-colors
                ${gameState.street === street 
                  ? 'bg-poker-green-600 text-white' 
                  : 'text-gray-500'
                }
              `}
            >
              {street}
            </div>
          ))}
        </div>
      </div>

      {/* Players */}
      {gameState.players.length > 0 && (
        <div className="mt-4">
          <div className="text-xs text-gray-400 uppercase mb-2">Players ({gameState.numActivePlayers} active)</div>
          <div className="flex flex-wrap gap-2">
            {gameState.players.map((player) => (
              <div
                key={player.seat}
                className={`
                  px-3 py-1.5 rounded-lg text-xs
                  ${player.isHero 
                    ? 'bg-poker-green-600/30 border border-poker-green-500' 
                    : player.isActive 
                      ? 'bg-gray-700/50' 
                      : 'bg-gray-800/30 opacity-50'
                  }
                `}
              >
                <div className="font-medium text-white">
                  {player.isHero ? 'You' : `Seat ${player.seat}`}
                  <span className="text-gray-400 ml-1">({player.position})</span>
                </div>
                <div className="text-gray-400">
                  {(player.stack / gameState.bigBlind).toFixed(1)} BB
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
