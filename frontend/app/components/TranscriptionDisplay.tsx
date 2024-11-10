import { useState, useRef, useEffect, useCallback, memo } from 'react';
import type { TranscriptionSegment } from '../utils/transcription-formatter';
import { formatTranscription } from '../utils/transcription-formatter';
import { FiCopy, FiDownload } from 'react-icons/fi';

interface TranscriptionDisplayProps {
  isLiveMode: boolean;
  language: string;
  numSpeakers: number;
  onSegmentsUpdate?: (segments: TranscriptionSegment[]) => void;
  transcription: string;
  isLoading: boolean;
  segments: TranscriptionSegment[];
  setSegments: React.Dispatch<React.SetStateAction<TranscriptionSegment[]>>;
  isTranscribing: boolean;
  progress: number;
  setProgress: React.Dispatch<React.SetStateAction<number>>;
}

export default memo(function TranscriptionDisplay({
  isLiveMode,
  language,
  numSpeakers,
  onSegmentsUpdate,
  transcription,
  isLoading,
  segments,
  setSegments,
  isTranscribing,
  progress,
  setProgress,
}: TranscriptionDisplayProps) {
  const [isInitializing, setIsInitializing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  // Smooth scroll to bottom when new segments are added
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [segments]);

  const handleCopy = () => {
    const text = segments.map(segment => {
      const timestamp =
        segment.start !== undefined && segment.end !== undefined
          ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
          : segment.timestamp || '';
      return `${timestamp}\n${segment.speaker}: ${segment.text}`;
    }).join('\n');
    navigator.clipboard.writeText(text);
    
    // Show success state
    setCopySuccess(true);
    
    // Reset after animation
    setTimeout(() => {
      setCopySuccess(false);
    }, 2000);
  };

  const handleDownload = (format: 'md' | 'txt') => {
    const formattedContent = formatTranscription(segments, format);
    const blob = new Blob([formattedContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setIsDownloadModalOpen(false);
    setDownloadSuccess(true);
    
    setTimeout(() => {
      setDownloadSuccess(false);
    }, 2000);
  };

  const formatTime = (seconds: number): string => {
    return new Date(seconds * 1000).toISOString().substr(11, 8);
  };

  const handleTranscriptionEvent = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);
    if (!data) return;

    setSegments(prev => {
      // Check if this is a new speaker or continuation
      if (prev.length > 0 && prev[prev.length - 1].speaker === data.speaker) {
        const newSegments = [...prev];
        const lastSegment = { ...newSegments[newSegments.length - 1] };
        lastSegment.text = `${lastSegment.text} ${data.text}`.trim();
        lastSegment.end = data.end;
        newSegments[newSegments.length - 1] = lastSegment;
        onSegmentsUpdate?.(newSegments);
        return newSegments;
      }
      
      const newSegments = [...prev, data];
      onSegmentsUpdate?.(newSegments);
      return newSegments;
    });
  }, [onSegmentsUpdate]);

  const handleProgressEvent = useCallback((event: MessageEvent) => {
    const data = event.data ? JSON.parse(event.data) : {};
    if (data.progress !== undefined) {
      setProgress(data.progress);
    }
  }, [setProgress]);

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
    if (isLiveMode) {
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
  }, [isLiveMode, language, numSpeakers, handleTranscriptionEvent, handleError, handleClose]);

  // When transcription changes (for recorded transcription), parse it into segments
  useEffect(() => {
    if (!isLiveMode && transcription && segments.length === 0) {
      const parsedSegments = parseTranscription(transcription);
      setSegments(parsedSegments);
    }
  }, [isLiveMode, transcription, segments.length, setSegments]);

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

  if (isInitializing && isLiveMode) {
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[#ff7eb3] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-400">Initializing transcription...</p>
        <p className="text-sm text-gray-500 mt-2">Please wait while we set up the transcription service</p>
      </div>
    );
  }

  // Adjusted rendering logic
  if ((isLoading || isTranscribing) && segments.length === 0) {
    // Show a loading indicator when transcribing
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[#ff7eb3] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-gray-400">Transcribing...</p>
        {isTranscribing && (
          <div className="mt-4">
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] h-2 rounded-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-right text-gray-400 text-sm mt-1">
              {progress.toFixed(1)}% completed
            </div>
          </div>
        )}
      </div>
    );
  }

  if (!segments || segments.length === 0) {
    // If there are no segments and not transcribing, don't display anything
    return null;
  }

  return (
    <div className="mt-4">
      <div className="flex justify-end mb-2 space-x-4">
        <button
          onClick={handleCopy}
          className="text-gray-400 hover:text-white focus:outline-none flex items-center space-x-1 group relative"
          disabled={copySuccess}
        >
          <div className="relative w-5 h-5">
            <FiCopy 
              className={`w-5 h-5 absolute transition-all duration-300 ${
                copySuccess ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
              }`}
            />
            <svg 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className={`w-5 h-5 absolute transition-all duration-300 ${
                copySuccess 
                  ? 'opacity-100 scale-100 text-green-400' 
                  : 'opacity-0 scale-75'
              }`}
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={`text-sm transition-colors duration-300 ${
            copySuccess ? 'text-green-400' : ''
          }`}>
            {copySuccess ? 'Copied!' : 'Copy'}
          </span>
        </button>
        <button
          onClick={() => setIsDownloadModalOpen(true)}
          className="text-gray-400 hover:text-white focus:outline-none flex items-center space-x-1 group relative"
          disabled={downloadSuccess}
        >
          <div className="relative w-5 h-5">
            <FiDownload 
              className={`w-5 h-5 absolute transition-all duration-300 ${
                downloadSuccess ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
              }`}
            />
            <svg 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className={`w-5 h-5 absolute transition-all duration-300 ${
                downloadSuccess 
                  ? 'opacity-100 scale-100 text-green-400' 
                  : 'opacity-0 scale-75'
              }`}
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={`text-sm transition-colors duration-300 ${
            downloadSuccess ? 'text-green-400' : ''
          }`}>
            {downloadSuccess ? 'Downloaded!' : 'Download'}
          </span>
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
        {isTranscribing && (
          <div className="flex justify-center items-center mt-4">
            <div className="animate-spin w-6 h-6 border-4 border-[#ff7eb3] border-t-transparent rounded-full"></div>
            <span className="ml-2 text-gray-400">Transcribing...</span>
          </div>
        )}
      </div>
      {isTranscribing && (
        <div className="mt-4">
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] h-2 rounded-full transition-all duration-200"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="text-right text-gray-400 text-sm mt-1">
            {progress.toFixed(1)}% completed
          </div>
        </div>
      )}
      {/* Format Selection Modal */}
      {isDownloadModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsDownloadModalOpen(false)}
          />
          <div className="relative bg-gray-900 rounded-xl p-6 shadow-xl border border-gray-800 w-full max-w-sm">
            <h3 className="text-lg font-medium text-gray-200 mb-4">
              Choose Format
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => handleDownload('md')}
                className="w-full p-4 rounded-lg bg-gradient-to-r from-[#ff7eb3]/10 to-[#8957ff]/10 
                         border border-gray-800 hover:border-[#ff7eb3]/50 transition-all duration-300
                         text-left group"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] group-hover:shadow-lg group-hover:shadow-purple-500/20">
                    <span className="text-white text-lg">.md</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-200">Markdown</div>
                    <div className="text-sm text-gray-400">Formatted with headers and styling</div>
                  </div>
                </div>
              </button>
              
              <button
                onClick={() => handleDownload('txt')}
                className="w-full p-4 rounded-lg bg-gradient-to-r from-[#ff7eb3]/10 to-[#8957ff]/10 
                         border border-gray-800 hover:border-[#ff7eb3]/50 transition-all duration-300
                         text-left group"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] group-hover:shadow-lg group-hover:shadow-purple-500/20">
                    <span className="text-white text-lg">.txt</span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-200">Plain Text</div>
                    <div className="text-sm text-gray-400">Simple text format</div>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
