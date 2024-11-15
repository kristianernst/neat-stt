import { useState, useRef, useEffect, useCallback, memo } from 'react';
import type { TranscriptionSegment } from '../utils/transcription-formatter';
import { formatTranscription } from '../utils/transcription-formatter';
import { FiCopy, FiDownload } from 'react-icons/fi';
import debounce from 'lodash/debounce';

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
    // Create a deep copy of segments to prevent any state issues
    const segmentsCopy = JSON.parse(JSON.stringify(segments));
    
    // Sort segments by start time to ensure correct order
    segmentsCopy.sort((a: TranscriptionSegment, b: TranscriptionSegment) => (a.start || 0) - (b.start || 0));
    
    const formattedContent = formatTranscription(segmentsCopy, format);
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
      const newSegments = [...prev];
      // Find the last segment from the same speaker
      const lastSegmentIndex = newSegments.length - 1;
      const lastSegment = lastSegmentIndex >= 0 ? newSegments[lastSegmentIndex] : null;

      // Check if we should merge with the last segment
      if (lastSegment && 
          lastSegment.speaker === data.speaker && 
          // Only merge if the gap is less than 5 minutes (300 seconds)
          Math.abs(lastSegment.end - data.start) < 300) {
        
        // Update the last segment instead of creating a new one
        newSegments[lastSegmentIndex] = {
          ...lastSegment,
          text: `${lastSegment.text} ${data.text}`.trim(),
          end: data.end
        };
      } else {
        // Add as new segment if it's a different speaker or time gap is too large
        newSegments.push({ ...data });
      }
      
      return newSegments;
    });
  }, []);

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

  useEffect(() => {
    if (scrollRef.current && segments.length > 0) {
      // Slightly scroll down to hint at scrollability
      scrollRef.current.scrollTop = 10;
      
      // Then smoothly scroll back to top
      setTimeout(() => {
        scrollRef.current?.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      }, 500);
    }
  }, [segments.length === 1]); // Only trigger on first segment

  const debouncedSetSegments = useCallback(
    debounce((newSegments: TranscriptionSegment[]) => {
      setSegments(newSegments);
    }, 100),
    []
  );

  useEffect(() => {
    return () => {
      setSegments([]);
    };
  }, []);

  if (isInitializing && isLiveMode) {
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[var(--spinner-border)] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-[var(--text-gray-400)]">Initializing transcription...</p>
        <p className="text-sm text-[var(--text-gray-500)] mt-2">Please wait while we set up the transcription service</p>
      </div>
    );
  }

  // Adjusted rendering logic
  if ((isLoading || isTranscribing) && segments.length === 0) {
    // Show a loading indicator when transcribing
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[var(--gradient-start)] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-[var(--text-secondary)]">Transcribing...</p>
        {isTranscribing && (
          <div className="mt-4">
            <div className="w-full bg-[var(--card-bg)] border border-[var(--card-border)] rounded-full h-2">
              <div
                className="bg-[var(--gradient-start)] h-2 rounded-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-right text-[var(--text-secondary)] text-sm mt-1">
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
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                     focus:outline-none flex items-center space-x-1 group relative"
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
                  ? 'opacity-100 scale-100 text-[var(--success-text)]' 
                  : 'opacity-0 scale-75'
              }`}
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={`text-sm transition-colors duration-300 ${
            copySuccess ? 'text-[var(--success-text)]' : ''
          }`}>
            {copySuccess ? 'Copied!' : 'Copy'}
          </span>
        </button>
        <button
          onClick={() => setIsDownloadModalOpen(true)}
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                     focus:outline-none flex items-center space-x-1 group relative"
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
                  ? 'opacity-100 scale-100 text-[var(--success-text)]' 
                  : 'opacity-0 scale-75'
              }`}
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={`text-sm transition-colors duration-300 ${
            downloadSuccess ? 'text-[var(--success-text)]' : ''
          }`}>
            {downloadSuccess ? 'Downloaded!' : 'Download'}
          </span>
        </button>
      </div>
      <div ref={scrollRef} className="card p-6 space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar relative">
        {/* Top gradient fade */}
        <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-[var(--card-bg)] to-transparent pointer-events-none z-10" />
        
        {/* Content */}
        {segments.map((segment, index) => (
          <div
            key={`${segment.speaker}-${segment.start}-${segment.end}`}
            className="space-y-2 p-3 rounded-lg"
          >
            {/* Metadata line (timestamp + speaker) */}
            <div className="flex items-center gap-2 text-sm">
              <span className="gradient-text font-mono">
                {segment.start !== undefined && segment.end !== undefined
                  ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
                  : segment.timestamp || null}
              </span>
              {segment.speaker && (
                <>
                  <span className="text-[var(--text-secondary)]">•</span>
                  <span className="font-medium text-[var(--gradient-start)]">
                    {segment.speaker}
                  </span>
                </>
              )}
            </div>

            {/* Text content on new line */}
            <div className="text-[var(--text-primary)] leading-relaxed font-serif pl-4">
              {segment.text}
            </div>
          </div>
        ))}
        
        {/* Bottom gradient fade */}
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[var(--card-bg)] to-transparent pointer-events-none z-10" />
      </div>
      {isTranscribing && (
        <div className="mt-4">
          <div className="w-full bg-[var(--card-bg)] border border-[var(--card-border)] rounded-full h-2">
            <div
              className="bg-[var(--gradient-start)] h-2 rounded-full transition-all duration-200"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="text-right text-[var(--text-secondary)] text-sm mt-1">
            {progress.toFixed(1)}% completed
          </div>
        </div>
      )}
      {/* Format Selection Modal */}
      {isDownloadModalOpen && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div 
            className="absolute inset-0 bg-[var(--modal-overlay)] backdrop-blur-sm"
            onClick={() => setIsDownloadModalOpen(false)}
          />
          <div className="relative bg-[var(--modal-bg)] card p-6 w-full max-w-sm">
            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-4">
              Choose Format
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => handleDownload('md')}
                className="w-full p-4 rounded-lg bg-[var(--card-bg)]
                         border border-[var(--card-border)] 
                         hover:border-[var(--gradient-start)]/50 
                         transition-all duration-300
                         text-left group"
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg gradient-button">
                    <span className="text-white text-lg">.md</span>
                  </div>
                  <div>
                    <div className="font-medium text-[var(--text-primary)]">Markdown</div>
                    <div className="text-sm text-[var(--text-secondary)]">
                      Formatted with headers and styling
                    </div>
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
