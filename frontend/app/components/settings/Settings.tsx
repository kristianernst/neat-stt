import { memo } from 'react';
import ConfigArea from './ConfigArea';
import { FiX } from 'react-icons/fi';

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
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="min-h-screen px-4 text-center">
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        <div className="inline-block w-full max-w-4xl my-8 text-left align-middle transition-all transform">
          <div className="relative bg-[var(--bg-primary)] rounded-xl shadow-xl p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold gradient-text">Settings</h2>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-[var(--card-hover)] rounded-lg transition-colors"
              >
                <FiX className="w-6 h-6 text-[var(--text-secondary)]" />
              </button>
            </div>

            <ConfigArea
              language={language}
              onLanguageChange={onLanguageChange}
              numSpeakers={numSpeakers}
              onNumSpeakersChange={onNumSpeakersChange}
              disabled={disabled}
            />
          </div>
        </div>
      </div>
    </div>
  );
}); 