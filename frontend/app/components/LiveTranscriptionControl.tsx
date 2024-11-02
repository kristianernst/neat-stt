import { memo, useMemo } from 'react';

interface LiveTranscriptionControlProps {
  onStart: () => void;
  onStop: () => void;
  onDownload: () => void;
  isLiveMode: boolean;
  isDownloadReady: boolean;
  isDisabled: boolean;
  isStoppingTranscription: boolean;
}

const getButtonProps = (
  isDownloadReady: boolean, 
  isLiveMode: boolean,
  isStoppingTranscription: boolean,
  onDownload: () => void,
  onStop: () => void,
  onStart: () => void,
) => {
  if (isStoppingTranscription) {
    return {
      onClick: () => {},
      text: 'Stopping Transcription...',
      className: 'bg-red-500/20 text-red-300',
      disabled: true
    };
  }
  if (isDownloadReady) {
    return {
      onClick: onDownload,
      text: 'Download Transcription',
      className: 'bg-green-500/20 text-green-300 hover:bg-green-500/30'
    };
  }
  if (isLiveMode) {
    return {
      onClick: onStop,
      text: 'Stop Transcription',
      className: 'bg-red-500/20 text-red-300 hover:bg-red-500/30'
    };
  }
  return {
    onClick: onStart,
    text: 'Start Live Transcription',
    className: 'bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] hover:shadow-lg hover:shadow-purple-500/20'
  };
};

export default memo(function LiveTranscriptionControl({
  onStart,
  onStop,
  onDownload,
  isLiveMode,
  isDownloadReady,
  isDisabled,
  isStoppingTranscription
}: LiveTranscriptionControlProps) {
  const buttonProps = useMemo(
    () => getButtonProps(isDownloadReady, isLiveMode, isStoppingTranscription, onDownload, onStop, onStart),
    [isDownloadReady, isLiveMode, isStoppingTranscription, onDownload, onStop, onStart]
  );

  return (
    <button
      onClick={buttonProps.onClick}
      disabled={isDisabled}
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