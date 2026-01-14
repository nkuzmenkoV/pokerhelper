import { useRef, useState, useEffect, useCallback } from 'react';

interface BoundingBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  classId?: number;
  className?: string;
  confidence?: number;
  isSelected?: boolean;
}

interface LabelingCanvasProps {
  imageUrl: string | null;
  boxes: BoundingBox[];
  selectedBoxId: string | null;
  onBoxSelect: (boxId: string | null) => void;
  onBoxCreate: (box: Omit<BoundingBox, 'id'>) => void;
  onBoxUpdate: (boxId: string, updates: Partial<BoundingBox>) => void;
  onBoxDelete: (boxId: string) => void;
  imageWidth: number;
  imageHeight: number;
  mode: 'select' | 'draw';
}

// Suit colors for display
const SUIT_COLORS: Record<string, string> = {
  's': '#9CA3AF', // gray
  'h': '#EF4444', // red
  'd': '#3B82F6', // blue
  'c': '#22C55E', // green
};

export function LabelingCanvas({
  imageUrl,
  boxes,
  selectedBoxId,
  onBoxSelect,
  onBoxCreate,
  onBoxUpdate,
  onBoxDelete,
  imageWidth,
  imageHeight,
  mode,
}: LabelingCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState<{ x: number; y: number } | null>(null);
  const [currentDraw, setCurrentDraw] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
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

  // Calculate scale to fit container
  useEffect(() => {
    if (!containerRef.current || imageWidth === 0) return;

    const containerWidth = containerRef.current.clientWidth;
    const newScale = Math.min(1, containerWidth / imageWidth);
    setScale(newScale);
  }, [imageWidth, containerRef.current?.clientWidth]);

  // Redraw canvas
  const redraw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    const img = imageRef.current;
    
    if (!canvas || !ctx || !img) return;

    // Set canvas size
    canvas.width = imageWidth * scale;
    canvas.height = imageHeight * scale;

    // Clear and draw image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Draw boxes
    boxes.forEach(box => {
      const x = box.x * scale;
      const y = box.y * scale;
      const w = box.width * scale;
      const h = box.height * scale;
      
      const isSelected = box.id === selectedBoxId;
      
      // Box border
      ctx.strokeStyle = isSelected ? '#22C55E' : 
        box.className ? SUIT_COLORS[box.className[1]] || '#FCD34D' : '#FCD34D';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.strokeRect(x, y, w, h);
      
      // Fill with transparency
      ctx.fillStyle = isSelected ? 'rgba(34, 197, 94, 0.2)' : 'rgba(252, 211, 77, 0.1)';
      ctx.fillRect(x, y, w, h);
      
      // Label
      if (box.className) {
        ctx.fillStyle = isSelected ? '#22C55E' : '#FCD34D';
        ctx.font = 'bold 14px monospace';
        ctx.fillText(box.className, x + 4, y + 16);
      }
      
      // Confidence
      if (box.confidence !== undefined && box.confidence < 1) {
        ctx.fillStyle = '#9CA3AF';
        ctx.font = '10px sans-serif';
        ctx.fillText(`${(box.confidence * 100).toFixed(0)}%`, x + 4, y + h - 4);
      }
    });

    // Draw current drawing box
    if (currentDraw) {
      ctx.strokeStyle = '#22C55E';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(
        currentDraw.x * scale,
        currentDraw.y * scale,
        currentDraw.w * scale,
        currentDraw.h * scale
      );
      ctx.setLineDash([]);
    }
  }, [boxes, selectedBoxId, scale, imageWidth, imageHeight, currentDraw]);

  // Redraw on changes
  useEffect(() => {
    redraw();
  }, [redraw]);

  // Get mouse position relative to image
  const getMousePos = (e: React.MouseEvent): { x: number; y: number } => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / scale,
      y: (e.clientY - rect.top) / scale,
    };
  };

  // Find box at position
  const findBoxAt = (x: number, y: number): BoundingBox | null => {
    for (const box of boxes) {
      if (
        x >= box.x &&
        x <= box.x + box.width &&
        y >= box.y &&
        y <= box.y + box.height
      ) {
        return box;
      }
    }
    return null;
  };

  // Mouse handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    const pos = getMousePos(e);
    
    if (mode === 'select') {
      const box = findBoxAt(pos.x, pos.y);
      onBoxSelect(box?.id || null);
    } else if (mode === 'draw') {
      setIsDrawing(true);
      setDrawStart(pos);
      setCurrentDraw({ x: pos.x, y: pos.y, w: 0, h: 0 });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !drawStart) return;
    
    const pos = getMousePos(e);
    setCurrentDraw({
      x: Math.min(drawStart.x, pos.x),
      y: Math.min(drawStart.y, pos.y),
      w: Math.abs(pos.x - drawStart.x),
      h: Math.abs(pos.y - drawStart.y),
    });
  };

  const handleMouseUp = () => {
    if (isDrawing && currentDraw && currentDraw.w > 10 && currentDraw.h > 10) {
      onBoxCreate({
        x: currentDraw.x,
        y: currentDraw.y,
        width: currentDraw.w,
        height: currentDraw.h,
      });
    }
    
    setIsDrawing(false);
    setDrawStart(null);
    setCurrentDraw(null);
  };

  // Keyboard handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedBoxId) {
          onBoxDelete(selectedBoxId);
        }
      } else if (e.key === 'Escape') {
        onBoxSelect(null);
        setIsDrawing(false);
        setCurrentDraw(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedBoxId, onBoxDelete, onBoxSelect]);

  if (!imageUrl) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <div className="text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p>Capture a screenshot to start labeling</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="glass rounded-xl overflow-hidden">
      {/* Canvas */}
      <div className="relative bg-gray-900">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className={`${mode === 'draw' ? 'cursor-crosshair' : 'cursor-pointer'}`}
        />
      </div>

      {/* Info bar */}
      <div className="px-4 py-2 bg-gray-800/50 flex items-center justify-between text-sm">
        <div className="text-gray-400">
          {imageWidth} x {imageHeight} px
          {scale < 1 && <span className="ml-2">({(scale * 100).toFixed(0)}% zoom)</span>}
        </div>
        <div className="text-gray-400">
          {boxes.length} boxes
          {selectedBoxId && (
            <span className="ml-2 text-poker-green-400">• 1 selected</span>
          )}
        </div>
      </div>
    </div>
  );
}
