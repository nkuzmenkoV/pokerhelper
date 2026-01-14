import { useMemo } from 'react';

interface PlayerHUD {
  playerId: string;
  playerName: string;
  hands: number;
  vpip: number;
  pfr: number;
  threeBet: number;
  af: number | string;
  position: string;
  isHero: boolean;
}

interface HUDOverlayProps {
  players: PlayerHUD[];
  showDetailed: boolean;
}

// Player type classification based on stats
function getPlayerType(vpip: number, pfr: number, hands: number): {
  type: string;
  color: string;
  description: string;
} {
  if (hands < 20) {
    return { type: '?', color: 'text-gray-400', description: 'Недостаточно данных' };
  }

  if (vpip < 20) {
    if (pfr > 15) {
      return { type: 'TAG', color: 'text-green-400', description: 'Tight-Aggressive' };
    }
    return { type: 'Rock', color: 'text-blue-400', description: 'Очень тайтовый' };
  } else if (vpip < 30) {
    if (pfr > 18) {
      return { type: 'LAG', color: 'text-yellow-400', description: 'Loose-Aggressive' };
    }
    return { type: 'Weak', color: 'text-orange-400', description: 'Слабо-тайтовый' };
  } else {
    if (pfr > 20) {
      return { type: 'Maniac', color: 'text-red-400', description: 'Маньяк' };
    }
    return { type: 'Fish', color: 'text-pink-400', description: 'Коллинг-станция' };
  }
}

// Color coding for stats
function getStatColor(value: number, thresholds: { low: number; mid: number; high: number }): string {
  if (value < thresholds.low) return 'text-blue-400';
  if (value < thresholds.mid) return 'text-green-400';
  if (value < thresholds.high) return 'text-yellow-400';
  return 'text-red-400';
}

function PlayerHUDCard({ player, showDetailed }: { player: PlayerHUD; showDetailed: boolean }) {
  const playerType = useMemo(
    () => getPlayerType(player.vpip, player.pfr, player.hands),
    [player.vpip, player.pfr, player.hands]
  );

  const vpipColor = getStatColor(player.vpip, { low: 18, mid: 25, high: 35 });
  const pfrColor = getStatColor(player.pfr, { low: 12, mid: 18, high: 25 });
  const threeBetColor = getStatColor(player.threeBet, { low: 5, mid: 8, high: 12 });

  if (player.isHero) {
    return null; // Don't show HUD for hero
  }

  return (
    <div className="bg-gray-900/90 backdrop-blur-sm rounded-lg px-2 py-1.5 border border-gray-700/50 min-w-[120px]">
      {/* Player Name & Type */}
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-300 truncate max-w-[80px]">
          {player.playerName}
        </span>
        <span className={`text-xs font-bold ${playerType.color}`} title={playerType.description}>
          {playerType.type}
        </span>
      </div>

      {/* Main Stats */}
      <div className="flex gap-2 text-xs font-mono">
        <div className="flex flex-col items-center">
          <span className="text-gray-500 text-[10px]">VPIP</span>
          <span className={vpipColor}>{player.vpip}</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-gray-500 text-[10px]">PFR</span>
          <span className={pfrColor}>{player.pfr}</span>
        </div>
        {showDetailed && (
          <>
            <div className="flex flex-col items-center">
              <span className="text-gray-500 text-[10px]">3B</span>
              <span className={threeBetColor}>{player.threeBet}</span>
            </div>
            <div className="flex flex-col items-center">
              <span className="text-gray-500 text-[10px]">AF</span>
              <span className="text-gray-300">{player.af}</span>
            </div>
          </>
        )}
      </div>

      {/* Hand count */}
      <div className="text-[10px] text-gray-500 text-center mt-1">
        {player.hands} hands
      </div>
    </div>
  );
}

export function HUDOverlay({ players, showDetailed }: HUDOverlayProps) {
  const activePlayers = players.filter(p => !p.isHero);

  if (activePlayers.length === 0) {
    return null;
  }

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">HUD Stats</h3>
        <span className="text-xs text-gray-400">{activePlayers.length} opponents</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {activePlayers.map((player) => (
          <PlayerHUDCard
            key={player.playerId}
            player={player}
            showDetailed={showDetailed}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-gray-700/50">
        <div className="text-[10px] text-gray-500 space-y-1">
          <div className="flex flex-wrap gap-3">
            <span><span className="text-green-400 font-bold">TAG</span> - Сильный игрок</span>
            <span><span className="text-blue-400 font-bold">Rock</span> - Очень тайтовый</span>
            <span><span className="text-yellow-400 font-bold">LAG</span> - Агрессивный</span>
            <span><span className="text-pink-400 font-bold">Fish</span> - Слабый игрок</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Compact HUD for inline display (e.g., next to player name)
export function CompactHUD({ vpip, pfr, hands }: { vpip: number; pfr: number; hands: number }) {
  return (
    <span className="text-[10px] font-mono text-gray-400">
      {vpip}/{pfr} ({hands})
    </span>
  );
}
