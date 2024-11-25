import { useState } from 'react';
import type { ChangeEvent } from 'react';
import Card from '../shared/Card';
import LoadingSpinner from '../shared/LoadingSpinner';

interface AudioUploaderProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
  isDisabled: boolean;
}

export default function AudioUploader({ 
  onFileSelect, 
  isUploading,
  isDisabled
}: AudioUploaderProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files?.[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <Card
        padding="lg"
        className={`
          relative border-2 border-dashed text-center
          transition-all duration-300 ease-in-out
          ${dragActive 
            ? 'border-[var(--gradient-start)] bg-[var(--gradient-start)]/5 shadow-lg shadow-[var(--gradient-start)]/20' 
            : 'border-[var(--card-border)] hover:border-[var(--gradient-start)]/50'}
        `}
      >
        <input
          type="file"
          accept="audio/*"
          onChange={(e: ChangeEvent<HTMLInputElement>) => e.target.files?.[0] && onFileSelect(e.target.files[0])}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isDisabled}
        />
        {isUploading ? (
          <div className="flex items-center justify-center space-x-3">
            <LoadingSpinner size="sm" />
            <span className="gradient-text font-medium">Processing your audio...</span>
          </div>
        ) : (
          <UploadIcon />
        )}
      </Card>
    </div>
  );
}

const UploadIcon = () => (
  <>
    <div className="mb-4 relative group">
      <svg className="mx-auto h-12 w-12 text-gray-400 transition-transform duration-300 group-hover:scale-110" 
           stroke="url(#gradient)" fill="none" viewBox="0 0 48 48" aria-hidden="true">
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ff7eb3" />
            <stop offset="100%" stopColor="#8957ff" />
          </linearGradient>
        </defs>
        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" 
              strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
    <p className="text-lg text-[var(--text-primary)]">Drop your audio file here, or click to select</p>
    <p className="text-sm text-[var(--text-secondary)]">MP3, WAV, M4A up to 10MB</p>
  </>
);