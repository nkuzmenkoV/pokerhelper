interface PositionDisplayProps {
  heroPosition: string;
  numPlayers?: number;
  buttonSeat?: number;
  tableFormat?: '6max' | '9max';
}

interface PositionInfo {
  name: string;
  shortName: string;
  color: string;
  description: string;
  angle: number; // Position around table (degrees)
}

const POSITIONS_6MAX: Record<string, PositionInfo> = {
  'UTG': { name: 'Under the Gun', shortName: 'UTG', color: '#f87171', description: 'First to act, tightest range', angle: 180 },
  'HJ': { name: 'Hijack', shortName: 'HJ', color: '#2dd4bf', description: 'One before cutoff', angle: 240 },
  'CO': { name: 'Cutoff', shortName: 'CO', color: '#a78bfa', description: 'Second to last, wider range', angle: 300 },
  'BTN': { name: 'Button', shortName: 'BTN', color: '#fbbf24', description: 'Best position, widest range', angle: 0 },
  'SB': { name: 'Small Blind', shortName: 'SB', color: '#f472b6', description: 'Forced bet, OOP postflop', angle: 60 },
  'BB': { name: 'Big Blind', shortName: 'BB', color: '#60a5fa', description: 'Forced bet, closes action', angle: 120 },
};

const POSITIONS_9MAX: Record<string, PositionInfo> = {
  'UTG': { name: 'Under the Gun', shortName: 'UTG', color: '#f87171', description: 'First to act', angle: 140 },
  'UTG1': { name: 'UTG+1', shortName: 'UTG+1', color: '#fb923c', description: 'Second position', angle: 170 },
  'UTG2': { name: 'UTG+2', shortName: 'UTG+2', color: '#facc15', description: 'Third position', angle: 200 },
  'LJ': { name: 'Lojack', shortName: 'LJ', color: '#34d399', description: 'Middle position', angle: 230 },
  'HJ': { name: 'Hijack', shortName: 'HJ', color: '#2dd4bf', description: 'One before cutoff', angle: 260 },
  'CO': { name: 'Cutoff', shortName: 'CO', color: '#a78bfa', description: 'Second to last', angle: 290 },
  'BTN': { name: 'Button', shortName: 'BTN', color: '#fbbf24', description: 'Best position', angle: 320 },
  'SB': { name: 'Small Blind', shortName: 'SB', color: '#f472b6', description: 'Forced bet', angle: 30 },
  'BB': { name: 'Big Blind', shortName: 'BB', color: '#60a5fa', description: 'Big blind', angle: 80 },
};

export function PositionDisplay({ 
  heroPosition, 
  tableFormat = '6max' 
}: PositionDisplayProps) {
  const positions = tableFormat === '9max' ? POSITIONS_9MAX : POSITIONS_6MAX;
  const positionKeys = Object.keys(positions);
  const heroInfo = positions[heroPosition] || positions['BTN'];
  
  // Calculate table dimensions
  const tableWidth = 200;
  const tableHeight = 140;
  const centerX = tableWidth / 2;
  const centerY = tableHeight / 2;
  const radiusX = 80;
  const radiusY = 55;

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Position</h3>
        <span className={`position-badge ${heroPosition.toLowerCase()}`}>
          {heroInfo.shortName}
        </span>
      </div>
      
      {/* Visual Table */}
      <div className="relative flex justify-center mb-4">
        <svg width={tableWidth} height={tableHeight} viewBox={`0 0 ${tableWidth} ${tableHeight}`}>
          {/* Table felt */}
          <ellipse 
            cx={centerX} 
            cy={centerY} 
            rx={radiusX} 
            ry={radiusY}
            fill="url(#feltGradient)"
            stroke="rgba(255,255,255,0.2)"
            strokeWidth="2"
          />
          
          {/* Gradient definition */}
          <defs>
            <radialGradient id="feltGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#1e5631" />
              <stop offset="100%" stopColor="#0f2817" />
            </radialGradient>
          </defs>
          
          {/* Position markers */}
          {positionKeys.map((pos) => {
            const info = positions[pos];
            const angle = (info.angle * Math.PI) / 180;
            const x = centerX + radiusX * 1.15 * Math.cos(angle);
            const y = centerY + radiusY * 1.15 * Math.sin(angle);
            const isHero = pos === heroPosition;
            
            return (
              <g key={pos}>
                {/* Position circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHero ? 14 : 10}
                  fill={isHero ? info.color : 'rgba(255,255,255,0.1)'}
                  stroke={isHero ? 'white' : 'rgba(255,255,255,0.2)'}
                  strokeWidth={isHero ? 2 : 1}
                />
                
                {/* Position label */}
                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={isHero ? 8 : 6}
                  fill={isHero ? 'black' : 'rgba(255,255,255,0.5)'}
                  fontWeight={isHero ? 'bold' : 'normal'}
                  fontFamily="monospace"
                >
                  {info.shortName.length > 3 ? pos.slice(0, 2) : info.shortName}
                </text>
                
                {/* Hero indicator */}
                {isHero && (
                  <circle
                    cx={x}
                    cy={y}
                    r={18}
                    fill="none"
                    stroke={info.color}
                    strokeWidth="2"
                    opacity="0.5"
                    className="animate-pulse"
                  />
                )}
              </g>
            );
          })}
          
          {/* Dealer button */}
          <g>
            <circle
              cx={centerX}
              cy={centerY}
              r={12}
              fill="#1a1a1a"
              stroke="white"
              strokeWidth="1"
            />
            <text
              x={centerX}
              y={centerY}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="8"
              fill="white"
              fontWeight="bold"
            >
              D
            </text>
          </g>
        </svg>
      </div>
      
      {/* Position Info */}
      <div className="text-center">
        <div className="text-lg font-semibold text-white mb-1" style={{ color: heroInfo.color }}>
          {heroInfo.name}
        </div>
        <div className="text-xs text-gray-500">
          {heroInfo.description}
        </div>
      </div>
      
      {/* Position Tips */}
      <div className="mt-4 p-3 bg-black/30 rounded-lg">
        <div className="text-xs text-gray-400">
          {heroPosition === 'BTN' && '✓ Best position - can steal blinds and play widest range'}
          {heroPosition === 'SB' && '⚠ Out of position postflop - be selective'}
          {heroPosition === 'BB' && '✓ Already invested - can defend wider'}
          {heroPosition === 'CO' && '✓ Second best position - good for late position steals'}
          {(heroPosition === 'UTG' || heroPosition === 'UTG1' || heroPosition === 'UTG2') && 
            '⚠ Many players to act - play tight value hands'}
          {(heroPosition === 'HJ' || heroPosition === 'LJ') && 
            '◉ Middle position - balanced approach'}
        </div>
      </div>
    </div>
  );
}

// Compact badge version
export function PositionBadge({ position }: { position: string }) {
  const info = POSITIONS_6MAX[position] || POSITIONS_9MAX[position];
  
  if (!info) {
    return <span className="position-badge">{position}</span>;
  }
  
  return (
    <span 
      className="position-badge"
      style={{ backgroundColor: info.color, color: '#0f172a' }}
      title={info.description}
    >
      {info.shortName}
    </span>
  );
}
