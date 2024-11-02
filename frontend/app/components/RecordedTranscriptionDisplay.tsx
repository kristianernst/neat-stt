import { memo, useMemo } from 'react';

interface TranscriptionBlock {
  timestamp: string;
  text: string;
  key: number;
}

interface RecordedTranscriptionDisplayProps {
  transcription: string;
  isLoading: boolean;
}

export default memo(function RecordedTranscriptionDisplay({ 
  transcription, 
  isLoading 
}: RecordedTranscriptionDisplayProps) {
  const transcriptionBlocks = useMemo(() => {
    if (!transcription) return [];
    return transcription.split('\n\n').map((block, index) => {
      const [timestamp, ...textLines] = block.split('\n');
      if (!timestamp || !textLines.length) return null;
      return { timestamp, text: textLines.join(' '), key: index } as TranscriptionBlock;
    }).filter(Boolean) as TranscriptionBlock[];
  }, [transcription]);

  if (isLoading) {
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

  if (!transcription) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="card p-6 space-y-4">
        {transcriptionBlocks.map((block) => (
          <div key={block.key} className="space-y-2 hover:bg-gray-800/30 p-3 rounded-lg transition-all duration-200">
            <div className="text-sm gradient-text font-mono">{block.timestamp}</div>
            <div className="text-gray-300 leading-relaxed font-serif">{block.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}); 