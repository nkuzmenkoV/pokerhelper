import React from 'react';

interface ScreenCaptureProps {
  isCapturing: boolean;
  onStart: () => void;
  onStop: () => void;
  videoRef: React.RefObject<HTMLVideoElement>;
}

export function ScreenCapture({ isCapturing, onStart, onStop, videoRef }: ScreenCaptureProps) {
  return (
    <div className="glass rounded-xl overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Screen Capture</h2>
        
        {isCapturing ? (
          <button
            onClick={onStop}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
            Stop Capture
          </button>
        ) : (
          <button
            onClick={onStart}
            className="px-4 py-2 bg-poker-green-600 hover:bg-poker-green-500 rounded-lg text-sm font-medium transition-colors"
          >
            Start Capture
          </button>
        )}
      </div>

      <div className="relative aspect-video bg-gray-900">
        {isCapturing ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
            <svg className="w-16 h-16 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className="text-lg">Click "Start Capture" to begin</p>
            <p className="text-sm mt-2 opacity-70">Select the PokerOK window when prompted</p>
          </div>
        )}
      </div>
    </div>
  );
}
