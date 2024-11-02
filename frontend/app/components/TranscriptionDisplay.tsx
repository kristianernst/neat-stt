import { useState, useRef, useEffect, useCallback, memo } from 'react';
import type { TranscriptionSegment } from '../utils/transcription-formatter';
import { formatTranscription } from '../utils/transcription-formatter';
import { FiCopy, FiDownload } from 'react-icons/fi'; // Importing icons from react-icons

interface TranscriptionDisplayProps {
  isLiveMode: boolean;
  language: string;
  numSpeakers: number;
  onSegmentsUpdate?: (segments: TranscriptionSegment[]) => void;
  isDownloadReady?: boolean;
  transcription: string;
  isLoading: boolean;
  segments: TranscriptionSegment[];
  setSegments: React.Dispatch<React.SetStateAction<TranscriptionSegment[]>>;
}

export default memo(function TranscriptionDisplay({
  isLiveMode,
  language,
  numSpeakers,
  onSegmentsUpdate,
  isDownloadReady,
  transcription,
  isLoading,
  segments,
  setSegments,
}: TranscriptionDisplayProps) {
  const [isInitializing, setIsInitializing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Scroll to bottom when new segments are added
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [segments]);

  const handleCopy = () => {
    const text = segments.map(segment => {
      const timestamp = segment.start !== undefined && segment.end !== undefined
        ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
        : segment.timestamp || '';
      return `${timestamp}\n${segment.speaker}: ${segment.text}`;
    }).join('\n');
    navigator.clipboard.writeText(text);
  };

  const handleDownload = () => {
    const downloadFormat = window.confirm(
      'Choose a format:\nOK - Markdown (.md)\nCancel - Plain Text (.txt)'
    ) ? 'md' : 'txt';

    const formattedContent = formatTranscription(segments, downloadFormat);
    const blob = new Blob([formattedContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription.${downloadFormat}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatTime = (seconds: number): string => {
    return new Date(seconds * 1000).toISOString().substr(11, 8);
  };

  const handleTranscriptionEvent = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);
    setSegments(prev => {
      if (prev.length > 0 && prev[prev.length - 1].speaker === data.speaker) {
        const newSegments = [...prev];
        const lastSegment = { ...newSegments[newSegments.length - 1] };
        lastSegment.text = `${lastSegment.text} ${data.text}`;
        lastSegment.end = data.end;
        newSegments[newSegments.length - 1] = lastSegment;
        onSegmentsUpdate?.(newSegments);
        return newSegments;
      }
      const newSegments = [...prev, data];
      onSegmentsUpdate?.(newSegments);
      return newSegments;
    });
  }, [onSegmentsUpdate, setSegments]);

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
    if (isLiveMode && !isDownloadReady) {
      setIsInitializing(true);
      const params = new URLSearchParams({
        language,
        num_speakers: numSpeakers.toString()
      });

      eventSourceRef.current = new EventSource(`http://localhost:8000/live-transcribe?${params}`);

      eventSourceRef.current.addEventListener('ready', () => setIsInitializing(false));
      eventSourceRef.current.addEventListener('transcription', handleTranscriptionEvent);
      eventSourceRef.current.addEventListener('error', handleError);
      eventSourceRef.current.addEventListener('close', handleClose);
    } else {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.removeEventListener('transcription', handleTranscriptionEvent);
        eventSourceRef.current.removeEventListener('error', handleError);
        eventSourceRef.current.removeEventListener('close', handleClose);
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [isLiveMode, language, numSpeakers, handleTranscriptionEvent, handleError, handleClose, isDownloadReady]);

  // When transcription changes (for recorded transcription), parse it into segments
  useEffect(() => {
    if (!isLiveMode && transcription) {
      const parsedSegments = parseTranscription(transcription);
      if (parsedSegments.length > 0) {
        setSegments(parsedSegments);
        onSegmentsUpdate?.(parsedSegments);
      }
    }
  }, [isLiveMode, transcription, setSegments, onSegmentsUpdate]);

  const parseTranscription = (transcription: string): TranscriptionSegment[] => {
    if (!transcription) return [];
    return transcription.split('\n\n').map((block, index) => {
      const [timestamp, ...textLines] = block.split('\n');
      if (!timestamp || !textLines.length) return null;
      return {
        timestamp: timestamp.trim(),
        text: textLines.join(' ').trim(),
        speaker: 'Speaker', // You might have logic to extract speaker names
      } as TranscriptionSegment;
    }).filter(Boolean) as TranscriptionSegment[];
  };

  if (isLoading) {
    // Loading placeholder
    return (
      <div className="mt-4 card p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gradient-to-r from-[#ff7eb3]/20 to-[#8957ff]/20 rounded w-3/4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gradient-to-r from-[#ff7eb3]/20 to-[#8957ff]/20 rounded"></div>
            <div className="h-4 bg-gradient-to-r from-[#ff7eb3]/20 to-[#8957ff]/20 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (isInitializing && isLiveMode) {
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[#ff7eb3] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-400">Initializing transcription...</p>
        <p className="text-sm text-gray-500 mt-2">Please wait while we set up the transcription service</p>
      </div>
    );
  }

  if (!segments || segments.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="flex justify-end mb-2 space-x-4">
        <button
          onClick={handleCopy}
          className="text-gray-400 hover:text-white focus:outline-none flex items-center space-x-1"
        >
          <FiCopy className="w-5 h-5" />
          <span className="text-sm">Copy</span>
        </button>
        <button
          onClick={handleDownload}
          className="text-gray-400 hover:text-white focus:outline-none flex items-center space-x-1"
        >
          <FiDownload className="w-5 h-5" />
          <span className="text-sm">Download</span>
        </button>
      </div>
      <div ref={scrollRef} className="card p-6 space-y-4 max-h-[600px] overflow-y-auto">
        {segments.map((segment, index) => (
          <div
            key={`${index}`}
            className="space-y-2 hover:bg-gray-800/30 p-3 rounded-lg transition-all duration-200"
          >
            <div className="text-sm gradient-text font-mono">
              {segment.start !== undefined && segment.end !== undefined
                ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
                : segment.timestamp || null}
            </div>
            <div className="text-gray-300 leading-relaxed font-serif">
              {segment.speaker ? (
                <span className="font-medium text-[#ff7eb3]">{segment.speaker}:</span>
              ) : null}{' '}
              {segment.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
});
