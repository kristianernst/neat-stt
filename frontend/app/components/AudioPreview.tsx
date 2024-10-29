interface AudioPreviewProps {
  file: File | null;
  onClose: () => void;
}

export default function AudioPreview({ file, onClose }: AudioPreviewProps) {
  if (!file) return null;

  const audioUrl = URL.createObjectURL(file);

  return (
    <div className="card p-6 glass-effect">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium gradient-text">{file.name}</h3>
        <button 
          onClick={onClose}
          className="text-gray-400 hover:text-gray-200 transition-colors"
          aria-label="Close preview"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <audio 
        controls 
        className="w-full" 
        src={audioUrl}
        onEnded={() => URL.revokeObjectURL(audioUrl)} 
      />
    </div>
  );
} 