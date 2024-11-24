import { memo } from 'react';

interface TranscriptionControlProps {
  isLiveMode: boolean;
  isDisabled: boolean;
  isStoppingTranscription: boolean;
  onStartLive: () => void;
  onStopLive: () => void;
}

export default memo(function TranscriptionControl({
  isLiveMode,
  isDisabled,
  isStoppingTranscription,
  onStartLive,
  onStopLive,
}: TranscriptionControlProps) {
  const getButtonProps = () => {
    if (isStoppingTranscription) {
      return {
        onClick: () => {},
        text: 'Stopping Transcription...',
        className: 'bg-[var(--error-bg)] text-[var(--error-text)]',
        disabled: true,
      };
    }
    if (isLiveMode) {
      return {
        onClick: onStopLive,
        text: 'Stop Transcription',
        className: 'bg-[var(--error-bg)] text-[var(--error-text)] hover:bg-[var(--error-bg)]/80',
      };
    }
    return {
      onClick: onStartLive,
      text: 'Start Live Transcription',
      className: 'gradient-button',
    };
  };

  const buttonProps = getButtonProps();

  return (
    <button
      onClick={buttonProps.onClick}
      disabled={buttonProps.disabled || isDisabled}
      className={`
        w-full py-3 px-4 rounded-xl text-center transition-all duration-300
        ${buttonProps.className}
        disabled:opacity-50 disabled:cursor-not-allowed
      `}
    >
      {buttonProps.text}
    </button>
  );
});
