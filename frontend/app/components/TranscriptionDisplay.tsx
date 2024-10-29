interface TranscriptionDisplayProps {
  transcription: string;
  isLoading: boolean;
}

export default function TranscriptionDisplay({ 
  transcription, 
  isLoading 
}: TranscriptionDisplayProps) {
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
        {transcription.split('\n\n').map((block, index) => {
          const [timestamp, ...textLines] = block.split('\n');
          if (!timestamp || !textLines.length) return null;
          
          return (
            <div key={index} className="space-y-2 hover:bg-gray-800/30 p-3 rounded-lg transition-all duration-200">
              <div className="text-sm gradient-text font-mono">{timestamp}</div>
              <div className="text-gray-300 leading-relaxed font-serif">{textLines.join(' ')}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
} 