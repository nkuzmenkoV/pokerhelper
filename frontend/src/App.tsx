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
  const [, setLastUpdate] = useState<Date | null>(null);

  const { status, lastResponse, sendFrame, connect, disconnect } = useWebSocket();
  const { isCapturing, startCapture, stopCapture, captureFrame, videoRef } = useScreenCapture();

  // Process WebSocket responses
  useEffect(() => {
    if (lastResponse?.status === 'success') {
      if (lastResponse.gameState) {
        setGameState(lastResponse.gameState as unknown as GameState);
        setLastUpdate(new Date());
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
    <div className="min-h-screen">
      {/* Top Navigation Bar */}
      <nav className="glass-elevated sticky top-0 z-50 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-xl font-bold glow-green">
                ♠
              </div>
              <div>
                <h1 className="text-lg font-semibold text-white">Poker MTT Helper</h1>
                <p className="text-xs text-gray-500">GTO Assistant</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Quick Stats */}
            {gameState && (
              <div className="hidden md:flex items-center gap-6 px-4 py-1.5 rounded-lg bg-black/30">
                <div className="text-center">
                  <div className="text-xs text-gray-500">Stack</div>
                  <div className="text-sm font-semibold text-white">
                    {gameState.heroStackBb?.toFixed(1) || '—'} BB
                  </div>
                </div>
                <div className="w-px h-8 bg-gray-700"></div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Pot</div>
                  <div className="text-sm font-semibold text-white">
                    {gameState.potBb?.toFixed(1) || '—'} BB
                  </div>
                </div>
                <div className="w-px h-8 bg-gray-700"></div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Position</div>
                  <div className={`position-badge ${gameState.heroPosition?.toLowerCase() || ''}`}>
                    {gameState.heroPosition || '—'}
                  </div>
                </div>
              </div>
            )}

            <Link 
              to="/training" 
              className="flex items-center gap-2 px-4 py-2 bg-purple-600/80 hover:bg-purple-500/80 rounded-lg text-sm font-medium transition-all hover:scale-105"
            >
              <span>🎯</span>
              <span className="hidden sm:inline">Training</span>
            </Link>
            
            <ConnectionStatus status={status} />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          
          {/* Left Column - Screen Capture & Controls */}
          <div className="xl:col-span-8 space-y-4">
            {/* Screen Capture Card */}
            <div className="glass-elevated rounded-2xl overflow-hidden">
              <ScreenCapture
                isCapturing={isCapturing}
                onStart={startCapture}
                onStop={stopCapture}
                videoRef={videoRef}
              />
              
              {/* Controls Bar */}
              <div className="px-4 py-3 border-t border-white/5 flex flex-wrap items-center gap-4">
                <button
                  onClick={handleAnalyze}
                  disabled={!isCapturing || status !== 'connected'}
                  className="btn-action btn-raise disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
                >
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Analyze
                  </span>
                </button>

                <div className="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-black/20">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoAnalyze}
                      onChange={(e) => setAutoAnalyze(e.target.checked)}
                      disabled={!isCapturing}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-green-600"></div>
                  </label>
                  <span className="text-sm text-gray-400">Auto</span>
                </div>

                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/20">
                  <span className="text-xs text-gray-500">FPS</span>
                  <select
                    value={fps}
                    onChange={(e) => setFps(Number(e.target.value))}
                    className="bg-transparent border-none text-sm text-white focus:ring-0 cursor-pointer"
                  >
                    <option value={1} className="bg-gray-800">1</option>
                    <option value={2} className="bg-gray-800">2</option>
                    <option value={5} className="bg-gray-800">5</option>
                  </select>
                </div>

                {lastResponse?.status === 'no_table_detected' && (
                  <div className="flex items-center gap-2 text-amber-400 text-sm animate-fade-in">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    No table detected
                  </div>
                )}
              </div>
            </div>

            {/* Game Info & HUD */}
            {gameState && (
              <div className="animate-slide-up">
                <GameInfo gameState={gameState} />
              </div>
            )}

            {gameState && gameState.players && gameState.players.length > 0 && (
              <div className="glass rounded-xl p-4 animate-slide-up">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Player Stats</h3>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={showDetailedHUD}
                      onChange={(e) => setShowDetailedHUD(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4 bg-gray-700 rounded-full peer peer-checked:after:translate-x-4 peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-green-600 relative"></div>
                    <span className="text-xs text-gray-500">Detailed</span>
                  </label>
                </div>
                <HUDOverlay
                  players={gameState.players.map(p => ({
                    playerId: `seat_${p.seat}`,
                    playerName: p.name || `Seat ${p.seat}`,
                    hands: 0,
                    vpip: 25,
                    pfr: 18,
                    threeBet: 7,
                    af: 2.5,
                    position: p.position,
                    isHero: p.isHero,
                  }))}
                  showDetailed={showDetailedHUD}
                />
              </div>
            )}
          </div>

          {/* Right Column - Recommendations */}
          <div className="xl:col-span-4 space-y-4">
            {/* Main Action Panel */}
            <ActionPanel recommendation={recommendation} />

            {/* Equity Display */}
            {gameState && gameState.heroCards && gameState.heroCards.length === 2 && (
              <div className="animate-slide-up">
                <EquityDisplay
                  heroCards={gameState.heroCards}
                  boardCards={gameState.boardCards || []}
                />
              </div>
            )}

            {/* Hand Range Matrix */}
            {recommendation && (
              <div className="animate-slide-up">
                <HandRange
                  position={recommendation.position}
                  stackBb={recommendation.stackBb}
                  isPushFold={recommendation.isPushFold}
                  heroHand={recommendation.hand}
                />
              </div>
            )}

            {/* Notes Panel */}
            {recommendation?.notes && recommendation.notes.length > 0 && (
              <div className="glass rounded-xl p-4 animate-slide-up">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Analysis Notes
                </h3>
                <ul className="space-y-2">
                  {recommendation.notes.filter(n => n).map((note, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-300">
                      <span className="text-green-500 mt-0.5">→</span>
                      <span>{note}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Quick Help */}
            <div className="glass rounded-xl p-4">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Quick Guide</h3>
              <div className="space-y-2 text-xs text-gray-500">
                <p>1. Click <strong className="text-gray-400">Start Capture</strong> and select PokerOK window</p>
                <p>2. Enable <strong className="text-gray-400">Auto</strong> for continuous analysis</p>
                <p>3. Follow the recommended action</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-8 py-4">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between text-xs text-gray-600">
          <span>Poker MTT Helper v1.0</span>
          <span>Use responsibly. For educational purposes only.</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
