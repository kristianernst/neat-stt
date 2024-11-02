import { useState, useRef, useEffect, useMemo, useCallback, memo } from 'react';
import type { TranscriptionSegment } from '../utils/transcription-formatter';

interface LiveTranscriptionDisplayProps {
  isLiveMode: boolean;
  language: string;
  numSpeakers: number;
  onSegmentsUpdate?: (segments: TranscriptionSegment[]) => void;
  isDownloadReady?: boolean;
}

export default memo(function LiveTranscriptionDisplay({ 
  isLiveMode,
  language,
  numSpeakers,
  onSegmentsUpdate,
  isDownloadReady
}: LiveTranscriptionDisplayProps) {
  const [liveSegments, setLiveSegments] = useState<TranscriptionSegment[]>([]);
  const [isInitializing, setIsInitializing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleTranscription = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);
    setLiveSegments(prev => {
      const newSegments = [...prev, data].sort((a, b) => a.start - b.start);
      const uniqueSegments = newSegments.filter((segment, index, self) =>
        index === self.findIndex(s => 
          Math.abs(s.start - segment.start) < 0.1 && 
          Math.abs(s.end - segment.end) < 0.1
        )
      );
      onSegmentsUpdate?.(uniqueSegments);
      return uniqueSegments;
    });

    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [onSegmentsUpdate]);

  const handleError = useCallback((error: Event) => {
    console.error('SSE Error:', error);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsInitializing(false);
  }, []);

  const handleClose = useCallback(() => {
    console.log('SSE connection closed');
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsInitializing(false);
  }, []);

  useEffect(() => {
    if (!isLiveMode || isDownloadReady) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    setIsInitializing(true);
    const params = new URLSearchParams({
      language,
      num_speakers: numSpeakers.toString()
    });

    eventSourceRef.current = new EventSource(`http://localhost:8000/live-transcribe?${params}`);
    
    eventSourceRef.current.addEventListener('ready', () => setIsInitializing(false));
    eventSourceRef.current.addEventListener('transcription', handleTranscription);
    eventSourceRef.current.addEventListener('error', handleError);
    eventSourceRef.current.addEventListener('close', handleClose);

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.removeEventListener('transcription', handleTranscription);
        eventSourceRef.current.removeEventListener('error', handleError);
        eventSourceRef.current.removeEventListener('close', handleClose);
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [isLiveMode, language, numSpeakers, handleTranscription, handleError, handleClose, isDownloadReady]);

  const renderSegments = useMemo(() => (
    liveSegments.map((segment, index) => (
      <div key={`${segment.start}-${segment.end}-${index}`} className="space-y-2 hover:bg-gray-800/30 p-3 rounded-lg transition-all duration-200">
        <div className="text-sm gradient-text font-mono">
          [{new Date(segment.start * 1000).toISOString().substr(11, 8)} {'->'} {new Date(segment.end * 1000).toISOString().substr(11, 8)}]
        </div>
        <div className="text-gray-300 leading-relaxed font-serif">
          <span className="font-medium text-[#ff7eb3]">{segment.speaker}:</span> {segment.text}
        </div>
      </div>
    ))
  ), [liveSegments]);

  if (!isLiveMode) return null;

  if (isInitializing) {
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[#ff7eb3] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-400">Initializing transcription...</p>
        <p className="text-sm text-gray-500 mt-2">Please wait while we set up the transcription service</p>
      </div>
    );
  }

  return (
    <div className="mt-4">
      <div ref={scrollRef} className="card p-6 space-y-4 max-h-[600px] overflow-y-auto">
        {renderSegments}
      </div>
    </div>
  );
});