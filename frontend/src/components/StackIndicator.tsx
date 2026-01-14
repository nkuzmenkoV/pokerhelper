interface StackIndicatorProps {
  stackBb: number;
  maxBb?: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

interface StackZone {
  name: string;
  min: number;
  max: number;
  color: string;
  bgColor: string;
  description: string;
}

const STACK_ZONES: StackZone[] = [
  { name: 'Critical', min: 0, max: 5, color: 'text-red-400', bgColor: 'danger', description: 'Push/Fold only' },
  { name: 'Short', min: 5, max: 10, color: 'text-orange-400', bgColor: 'warning', description: 'Push/Fold territory' },
  { name: 'Shallow', min: 10, max: 20, color: 'text-yellow-400', bgColor: 'warning', description: 'Short stack play' },
  { name: 'Medium', min: 20, max: 40, color: 'text-green-400', bgColor: 'healthy', description: 'Standard play' },
  { name: 'Deep', min: 40, max: 100, color: 'text-blue-400', bgColor: 'deep', description: 'Postflop flexibility' },
  { name: 'Very Deep', min: 100, max: Infinity, color: 'text-purple-400', bgColor: 'deep', description: 'Maximum flexibility' },
];

function getStackZone(stackBb: number): StackZone {
  for (const zone of STACK_ZONES) {
    if (stackBb >= zone.min && stackBb < zone.max) {
      return zone;
    }
  }
  return STACK_ZONES[STACK_ZONES.length - 1];
}

export function StackIndicator({ 
  stackBb, 
  maxBb = 100, 
  showLabel = true,
  size = 'md' 
}: StackIndicatorProps) {
  const zone = getStackZone(stackBb);
  const percentage = Math.min((stackBb / maxBb) * 100, 100);
  
  const sizeClasses = {
    sm: { height: 'h-2', text: 'text-xs', padding: 'py-2' },
    md: { height: 'h-3', text: 'text-sm', padding: 'py-3' },
    lg: { height: 'h-4', text: 'text-base', padding: 'py-4' },
  };
  
  const sizes = sizeClasses[size];

  return (
    <div className="glass rounded-xl p-4">
      {showLabel && (
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Stack Depth</h3>
          <span className={`text-xs font-medium ${zone.color}`}>{zone.name}</span>
        </div>
      )}
      
      {/* Stack Value */}
      <div className="flex items-baseline gap-2 mb-3">
        <span className={`${sizes.text} font-mono font-bold text-white`}>
          {stackBb.toFixed(1)}
        </span>
        <span className="text-gray-500 text-xs">BB</span>
      </div>
      
      {/* Progress Bar */}
      <div className={`stack-indicator ${sizes.height} mb-3`}>
        <div 
          className={`stack-fill ${zone.bgColor}`}
          style={{ width: `${percentage}%` }}
        />
        
        {/* Zone markers */}
        <div className="absolute inset-0 flex">
          {[10, 20, 40].map(marker => (
            <div 
              key={marker}
              className="absolute top-0 bottom-0 w-px bg-white/20"
              style={{ left: `${(marker / maxBb) * 100}%` }}
            />
          ))}
        </div>
      </div>
      
      {/* Zone Description */}
      <div className="text-xs text-gray-500">
        {zone.description}
      </div>
      
      {/* Stack Zones Legend */}
      <div className="mt-4 grid grid-cols-3 gap-2">
        {STACK_ZONES.slice(0, 6).map((z, i) => (
          <div 
            key={i}
            className={`px-2 py-1 rounded text-[10px] text-center ${
              zone.name === z.name 
                ? 'bg-white/10 border border-white/20' 
                : 'bg-black/20'
            }`}
          >
            <div className={z.color}>{z.name}</div>
            <div className="text-gray-600">{z.min}-{z.max === Infinity ? '∞' : z.max}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Compact inline version
export function StackIndicatorInline({ stackBb }: { stackBb: number }) {
  const zone = getStackZone(stackBb);
  
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 stack-indicator h-2">
        <div 
          className={`stack-fill ${zone.bgColor}`}
          style={{ width: `${Math.min((stackBb / 100) * 100, 100)}%` }}
        />
      </div>
      <span className={`text-xs font-mono ${zone.color}`}>
        {stackBb.toFixed(0)}BB
      </span>
    </div>
  );
}
