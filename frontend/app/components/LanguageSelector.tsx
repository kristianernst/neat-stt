interface LanguageSelectorProps {
  value: string;
  onChange: (language: string) => void;
  numSpeakers: number;
  onNumSpeakersChange: (num: number) => void;
  disabled?: boolean;
}

const languages = [
  { value: "english", label: "🇬🇧 English" },
  { value: "danish", label: "🇩🇰 Danish" },
  { value: "spanish", label: "🇪🇸 Spanish" },
  { value: "french", label: "🇫🇷 French" },
  { value: "german", label: "🇩🇪 German" }
];

export default function LanguageSelector({ 
  value, 
  onChange, 
  numSpeakers,
  onNumSpeakersChange,
  disabled 
}: LanguageSelectorProps) {
  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-200">
        Select Language
      </label>
      <div className="grid grid-cols-1 gap-2">
        {languages.map((lang) => (
          <button
            key={lang.value}
            onClick={() => onChange(lang.value)}
            disabled={disabled}
            className={`
              px-4 py-2 rounded-lg text-left transition-all
              ${value === lang.value 
                ? 'bg-gradient-to-r from-[#ff7eb3] to-[#8957ff] text-white shadow-lg shadow-purple-500/20' 
                : 'bg-[#1a1a1a] bg-opacity-80 text-gray-300 hover:bg-[#222222] backdrop-blur-sm border border-gray-800/30'}
              ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            {lang.label}
          </button>
        ))}
      </div>
    </div>
  );
}