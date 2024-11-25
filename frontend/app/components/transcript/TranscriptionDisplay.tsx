import { useState, useEffect, useCallback, memo, useRef } from 'react';
import type { TranscriptionSegment } from '~/utils/transcription-formatter';
import { formatTranscription } from '~/utils/transcription-formatter';
import { FiCopy, FiDownload } from 'react-icons/fi';
import debounce from 'lodash/debounce';
import IconButton from '../shared/IconButton';
import LoadingSpinner from '../shared/LoadingSpinner';
import Button from '../shared/Button';
import ScrollableCard from '../shared/ScrollableCard';
import MarkdownRenderer from '../shared/MarkdownRenderer';
import Modal from '../shared/Modal';
import Card from '../shared/Card';
import ProgressBar from '../shared/ProgressBar';
import CheckIcon from '../shared/CheckIcon';

const formatTime = (ms: number): string => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

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

const TranscriptContent = memo(({ segments }: { segments: TranscriptionSegment[] }) => {
  const content = formatTranscription(segments, 'md');
  return <MarkdownRenderer content={content} />;
});

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
  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleCopy = () => {
    const text = segments.map(segment => {
      const timestamp =
        segment.start !== undefined && segment.end !== undefined
          ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
          : segment.timestamp || '';
      return `${timestamp}\n${segment.speaker}: ${segment.text}`;
    }).join('\n');
    navigator.clipboard.writeText(text);
    
    setCopySuccess(true);
    setTimeout(() => {
      setCopySuccess(false);
    }, 2000);
  };

  const handleDownload = (format: 'md' | 'txt') => {
    const segmentsCopy = JSON.parse(JSON.stringify(segments));
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

  const handleTranscriptionEvent = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);
    if (!data) return;

    setSegments(prev => {
      const newSegments = [...prev];
      const lastSegmentIndex = newSegments.length - 1;
      const lastSegment = lastSegmentIndex >= 0 ? newSegments[lastSegmentIndex] : null;

      if (lastSegment && 
          lastSegment.speaker === data.speaker && 
          Math.abs(lastSegment.end - data.start) < 300) {
        newSegments[lastSegmentIndex] = {
          ...lastSegment,
          text: `${lastSegment.text} ${data.text}`.trim(),
          end: data.end
        };
      } else {
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
        speaker: 'Speaker',
      } as TranscriptionSegment;
    }).filter(Boolean) as TranscriptionSegment[];
  };

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
      <Card className="mt-4 text-center">
        <LoadingSpinner className="mx-auto mb-4" />
        <p className="text-[var(--text-gray-400)]">Initializing transcription...</p>
        <p className="text-sm text-[var(--text-gray-500)] mt-2">
          Please wait while we set up the transcription service
        </p>
      </Card>
    );
  }

  if ((isLoading || isTranscribing) && segments.length === 0) {
    return (
      <Card className="mt-4 text-center">
        <LoadingSpinner className="mx-auto mb-4" />
        <p className="text-[var(--text-secondary)]">Transcribing...</p>
        {isTranscribing && (
          <ProgressBar progress={progress} />
        )}
      </Card>
    );
  }

  if (!segments || segments.length === 0) return null;

  return (
    <div className="mt-4">
      <div className="flex justify-end mb-2 space-x-4">
        <IconButton
          icon={<FiCopy className="w-5 h-5" />}
          successIcon={<CheckIcon />}
          label="Copy"
          successLabel="Copied!"
          onClick={handleCopy}
        />
        <IconButton
          icon={<FiDownload className="w-5 h-5" />}
          successIcon={<CheckIcon />}
          label="Download"
          successLabel="Downloaded!"
          onClick={() => setIsDownloadModalOpen(true)}
        />
      </div>
      
      <ScrollableCard maxHeight="600px">
        <div className="p-6">
          <TranscriptContent segments={segments} />
        </div>
      </ScrollableCard>

      {isTranscribing && (
        <ProgressBar progress={progress} />
      )}

      <Modal
        isOpen={isDownloadModalOpen}
        onClose={() => setIsDownloadModalOpen(false)}
        title="Choose Format"
        maxWidth="max-w-sm"
      >
        <Button
          onClick={() => handleDownload('md')}
          variant="primary"
          className="w-full p-4 text-left"
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
        </Button>
      </Modal>
    </div>
  );
});
