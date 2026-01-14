import { useState } from 'react';

interface DetectedCard {
  card: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface ValidationModeProps {
  detectedCards: DetectedCard[];
  imageUrl: string | null;
  onCorrect: (index: number, correctCard: string) => void;
  onValidate: () => void;
  isValidating: boolean;
  modelReady: boolean;
}

const SUIT_DISPLAY: Record<string, { symbol: string; color: string }> = {
  s: { symbol: '♠', color: 'text-gray-300' },
  h: { symbol: '♥', color: 'text-red-500' },
  d: { symbol: '♦', color: 'text-blue-400' },
  c: { symbol: '♣', color: 'text-green-400' },
};

export function ValidationMode({
  detectedCards,
  imageUrl,
  onCorrect,
  onValidate,
  isValidating,
  modelReady,
}: ValidationModeProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Calculate accuracy metrics
  const avgConfidence = detectedCards.length > 0
    ? detectedCards.reduce((sum, c) => sum + c.confidence, 0) / detectedCards.length
    : 0;

  const highConfidenceCount = detectedCards.filter(c => c.confidence > 0.8).length;

  if (!modelReady) {
    return (
      <div className="glass rounded-xl p-4">
        <h3 className="text-lg font-semibold text-white mb-4">Model Validation</h3>
        <div className="text-center py-8">
          <svg className="w-12 h-12 mx-auto mb-3 text-gray-500 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <p className="text-gray-500">No trained model available</p>
          <p className="text-gray-600 text-sm mt-1">Train a model first to validate detections</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Model Validation</h3>
        <button
          onClick={onValidate}
          disabled={isValidating || !imageUrl}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
        >
          {isValidating ? 'Detecting...' : 'Run Detection'}
        </button>
      </div>

      {/* Metrics */}
      {detectedCards.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="bg-gray-800/50 rounded-lg p-2 text-center">
            <div className="text-xl font-bold text-white">{detectedCards.length}</div>
            <div className="text-xs text-gray-400">Detected</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-2 text-center">
            <div className={`text-xl font-bold ${avgConfidence > 0.7 ? 'text-green-400' : 'text-amber-400'}`}>
              {(avgConfidence * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-400">Avg Conf</div>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-2 text-center">
            <div className="text-xl font-bold text-green-400">{highConfidenceCount}</div>
            <div className="text-xs text-gray-400">High Conf</div>
          </div>
        </div>
      )}

      {/* Detected cards list */}
      {detectedCards.length > 0 ? (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {detectedCards.map((card, index) => {
            const suit = SUIT_DISPLAY[card.card[1]] || { symbol: '', color: 'text-white' };
            const isSelected = selectedIndex === index;
            
            return (
              <div
                key={index}
                onClick={() => setSelectedIndex(isSelected ? null : index)}
                className={`
                  flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors
                  ${isSelected 
                    ? 'bg-poker-green-500/20 border border-poker-green-500/50' 
                    : 'bg-gray-800/50 hover:bg-gray-700/50'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  {/* Card display */}
                  <div className={`text-xl font-bold font-mono ${suit.color}`}>
                    {card.card[0]}{suit.symbol}
                  </div>
                  
                  {/* Confidence bar */}
                  <div className="w-20">
                    <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          card.confidence > 0.8 
                            ? 'bg-green-500' 
                            : card.confidence > 0.5 
                              ? 'bg-amber-500' 
                              : 'bg-red-500'
                        }`}
                        style={{ width: `${card.confidence * 100}%` }}
                      />
                    </div>
                    <div className="text-[10px] text-gray-500 mt-0.5">
                      {(card.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  {card.confidence < 0.8 && (
                    <span className="text-xs text-amber-400">Low conf</span>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      // Would open card selector to correct
                    }}
                    className="text-xs text-gray-400 hover:text-white"
                  >
                    Correct
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-6 text-gray-500">
          {imageUrl ? (
            <>
              <p>No cards detected</p>
              <p className="text-sm mt-1">Click "Run Detection" to test the model</p>
            </>
          ) : (
            <p>Capture an image to validate detections</p>
          )}
        </div>
      )}

      {/* Validation tips */}
      <div className="mt-4 pt-3 border-t border-gray-700/50 text-xs text-gray-500">
        <p>💡 Tips:</p>
        <ul className="mt-1 space-y-0.5 ml-4">
          <li>• Detections with {'<'}80% confidence may need correction</li>
          <li>• Click a card to see its location</li>
          <li>• Corrected detections can be saved to improve the model</li>
        </ul>
      </div>
    </div>
  );
}
