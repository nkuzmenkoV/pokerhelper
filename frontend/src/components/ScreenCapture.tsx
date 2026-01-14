import React from 'react';

interface ScreenCaptureProps {
  isCapturing: boolean;
  onStart: () => void;
  onStop: () => void;
  videoRef: React.RefObject<HTMLVideoElement>;
}

export function ScreenCapture({ isCapturing, onStart, onStop, videoRef }: ScreenCaptureProps) {
  return (
    <div className="relative">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Screen Capture</h2>
          {isCapturing && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              Live
            </span>
          )}
        </div>
        
        {isCapturing ? (
          <button
            onClick={onStop}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
            Stop Capture
          </button>
        ) : (
          <button
            onClick={onStart}
            className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Start Capture
          </button>
        )}
      </div>

      <div className="relative aspect-video bg-gray-900/50">
        {/* Video element is always rendered to maintain ref */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-contain ${isCapturing ? 'block' : 'hidden'}`}
        />
        
        {/* Placeholder when not capturing */}
        {!isCapturing && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
            <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className="text-lg font-medium">No capture active</p>
            <p className="text-sm mt-2 opacity-70">Click "Start Capture" and select the PokerOK window</p>
          </div>
        )}
      </div>
    </div>
  );
}
