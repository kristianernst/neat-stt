import { memo } from 'react';

interface ProgressBarProps {
  progress: number;
  showLabel?: boolean;
  className?: string;
}

export default memo(function ProgressBar({ 
  progress, 
  showLabel = true,
  className = ''
}: ProgressBarProps) {
  return (
    <div className={`mt-4 ${className}`}>
      <div className="w-full bg-[var(--card-bg)] border border-[var(--card-border)] rounded-full h-2">
        <div
          className="bg-[var(--gradient-start)] h-2 rounded-full transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>
      {showLabel && (
        <div className="text-right text-[var(--text-secondary)] text-sm mt-1">
          {progress.toFixed(1)}% completed
        </div>
      )}
    </div>
  );
}); 