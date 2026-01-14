import { useState, useRef, useEffect, useCallback } from 'react';

interface CardPosition {
  x: number;
  y: number;
  width: number;
  height: number;
  index: number;
}

interface Layout {
  name: string;
  hero_cards: CardPosition[];
  board_cards: CardPosition[];
}

interface PositionCalibrationProps {
  imageUrl: string | null;
  imageWidth: number;
  imageHeight: number;
  layout: Layout | null;
  presets: Record<string, Layout>;
  onLayoutUpdate: (layout: Layout) => void;
  onPositionUpdate: (regionType: string, index: number, pos: CardPosition) => void;
  onPresetSelect: (presetName: string) => void;
}

type DragMode = 'move' | 'resize-br' | 'resize-tl' | null;

export function PositionCalibration({
  imageUrl,
  imageWidth,
  imageHeight,
  layout,
  presets,
  onLayoutUpdate,
  onPositionUpdate,
  onPresetSelect,
}: PositionCalibrationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(1);
  const [selectedRegion, setSelectedRegion] = useState<{type: string; index: number} | null>(null);
  const [dragMode, setDragMode] = useState<DragMode>(null);
  const [dragStart, setDragStart] = useState<{x: number; y: number} | null>(null);
  const [originalPos, setOriginalPos] = useState<CardPosition | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  // Load image
  useEffect(() => {
    if (!imageUrl) return;
    const img = new Image();
    img.onload = () => {
      imageRef.current = img;
      redraw();
    };
    img.src = imageUrl;
  }, [imageUrl]);

  // Calculate scale
  useEffect(() => {
    const container = canvasRef.current?.parentElement;
    if (container && imageWidth > 0) {
      const newScale = Math.min(1, container.clientWidth / imageWidth);
      setScale(newScale);
    }
  }, [imageWidth]);

  // Redraw canvas
  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    const img = imageRef.current;
    
    if (!canvas || !ctx || !img || !layout) return;

    canvas.width = imageWidth * scale;
    canvas.height = imageHeight * scale;

    // Draw image
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Draw positions
    const drawPosition = (pos: CardPosition, type: string, index: number) => {
      const x = pos.x * canvas.width;
      const y = pos.y * canvas.height;
      const w = pos.width * canvas.width;
      const h = pos.height * canvas.height;
      
      const isSelected = selectedRegion?.type === type && selectedRegion?.index === index;
      
      // Border
      ctx.strokeStyle = isSelected ? '#22C55E' : type === 'hero' ? '#F59E0B' : '#3B82F6';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(x, y, w, h);
      
      // Fill
      ctx.fillStyle = isSelected ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255, 255, 255, 0.1)';
      ctx.fillRect(x, y, w, h);
      
      // Label
      ctx.fillStyle = '#FFF';
      ctx.font = 'bold 12px sans-serif';
      ctx.fillText(`${type[0].toUpperCase()}${index + 1}`, x + 4, y + 14);
      
      // Resize handle (bottom-right)
      if (isSelected) {
        ctx.fillStyle = '#22C55E';
        ctx.fillRect(x + w - 8, y + h - 8, 8, 8);
      }
    };

    layout.hero_cards.forEach((pos, i) => drawPosition(pos, 'hero', i));
    layout.board_cards.forEach((pos, i) => drawPosition(pos, 'board', i));
  }, [layout, selectedRegion, scale, imageWidth, imageHeight]);

  useEffect(() => {
    redraw();
  }, [redraw]);

  // Get mouse position
  const getMousePos = (e: React.MouseEvent): {x: number; y: number} => {
    const canvas = canvasRef.current;
    if (!canvas) return {x: 0, y: 0};
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / scale / imageWidth,
      y: (e.clientY - rect.top) / scale / imageHeight,
    };
  };

  // Find position at mouse
  const findPositionAt = (mx: number, my: number): {type: string; index: number; mode: DragMode} | null => {
    if (!layout) return null;

    const checkPosition = (pos: CardPosition, type: string, index: number) => {
      const x2 = pos.x + pos.width;
      const y2 = pos.y + pos.height;
      
      // Check resize handle first
      if (mx >= x2 - 0.02 && mx <= x2 && my >= y2 - 0.02 && my <= y2) {
        return {type, index, mode: 'resize-br' as DragMode};
      }
      
      // Check inside
      if (mx >= pos.x && mx <= x2 && my >= pos.y && my <= y2) {
        return {type, index, mode: 'move' as DragMode};
      }
      
      return null;
    };

    for (let i = 0; i < layout.hero_cards.length; i++) {
      const result = checkPosition(layout.hero_cards[i], 'hero', i);
      if (result) return result;
    }
    
    for (let i = 0; i < layout.board_cards.length; i++) {
      const result = checkPosition(layout.board_cards[i], 'board', i);
      if (result) return result;
    }
    
    return null;
  };

  // Mouse handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    const pos = getMousePos(e);
    const hit = findPositionAt(pos.x, pos.y);
    
    if (hit) {
      setSelectedRegion({type: hit.type, index: hit.index});
      setDragMode(hit.mode);
      setDragStart(pos);
      
      const cards = hit.type === 'hero' ? layout?.hero_cards : layout?.board_cards;
      if (cards) {
        setOriginalPos({...cards[hit.index]});
      }
    } else {
      setSelectedRegion(null);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragMode || !dragStart || !originalPos || !selectedRegion || !layout) return;
    
    const pos = getMousePos(e);
    const dx = pos.x - dragStart.x;
    const dy = pos.y - dragStart.y;
    
    let newPos: CardPosition;
    
    if (dragMode === 'move') {
      newPos = {
        ...originalPos,
        x: Math.max(0, Math.min(1 - originalPos.width, originalPos.x + dx)),
        y: Math.max(0, Math.min(1 - originalPos.height, originalPos.y + dy)),
      };
    } else if (dragMode === 'resize-br') {
      newPos = {
        ...originalPos,
        width: Math.max(0.02, Math.min(0.2, originalPos.width + dx)),
        height: Math.max(0.02, Math.min(0.2, originalPos.height + dy)),
      };
    } else {
      return;
    }
    
    // Update local layout for immediate feedback
    const newLayout = {...layout};
    if (selectedRegion.type === 'hero') {
      newLayout.hero_cards = [...layout.hero_cards];
      newLayout.hero_cards[selectedRegion.index] = newPos;
    } else {
      newLayout.board_cards = [...layout.board_cards];
      newLayout.board_cards[selectedRegion.index] = newPos;
    }
    
    onLayoutUpdate(newLayout);
  };

  const handleMouseUp = () => {
    if (dragMode && selectedRegion && layout) {
      // Save position to backend
      const cards = selectedRegion.type === 'hero' ? layout.hero_cards : layout.board_cards;
      const pos = cards[selectedRegion.index];
      onPositionUpdate(selectedRegion.type, selectedRegion.index, pos);
    }
    
    setDragMode(null);
    setDragStart(null);
    setOriginalPos(null);
  };

  if (!imageUrl) {
    return (
      <div className="glass rounded-xl p-4">
        <h3 className="text-lg font-semibold text-white mb-3">Position Calibration</h3>
        <div className="text-center py-8 text-gray-500">
          Capture a screenshot to calibrate card positions
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">Position Calibration</h3>
        
        {/* Preset selector */}
        <select
          onChange={(e) => onPresetSelect(e.target.value)}
          value={layout?.name || ''}
          className="bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-white"
        >
          {Object.keys(presets).map(name => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </div>

      {/* Canvas */}
      <div className="relative bg-gray-900 rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="cursor-crosshair"
        />
      </div>

      {/* Instructions */}
      <div className="mt-3 text-xs text-gray-400 space-y-1">
        <p>• Click and drag boxes to reposition</p>
        <p>• Drag bottom-right corner to resize</p>
        <p>• <span className="text-amber-400">Orange</span> = Hero cards, <span className="text-blue-400">Blue</span> = Board cards</p>
      </div>

      {/* Selected info */}
      {selectedRegion && layout && (
        <div className="mt-3 p-2 bg-gray-800/50 rounded text-xs">
          <div className="text-gray-300 font-medium">
            {selectedRegion.type === 'hero' ? 'Hero' : 'Board'} Card {selectedRegion.index + 1}
          </div>
          {(() => {
            const cards = selectedRegion.type === 'hero' ? layout.hero_cards : layout.board_cards;
            const pos = cards[selectedRegion.index];
            return (
              <div className="text-gray-500 mt-1">
                Position: ({(pos.x * 100).toFixed(1)}%, {(pos.y * 100).toFixed(1)}%)
                <br />
                Size: {(pos.width * 100).toFixed(1)}% x {(pos.height * 100).toFixed(1)}%
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
