import { memo } from 'react';
import ConfigArea from './ConfigArea';
import Modal from '../shared/Modal';

interface SettingsProps {
  isOpen: boolean;
  onClose: () => void;
  language: string;
  onLanguageChange: (language: string) => void;
  numSpeakers: number;
  onNumSpeakersChange: (num: number) => void;
  disabled?: boolean;
}

export default memo(function Settings({
  isOpen,
  onClose,
  language,
  onLanguageChange,
  numSpeakers,
  onNumSpeakersChange,
  disabled
}: SettingsProps) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Settings"
      maxWidth="max-w-4xl"
    >
      <ConfigArea
        language={language}
        onLanguageChange={onLanguageChange}
        numSpeakers={numSpeakers}
        onNumSpeakersChange={onNumSpeakersChange}
        disabled={disabled}
      />
    </Modal>
  );
}); 