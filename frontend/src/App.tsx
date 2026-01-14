import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useWebSocket } from './hooks/useWebSocket';
import { useScreenCapture } from './hooks/useScreenCapture';
import { ScreenCapture } from './components/ScreenCapture';
import { ActionPanel } from './components/ActionPanel';
import { HandRange } from './components/HandRange';
import { GameInfo } from './components/GameInfo';
import { ConnectionStatus } from './components/ConnectionStatus';
import { HUDOverlay } from './components/HUDOverlay';
import { EquityDisplay } from './components/EquityDisplay';
import type { GameState, Recommendation } from './types/poker';

function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [autoAnalyze, setAutoAnalyze] = useState(false);
  const [fps, setFps] = useState(2);
  const [showDetailedHUD, setShowDetailedHUD] = useState(true);

  const { status, lastResponse, sendFrame, connect, disconnect } = useWebSocket();
  const { isCapturing, startCapture, stopCapture, captureFrame, videoRef } = useScreenCapture();

  // Process WebSocket responses
  useEffect(() => {
    if (lastResponse?.status === 'success') {
      if (lastResponse.gameState) {
        setGameState(lastResponse.gameState as unknown as GameState);
      }
      if (lastResponse.recommendations) {
        setRecommendation(lastResponse.recommendations as unknown as Recommendation);
      }
    }
  }, [lastResponse]);

  // Auto-analyze loop
  useEffect(() => {
    if (!autoAnalyze || !isCapturing || status !== 'connected') {
      return;
    }

    const interval = setInterval(() => {
      const frame = captureFrame();
      if (frame) {
        sendFrame(frame);
      }
    }, 1000 / fps);

    return () => clearInterval(interval);
  }, [autoAnalyze, isCapturing, status, fps, captureFrame, sendFrame]);

  // Manual analyze
  const handleAnalyze = useCallback(() => {
    const frame = captureFrame();
    if (frame) {
      sendFrame(frame);
    }
  }, [captureFrame, sendFrame]);

  // Connect on mount
  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white font-display">
              Poker MTT Helper
            </h1>
            <p className="text-gray-400 mt-1">
              Real-time poker table analysis with GTO recommendations
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link 
              to="/training" 
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm font-medium transition-colors"
            >
              🎯 Train Model
            </Link>
            <ConnectionStatus status={status} />
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Screen Capture */}
        <div className="lg:col-span-2 space-y-6">
          <ScreenCapture
            isCapturing={isCapturing}
            onStart={startCapture}
            onStop={stopCapture}
            videoRef={videoRef}
          />

          {/* Controls */}
          <div className="glass rounded-xl p-4">
            <div className="flex flex-wrap items-center gap-4">
              <button
                onClick={handleAnalyze}
                disabled={!isCapturing || status !== 'connected'}
                className="px-6 py-2.5 bg-poker-green-600 hover:bg-poker-green-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors"
              >
                Analyze Frame
              </button>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoAnalyze}
                  onChange={(e) => setAutoAnalyze(e.target.checked)}
                  disabled={!isCapturing}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-poker-green-500 focus:ring-poker-green-500"
                />
                <span className="text-gray-300">Auto-analyze</span>
              </label>

              <div className="flex items-center gap-2">
                <label className="text-gray-400 text-sm">FPS:</label>
                <select
                  value={fps}
                  onChange={(e) => setFps(Number(e.target.value))}
                  className="bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-white"
                >
                  <option value={1}>1</option>
                  <option value={2}>2</option>
                  <option value={5}>5</option>
                </select>
              </div>

              {lastResponse?.status === 'no_table_detected' && (
                <span className="text-amber-400 text-sm">
                  ⚠ No poker table detected
                </span>
              )}
            </div>
          </div>

          {/* Game Info */}
          {gameState && (
            <GameInfo gameState={gameState} />
          )}

          {/* HUD Overlay */}
          {gameState && gameState.players.length > 0 && (
            <HUDOverlay
              players={gameState.players.map(p => ({
                playerId: `seat_${p.seat}`,
                playerName: p.name || `Seat ${p.seat}`,
                hands: 0, // Will be populated from HUD tracker
                vpip: 25, // Placeholder
                pfr: 18,  // Placeholder
                threeBet: 7, // Placeholder
                af: 2.5,  // Placeholder
                position: p.position,
                isHero: p.isHero,
              }))}
              showDetailed={showDetailedHUD}
            />
          )}
        </div>

        {/* Right Column - Recommendations */}
        <div className="space-y-6">
          {/* Action Panel */}
          <ActionPanel recommendation={recommendation} />

          {/* Hand Range Matrix */}
          {recommendation && (
            <HandRange
              position={recommendation.position}
              stackBb={recommendation.stackBb}
              isPushFold={recommendation.isPushFold}
              heroHand={recommendation.hand}
            />
          )}

          {/* Equity Calculator */}
          {gameState && gameState.heroCards.length === 2 && (
            <EquityDisplay
              heroCards={gameState.heroCards}
              boardCards={gameState.boardCards}
            />
          )}

          {/* Notes */}
          {recommendation?.notes && recommendation.notes.length > 0 && (
            <div className="glass rounded-xl p-4">
              <h3 className="text-lg font-semibold text-white mb-3">Notes</h3>
              <ul className="space-y-2">
                {recommendation.notes.map((note, index) => (
                  <li key={index} className="text-gray-300 text-sm flex items-start gap-2">
                    <span className="text-poker-green-400">•</span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* HUD Toggle */}
          <div className="glass rounded-xl p-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showDetailedHUD}
                onChange={(e) => setShowDetailedHUD(e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-poker-green-500"
              />
              <span className="text-gray-300 text-sm">Show detailed HUD stats</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
