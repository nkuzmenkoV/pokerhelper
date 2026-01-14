import { useState, useEffect } from 'react';

interface BoundingBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  classId?: number;
  className?: string;
  region_type?: string;
  position_index?: number;
}

interface QuickLabelBarProps {
  boxes: BoundingBox[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
  onLabelApplied: (boxId: string) => void;
  pendingRank: string | null;
  sessionCount: number;
  isAutoMode: boolean;
  onAutoModeToggle: (enabled: boolean) => void;
}

const SUIT_DISPLAY: Record<string, { symbol: string; color: string }> = {
  s: { symbol: '♠', color: 'text-gray-300' },
  h: { symbol: '♥', color: 'text-red-500' },
  d: { symbol: '♦', color: 'text-blue-400' },
  c: { symbol: '♣', color: 'text-green-400' },
};

export function QuickLabelBar({
  boxes,
  currentIndex,
  onIndexChange,
  onLabelApplied,
  pendingRank,
  sessionCount,
  isAutoMode,
  onAutoModeToggle,
}: QuickLabelBarProps) {
  const unlabeledBoxes = boxes.filter(b => b.classId === undefined);
  const labeledCount = boxes.length - unlabeledBoxes.length;
  const currentBox = boxes[currentIndex];

  // Auto-advance to next unlabeled box when a label is applied
  useEffect(() => {
    if (currentBox?.classId !== undefined) {
      const nextUnlabeled = boxes.findIndex((b, i) => i > currentIndex && b.classId === undefined);
      if (nextUnlabeled !== -1) {
        onIndexChange(nextUnlabeled);
      } else {
        // Try from beginning
        const fromStart = boxes.findIndex(b => b.classId === undefined);
        if (fromStart !== -1) {
          onIndexChange(fromStart);
        }
      }
    }
  }, [currentBox?.classId]);

  return (
    <div className="glass rounded-xl p-3">
      {/* Progress and status */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Progress */}
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Progress:</span>
            <span className="text-white font-medium">
              {labeledCount} / {boxes.length}
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-poker-green-500 transition-all"
              style={{ width: `${boxes.length > 0 ? (labeledCount / boxes.length) * 100 : 0}%` }}
            />
          </div>
        </div>
        
        {/* Session counter */}
        <div className="text-sm">
          <span className="text-gray-400">Session:</span>
          <span className="text-poker-green-400 font-bold ml-1">{sessionCount}</span>
          <span className="text-gray-500 ml-1">images</span>
        </div>
      </div>

      {/* Current box indicator */}
      {boxes.length > 0 ? (
        <div className="flex items-center gap-4">
          {/* Navigation */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => onIndexChange(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
              className="p-1 rounded hover:bg-gray-700 disabled:opacity-30"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            <span className="text-sm text-gray-300 min-w-[3rem] text-center">
              {currentIndex + 1} / {boxes.length}
            </span>
            
            <button
              onClick={() => onIndexChange(Math.min(boxes.length - 1, currentIndex + 1))}
              disabled={currentIndex >= boxes.length - 1}
              className="p-1 rounded hover:bg-gray-700 disabled:opacity-30"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>

          {/* Current box info */}
          <div className="flex-1 flex items-center gap-3">
            {currentBox && (
              <>
                {/* Region type */}
                <div className={`px-2 py-0.5 rounded text-xs font-medium ${
                  currentBox.region_type === 'hero' 
                    ? 'bg-amber-500/20 text-amber-400' 
                    : currentBox.region_type === 'board'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {currentBox.region_type || 'Unknown'}
                  {currentBox.position_index !== undefined && ` #${currentBox.position_index + 1}`}
                </div>
                
                {/* Label status */}
                {currentBox.className ? (
                  <div className="flex items-center gap-1">
                    <span className="text-gray-400 text-sm">Labeled:</span>
                    <span className={`text-xl font-bold ${SUIT_DISPLAY[currentBox.className[1]]?.color || 'text-white'}`}>
                      {currentBox.className[0]}
                      {SUIT_DISPLAY[currentBox.className[1]]?.symbol}
                    </span>
                  </div>
                ) : (
                  <span className="text-amber-400 text-sm animate-pulse">
                    ⚡ Press rank then suit to label
                  </span>
                )}
              </>
            )}
          </div>

          {/* Pending rank indicator */}
          {pendingRank && (
            <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/20 rounded animate-pulse">
              <span className="text-amber-400 font-bold text-xl">{pendingRank}</span>
              <span className="text-amber-300 text-sm">+ suit?</span>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-gray-500 text-sm py-2">
          No regions detected. Use Auto-Detect or draw boxes manually.
        </div>
      )}

      {/* Quick actions */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-700/50">
        {/* Jump to unlabeled */}
        <button
          onClick={() => {
            const idx = boxes.findIndex(b => b.classId === undefined);
            if (idx !== -1) onIndexChange(idx);
          }}
          disabled={unlabeledBoxes.length === 0}
          className="text-xs text-gray-400 hover:text-white disabled:opacity-30"
        >
          → Jump to next unlabeled ({unlabeledBoxes.length} left)
        </button>
        
        {/* Auto mode toggle */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={isAutoMode}
            onChange={(e) => onAutoModeToggle(e.target.checked)}
            className="w-3 h-3 rounded border-gray-600 bg-gray-700 text-poker-green-500"
          />
          <span className="text-xs text-gray-400">Auto-advance</span>
        </label>
      </div>
    </div>
  );
}
