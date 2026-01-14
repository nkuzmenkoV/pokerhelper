import { useState, useCallback, useRef, useEffect } from 'react';

interface UseScreenCaptureReturn {
  isCapturing: boolean;
  stream: MediaStream | null;
  error: string | null;
  startCapture: () => Promise<void>;
  stopCapture: () => void;
  captureFrame: () => string | null;
  videoRef: React.RefObject<HTMLVideoElement>;
}

export function useScreenCapture(): UseScreenCaptureReturn {
  const [isCapturing, setIsCapturing] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Initialize canvas
  useEffect(() => {
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
  }, []);

  const startCapture = useCallback(async () => {
    try {
      setError(null);
      
      // Request screen capture
      const mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: 'window',
          frameRate: { ideal: 5, max: 10 },
        },
        audio: false,
      });

      // Set up video element
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play();
      }

      setStream(mediaStream);
      setIsCapturing(true);

      // Handle stream end (user stops sharing)
      mediaStream.getVideoTracks()[0].addEventListener('ended', () => {
        stopCapture();
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start screen capture';
      setError(errorMessage);
      console.error('Screen capture error:', err);
    }
  }, []);

  const stopCapture = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setStream(null);
    setIsCapturing(false);
  }, [stream]);

  const captureFrame = useCallback((): string | null => {
    if (!videoRef.current || !canvasRef.current || !isCapturing) {
      return null;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Set canvas size to video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      return null;
    }

    ctx.drawImage(video, 0, 0);

    // Convert to JPEG base64
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    
    // Remove data URL prefix to get just base64
    return dataUrl.split(',')[1];
  }, [isCapturing]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  return {
    isCapturing,
    stream,
    error,
    startCapture,
    stopCapture,
    captureFrame,
    videoRef,
  };
}
