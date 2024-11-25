import { memo } from 'react';
import Button from '../shared/Button';

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
        variant: 'error' as const,
        disabled: true,
      };
    }
    if (isLiveMode) {
      return {
        onClick: onStopLive,
        text: 'Stop Transcription',
        variant: 'error' as const,
      };
    }
    return {
      onClick: onStartLive,
      text: 'Start Live Transcription',
      variant: 'gradient' as const,
    };
  };

  const buttonProps = getButtonProps();

  return (
    <Button
      onClick={buttonProps.onClick}
      disabled={buttonProps.disabled || isDisabled}
      variant={buttonProps.variant}
      className="w-full py-3"
    >
      {buttonProps.text}
    </Button>
  );
});
