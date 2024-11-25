import { memo } from 'react';
import LanguageSelector from "./LanguageSelector";
import SpeakerCounter from "./SpeakerCounter";
import Card from '../shared/Card';

interface ConfigAreaProps {
  language: string;
  onLanguageChange: (language: string) => void;
  numSpeakers: number;
  onNumSpeakersChange: (num: number) => void;
  disabled?: boolean;
}

const ConfigArea = memo(function ConfigArea({
  language,
  onLanguageChange,
  numSpeakers,
  onNumSpeakersChange,
  disabled
}: ConfigAreaProps) {
  return (
    <div className="w-full max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <LanguageSelector
          value={language}
          onChange={onLanguageChange}
          disabled={disabled}
        />
      </Card>
      
      <Card>
        <SpeakerCounter
          value={numSpeakers}
          onChange={onNumSpeakersChange}
          disabled={disabled}
        />
      </Card>
    </div>
  );
});

export default ConfigArea; 