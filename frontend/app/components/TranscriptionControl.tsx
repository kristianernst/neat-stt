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
        className: 'bg-red-500/20 text-red-300',
        disabled: true,
      };
    }
    if (isLiveMode) {
      return {
        onClick: onStopLive,
        text: 'Stop Transcription',
        className: 'bg-red-500/20 text-red-300 hover:bg-red-500/30',
      };
    }
    return {
      onClick: onStartLive,
      text: 'Start Live Transcription',
      className: 'bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] hover:shadow-lg hover:shadow-purple-500/20',
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
