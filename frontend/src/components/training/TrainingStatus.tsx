import { useState, useEffect } from 'react';

interface TrainingProgress {
  status: 'idle' | 'preparing' | 'training' | 'completed' | 'failed' | 'cancelled';
  current_epoch: number;
  total_epochs: number;
  progress_pct: number;
  current_loss: number;
  best_loss: number | null;
  metrics: Record<string, number>;
  started_at: string | null;
  completed_at: string | null;
  error_message: string;
  model_path: string;
}

interface TrainingConfig {
  epochs: number;
  batch_size: number;
  img_size: number;
  model_size: string;
  device: string;
}

interface TrainingStatusProps {
  progress: TrainingProgress | null;
  config: TrainingConfig | null;
  onStart: () => void;
  onCancel: () => void;
  onConfigChange: (config: Partial<TrainingConfig>) => void;
  canStart: boolean;
}

const STATUS_COLORS: Record<string, { bg: string; text: string }> = {
  idle: { bg: 'bg-gray-500', text: 'text-gray-400' },
  preparing: { bg: 'bg-amber-500', text: 'text-amber-400' },
  training: { bg: 'bg-blue-500', text: 'text-blue-400' },
  completed: { bg: 'bg-green-500', text: 'text-green-400' },
  failed: { bg: 'bg-red-500', text: 'text-red-400' },
  cancelled: { bg: 'bg-gray-500', text: 'text-gray-400' },
};

const STATUS_LABELS: Record<string, string> = {
  idle: 'Ready',
  preparing: 'Preparing...',
  training: 'Training',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

export function TrainingStatus({
  progress,
  config,
  onStart,
  onCancel,
  onConfigChange,
  canStart,
}: TrainingStatusProps) {
  const [showConfig, setShowConfig] = useState(false);
  
  const status = progress?.status || 'idle';
  const isTraining = status === 'training' || status === 'preparing';
  const statusColor = STATUS_COLORS[status] || STATUS_COLORS.idle;

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Model Training</h3>
        <div className={`flex items-center gap-2 px-2 py-1 rounded-full ${statusColor.bg}/20`}>
          <div className={`w-2 h-2 rounded-full ${statusColor.bg} ${isTraining ? 'animate-pulse' : ''}`} />
          <span className={`text-xs font-medium ${statusColor.text}`}>
            {STATUS_LABELS[status]}
          </span>
        </div>
      </div>

      {/* Progress display during training */}
      {isTraining && progress && (
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-400">
              Epoch {progress.current_epoch} / {progress.total_epochs}
            </span>
            <span className="text-white font-medium">
              {progress.progress_pct.toFixed(1)}%
            </span>
          </div>
          <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-500"
              style={{ width: `${progress.progress_pct}%` }}
            />
          </div>
          
          {/* Loss info */}
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-800/50 rounded p-2">
              <span className="text-gray-400">Current Loss:</span>
              <span className="text-white ml-2 font-mono">
                {progress.current_loss.toFixed(4)}
              </span>
            </div>
            {progress.best_loss && (
              <div className="bg-gray-800/50 rounded p-2">
                <span className="text-gray-400">Best Loss:</span>
                <span className="text-green-400 ml-2 font-mono">
                  {progress.best_loss.toFixed(4)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Completed status */}
      {status === 'completed' && progress && (
        <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <div className="text-green-400 font-medium mb-1">Training Complete!</div>
          <div className="text-sm text-gray-400">
            Best loss: <span className="text-green-400 font-mono">{progress.best_loss?.toFixed(4)}</span>
          </div>
          {progress.model_path && (
            <div className="text-xs text-gray-500 mt-1 truncate">
              Model: {progress.model_path}
            </div>
          )}
        </div>
      )}

      {/* Failed status */}
      {status === 'failed' && progress && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="text-red-400 font-medium mb-1">Training Failed</div>
          <div className="text-sm text-red-300/70">
            {progress.error_message || 'Unknown error'}
          </div>
        </div>
      )}

      {/* Configuration */}
      {config && !isTraining && (
        <div className="mb-4">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="text-sm text-gray-400 hover:text-white flex items-center gap-1"
          >
            <svg
              className={`w-4 h-4 transition-transform ${showConfig ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            Configuration
          </button>
          
          {showConfig && (
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Epochs</label>
                <input
                  type="number"
                  value={config.epochs}
                  onChange={(e) => onConfigChange({ epochs: Number(e.target.value) })}
                  className="w-full bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-white"
                  min={10}
                  max={500}
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Batch Size</label>
                <select
                  value={config.batch_size}
                  onChange={(e) => onConfigChange({ batch_size: Number(e.target.value) })}
                  className="w-full bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-white"
                >
                  <option value={8}>8</option>
                  <option value={16}>16</option>
                  <option value={32}>32</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Model Size</label>
                <select
                  value={config.model_size}
                  onChange={(e) => onConfigChange({ model_size: e.target.value })}
                  className="w-full bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-white"
                >
                  <option value="n">Nano (fastest)</option>
                  <option value="s">Small</option>
                  <option value="m">Medium</option>
                  <option value="l">Large</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Device</label>
                <select
                  value={config.device}
                  onChange={(e) => onConfigChange({ device: e.target.value })}
                  className="w-full bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-white"
                >
                  <option value="cpu">CPU</option>
                  <option value="0">GPU 0</option>
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        {isTraining ? (
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg font-medium transition-colors"
          >
            Cancel Training
          </button>
        ) : (
          <button
            onClick={onStart}
            disabled={!canStart}
            className="flex-1 px-4 py-2 bg-poker-green-600 hover:bg-poker-green-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors"
          >
            Start Training
          </button>
        )}
      </div>

      {!canStart && status === 'idle' && (
        <div className="mt-2 text-xs text-gray-500 text-center">
          Need at least 10 labeled images to start training
        </div>
      )}
    </div>
  );
}
