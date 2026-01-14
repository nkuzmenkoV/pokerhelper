import { useState, useCallback, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  CardSelector,
  LabelingCanvas,
  DatasetProgress,
  TrainingStatus,
  ValidationMode,
  PositionCalibration,
  QuickLabelBar,
  CLASS_TO_ID,
} from '../components/training';

interface BoundingBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  classId?: number;
  className?: string;
  confidence?: number;
  region_type?: string;
  position_index?: number;
}

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

interface DatasetStats {
  total_images: number;
  total_boxes: number;
  cards_count: Record<string, number>;
  coverage: number;
  missing_cards: string[];
  balanced: boolean;
}

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

type TabType = 'label' | 'calibrate' | 'validate';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function TrainingPage() {
  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>('label');
  
  // Screen capture state
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  
  // Labeling state
  const [boxes, setBoxes] = useState<BoundingBox[]>([]);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [currentBoxIndex, setCurrentBoxIndex] = useState(0);
  const [selectedCard, setSelectedCard] = useState<string | null>(null);
  const [pendingRank, setPendingRank] = useState<string | null>(null);
  const [mode, setMode] = useState<'select' | 'draw'>('select');
  const [labeledCards, setLabeledCards] = useState<Set<string>>(new Set());
  
  // Auto mode state
  const [isAutoCapture, setIsAutoCapture] = useState(false);
  const [autoCaptureInterval, setAutoCaptureInterval] = useState(3);
  const [autoAdvance, setAutoAdvance] = useState(true);
  const [sessionCount, setSessionCount] = useState(0);
  
  // Layout/calibration state
  const [layout, setLayout] = useState<Layout | null>(null);
  const [presets, setPresets] = useState<Record<string, Layout>>({});
  
  // Dataset state
  const [datasetStats, setDatasetStats] = useState<DatasetStats | null>(null);
  
  // Training state
  const [trainingProgress, setTrainingProgress] = useState<TrainingProgress | null>(null);
  const [trainingConfig, setTrainingConfig] = useState<TrainingConfig | null>(null);
  
  // Validation state
  const [detectedCards, setDetectedCards] = useState<any[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [modelReady, setModelReady] = useState(false);

  // Polling for training status
  useEffect(() => {
    const interval = setInterval(() => {
      if (trainingProgress?.status === 'training' || trainingProgress?.status === 'preparing') {
        fetchTrainingStatus();
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [trainingProgress?.status]);

  // Initial data fetch
  useEffect(() => {
    fetchDatasetStats();
    fetchTrainingConfig();
    fetchTrainingStatus();
    checkModelAvailable();
    fetchLayout();
    fetchPresets();
  }, []);

  // Auto-capture interval
  useEffect(() => {
    if (!isAutoCapture || !isCapturing) return;
    
    const interval = setInterval(() => {
      captureFrame();
    }, autoCaptureInterval * 1000);
    
    return () => clearInterval(interval);
  }, [isAutoCapture, isCapturing, autoCaptureInterval]);

  // Auto-detect after capture
  useEffect(() => {
    if (capturedImage && boxes.length === 0) {
      autoDetect();
    }
  }, [capturedImage]);

  // Sync selected box with currentBoxIndex
  useEffect(() => {
    if (boxes.length > 0 && currentBoxIndex < boxes.length) {
      setSelectedBoxId(boxes[currentBoxIndex].id);
    }
  }, [currentBoxIndex, boxes]);

  // API calls
  const fetchDatasetStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/dataset/stats`);
      const data = await res.json();
      setDatasetStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchTrainingConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/config`);
      const data = await res.json();
      setTrainingConfig(data);
    } catch (err) {
      console.error('Failed to fetch config:', err);
    }
  };

  const fetchTrainingStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/status`);
      const data = await res.json();
      setTrainingProgress(data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  const checkModelAvailable = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/models`);
      const data = await res.json();
      setModelReady(data.models && data.models.length > 0);
    } catch (err) {
      console.error('Failed to check models:', err);
    }
  };

  const fetchLayout = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/layout`);
      const data = await res.json();
      setLayout(data);
    } catch (err) {
      console.error('Failed to fetch layout:', err);
    }
  };

  const fetchPresets = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/layout/presets`);
      const data = await res.json();
      setPresets(data.presets || {});
    } catch (err) {
      console.error('Failed to fetch presets:', err);
    }
  };

  // Screen capture
  const startCapture = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { displaySurface: 'window' } as any,
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsCapturing(true);
      }
      
      stream.getTracks()[0].onended = () => {
        setIsCapturing(false);
        setIsAutoCapture(false);
        if (videoRef.current) {
          videoRef.current.srcObject = null;
        }
      };
    } catch (err) {
      console.error('Screen capture failed:', err);
    }
  };

  const captureFrame = useCallback(() => {
    if (!videoRef.current) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(videoRef.current, 0, 0);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
      setCapturedImage(dataUrl);
      setImageSize({ width: canvas.width, height: canvas.height });
      setBoxes([]);
      setSelectedBoxId(null);
      setCurrentBoxIndex(0);
      setLabeledCards(new Set());
    }
  }, []);

  // Auto-detect cards
  const autoDetect = async () => {
    if (!capturedImage) return;
    
    try {
      const base64Data = capturedImage.split(',')[1];
      const res = await fetch(`${API_BASE}/api/training/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: base64Data,
          use_model: modelReady,
          use_heuristics: true,
          use_positions: true,
        }),
      });
      
      const data = await res.json();
      
      // Convert detected regions to boxes
      const newBoxes: BoundingBox[] = data.regions.map((r: any, idx: number) => ({
        id: `box-${idx}`,
        x: r.x,
        y: r.y,
        width: r.pixel_width,
        height: r.pixel_height,
        classId: r.suggested_class ? CLASS_TO_ID[r.suggested_class] : undefined,
        className: r.suggested_class,
        confidence: r.confidence,
        region_type: r.region_type,
        position_index: r.position_index,
      }));
      
      setBoxes(newBoxes);
      setCurrentBoxIndex(0);
      
      // If all boxes are already labeled (from model), offer to save
      const allLabeled = newBoxes.every(b => b.classId !== undefined);
      if (allLabeled && newBoxes.length > 0 && isAutoCapture) {
        // Auto-save in auto mode
        setTimeout(() => saveToDataset(newBoxes), 500);
      }
    } catch (err) {
      console.error('Auto-detect failed:', err);
    }
  };

  // Box management
  const handleBoxCreate = (box: Omit<BoundingBox, 'id'>) => {
    const newBox: BoundingBox = {
      ...box,
      id: `box-${Date.now()}`,
    };
    setBoxes([...boxes, newBox]);
    setSelectedBoxId(newBox.id);
    setCurrentBoxIndex(boxes.length);
  };

  const handleBoxDelete = (boxId: string) => {
    const newBoxes = boxes.filter(b => b.id !== boxId);
    setBoxes(newBoxes);
    if (selectedBoxId === boxId) {
      setSelectedBoxId(null);
      setCurrentBoxIndex(Math.max(0, currentBoxIndex - 1));
    }
  };

  // Card selection with quick mode support
  const handleCardSelect = useCallback((card: string, classId: number) => {
    setSelectedCard(card);
    
    // Apply to current selected box
    if (selectedBoxId) {
      setBoxes(prev => prev.map(b =>
        b.id === selectedBoxId
          ? { ...b, classId, className: card }
          : b
      ));
      setLabeledCards(prev => new Set([...prev, card]));
      
      // Auto-advance to next unlabeled box
      if (autoAdvance) {
        const currentIdx = boxes.findIndex(b => b.id === selectedBoxId);
        const nextUnlabeled = boxes.findIndex((b, i) => i > currentIdx && b.classId === undefined);
        if (nextUnlabeled !== -1) {
          setCurrentBoxIndex(nextUnlabeled);
        } else {
          // Check if all labeled
          const updatedBoxes = boxes.map(b =>
            b.id === selectedBoxId ? { ...b, classId, className: card } : b
          );
          const allLabeled = updatedBoxes.every(b => b.classId !== undefined);
          if (allLabeled && updatedBoxes.length > 0) {
            // All labeled, auto-save if in auto mode
            if (isAutoCapture) {
              setTimeout(() => saveToDataset(updatedBoxes), 300);
            }
          }
        }
      }
    }
  }, [selectedBoxId, boxes, autoAdvance, isAutoCapture]);

  // Quick select (from keyboard shortcuts in CardSelector)
  const handleQuickSelect = useCallback((card: string, classId: number) => {
    handleCardSelect(card, classId);
  }, [handleCardSelect]);

  // Save to dataset
  const saveToDataset = async (boxesToSave?: BoundingBox[]) => {
    const saveBoxes = boxesToSave || boxes;
    if (!capturedImage || saveBoxes.length === 0) return;
    
    // Filter boxes that have labels
    const labeledBoxes = saveBoxes.filter(b => b.classId !== undefined);
    if (labeledBoxes.length === 0) {
      if (!isAutoCapture) {
        alert('Please label at least one box before saving');
      }
      return;
    }
    
    try {
      const base64Data = capturedImage.split(',')[1];
      const boxesData = labeledBoxes.map(b => ({
        class_id: b.classId!,
        x_center: (b.x + b.width / 2) / imageSize.width,
        y_center: (b.y + b.height / 2) / imageSize.height,
        width: b.width / imageSize.width,
        height: b.height / imageSize.height,
      }));
      
      const res = await fetch(`${API_BASE}/api/training/dataset/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: base64Data,
          boxes: boxesData,
          source: 'browser',
        }),
      });
      
      if (res.ok) {
        // Update session counter
        setSessionCount(prev => prev + 1);
        
        // Clear current state
        setCapturedImage(null);
        setBoxes([]);
        setSelectedBoxId(null);
        setCurrentBoxIndex(0);
        setLabeledCards(new Set());
        
        // Refresh stats
        fetchDatasetStats();
        
        // In auto mode, capture next frame
        if (isAutoCapture && isCapturing) {
          setTimeout(captureFrame, 500);
        }
      } else {
        const error = await res.json();
        if (!isAutoCapture) {
          alert(`Failed to save: ${error.detail}`);
        }
      }
    } catch (err) {
      console.error('Save failed:', err);
    }
  };

  // Layout updates
  const handleLayoutUpdate = (newLayout: Layout) => {
    setLayout(newLayout);
  };

  const handlePositionUpdate = async (regionType: string, index: number, pos: CardPosition) => {
    try {
      await fetch(`${API_BASE}/api/training/layout/position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          region_type: regionType,
          index,
          x: pos.x,
          y: pos.y,
          width: pos.width,
          height: pos.height,
        }),
      });
    } catch (err) {
      console.error('Position update failed:', err);
    }
  };

  const handlePresetSelect = async (presetName: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/training/layout/preset/${presetName}`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setLayout(data.layout);
      }
    } catch (err) {
      console.error('Preset selection failed:', err);
    }
  };

  // Training controls
  const startTraining = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/training/start`, {
        method: 'POST',
      });
      
      if (res.ok) {
        fetchTrainingStatus();
      } else {
        const error = await res.json();
        alert(`Failed to start training: ${error.detail}`);
      }
    } catch (err) {
      console.error('Start training failed:', err);
    }
  };

  const cancelTraining = async () => {
    try {
      await fetch(`${API_BASE}/api/training/cancel`, { method: 'POST' });
      fetchTrainingStatus();
    } catch (err) {
      console.error('Cancel failed:', err);
    }
  };

  const updateConfig = async (updates: Partial<TrainingConfig>) => {
    try {
      const newConfig = { ...trainingConfig, ...updates };
      const res = await fetch(`${API_BASE}/api/training/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig),
      });
      
      if (res.ok) {
        setTrainingConfig(newConfig as TrainingConfig);
      }
    } catch (err) {
      console.error('Config update failed:', err);
    }
  };

  // Validation
  const runValidation = async () => {
    if (!capturedImage) return;
    
    setIsValidating(true);
    try {
      const base64Data = capturedImage.split(',')[1];
      const res = await fetch(`${API_BASE}/api/training/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_data: base64Data,
          use_model: true,
          use_heuristics: false,
          use_positions: false,
        }),
      });
      
      const data = await res.json();
      
      setDetectedCards(data.regions.map((r: any) => ({
        card: r.suggested_class || '??',
        confidence: r.confidence,
        x: r.x,
        y: r.y,
        width: r.pixel_width,
        height: r.pixel_height,
      })));
    } catch (err) {
      console.error('Validation failed:', err);
    }
    setIsValidating(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800/50 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="text-gray-400 hover:text-white">
                ← Back to Game
              </Link>
              <h1 className="text-xl font-bold">Card Recognition Training</h1>
            </div>
            
            {/* Tab switcher */}
            <div className="flex bg-gray-700/50 rounded-lg p-1">
              {(['label', 'calibrate', 'validate'] as TabType[]).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? 'bg-poker-green-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tab === 'label' ? 'Label Data' : tab === 'calibrate' ? 'Calibrate' : 'Validate'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Top Controls */}
        <div className="flex flex-wrap gap-3 mb-4">
          {/* Screen capture controls */}
          <div className="flex gap-2">
            {!isCapturing ? (
              <button
                onClick={startCapture}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Start Screen Capture
              </button>
            ) : (
              <>
                <button
                  onClick={captureFrame}
                  className="px-4 py-2 bg-poker-green-600 hover:bg-poker-green-500 rounded-lg font-medium transition-colors"
                >
                  📸 Capture
                </button>
                <button
                  onClick={() => {
                    setIsCapturing(false);
                    setIsAutoCapture(false);
                  }}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
                >
                  Stop
                </button>
              </>
            )}
          </div>
          
          {/* Auto-capture controls */}
          {isCapturing && activeTab === 'label' && (
            <div className="flex items-center gap-3 px-3 py-2 bg-gray-800/50 rounded-lg">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAutoCapture}
                  onChange={(e) => setIsAutoCapture(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-poker-green-500"
                />
                <span className="text-sm text-gray-300">Auto-capture</span>
              </label>
              {isAutoCapture && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">every</span>
                  <select
                    value={autoCaptureInterval}
                    onChange={(e) => setAutoCaptureInterval(Number(e.target.value))}
                    className="bg-gray-700 border-gray-600 rounded px-2 py-0.5 text-sm text-white"
                  >
                    <option value={2}>2s</option>
                    <option value={3}>3s</option>
                    <option value={5}>5s</option>
                    <option value={10}>10s</option>
                  </select>
                </div>
              )}
            </div>
          )}
          
          {/* Labeling tools */}
          {activeTab === 'label' && capturedImage && (
            <div className="flex gap-2 ml-auto">
              <button
                onClick={() => autoDetect()}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg font-medium transition-colors"
              >
                🔍 Detect
              </button>
              <div className="flex bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setMode('select')}
                  className={`px-3 py-1 rounded text-sm ${mode === 'select' ? 'bg-gray-600' : ''}`}
                >
                  Select
                </button>
                <button
                  onClick={() => setMode('draw')}
                  className={`px-3 py-1 rounded text-sm ${mode === 'draw' ? 'bg-gray-600' : ''}`}
                >
                  Draw
                </button>
              </div>
              <button
                onClick={() => saveToDataset()}
                disabled={boxes.filter(b => b.classId !== undefined).length === 0}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-700 disabled:text-gray-500 rounded-lg font-medium transition-colors"
              >
                💾 Save
              </button>
            </div>
          )}
        </div>

        {/* Quick Label Bar */}
        {activeTab === 'label' && capturedImage && boxes.length > 0 && (
          <div className="mb-4">
            <QuickLabelBar
              boxes={boxes}
              currentIndex={currentBoxIndex}
              onIndexChange={setCurrentBoxIndex}
              onLabelApplied={() => {}}
              pendingRank={pendingRank}
              sessionCount={sessionCount}
              isAutoMode={autoAdvance}
              onAutoModeToggle={setAutoAdvance}
            />
          </div>
        )}

        {/* Hidden video element */}
        <video ref={videoRef} className="hidden" />

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Canvas */}
          <div className="lg:col-span-2 space-y-4">
            {/* Live preview when capturing */}
            {isCapturing && !capturedImage && (
              <div className="glass rounded-xl p-4">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Live Preview</h3>
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  className="w-full rounded-lg"
                />
                <p className="text-sm text-gray-500 mt-2 text-center">
                  Click "Capture" to take a screenshot for labeling
                </p>
              </div>
            )}
            
            {/* Labeling canvas */}
            {activeTab === 'label' && (
              <LabelingCanvas
                imageUrl={capturedImage}
                boxes={boxes}
                selectedBoxId={selectedBoxId}
                onBoxSelect={setSelectedBoxId}
                onBoxCreate={handleBoxCreate}
                onBoxUpdate={() => {}}
                onBoxDelete={handleBoxDelete}
                imageWidth={imageSize.width}
                imageHeight={imageSize.height}
                mode={mode}
              />
            )}
            
            {/* Calibration view */}
            {activeTab === 'calibrate' && (
              <PositionCalibration
                imageUrl={capturedImage}
                imageWidth={imageSize.width}
                imageHeight={imageSize.height}
                layout={layout}
                presets={presets}
                onLayoutUpdate={handleLayoutUpdate}
                onPositionUpdate={handlePositionUpdate}
                onPresetSelect={handlePresetSelect}
              />
            )}
            
            {/* Validation view */}
            {activeTab === 'validate' && capturedImage && (
              <div className="glass rounded-xl overflow-hidden">
                <img src={capturedImage} alt="Captured" className="w-full" />
              </div>
            )}
          </div>

          {/* Right column - Tools */}
          <div className="space-y-4">
            {activeTab === 'label' && (
              <>
                {/* Card selector */}
                <CardSelector
                  selectedCard={selectedCard}
                  onSelect={handleCardSelect}
                  onQuickSelect={handleQuickSelect}
                  labeledCards={labeledCards}
                  disabled={!selectedBoxId}
                />
                
                {/* Dataset progress */}
                <DatasetProgress
                  stats={datasetStats}
                  onRefresh={fetchDatasetStats}
                />
              </>
            )}
            
            {activeTab === 'calibrate' && (
              <div className="glass rounded-xl p-4">
                <h3 className="text-lg font-semibold text-white mb-3">Calibration Tips</h3>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li>• Capture a frame with visible cards</li>
                  <li>• Drag boxes to match card positions</li>
                  <li>• Use corner handles to resize</li>
                  <li>• Select preset for your table type</li>
                  <li>• Positions are saved automatically</li>
                </ul>
              </div>
            )}
            
            {activeTab === 'validate' && (
              <ValidationMode
                detectedCards={detectedCards}
                imageUrl={capturedImage}
                onCorrect={() => {}}
                onValidate={runValidation}
                isValidating={isValidating}
                modelReady={modelReady}
              />
            )}
            
            {/* Training status - always visible */}
            <TrainingStatus
              progress={trainingProgress}
              config={trainingConfig}
              onStart={startTraining}
              onCancel={cancelTraining}
              onConfigChange={updateConfig}
              canStart={(datasetStats?.total_images || 0) >= 10}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
