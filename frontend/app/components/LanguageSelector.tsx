interface LanguageSelectorProps {
  value: string;
  onChange: (language: string) => void;
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
  disabled 
}: LanguageSelectorProps) {
  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-[var(--text-primary)]">
        Select Language
      </label>
      <div className="grid grid-cols-1 gap-2">
        {languages.map((lang) => (
          <button
            key={lang.value}
            onClick={() => onChange(lang.value)}
            disabled={disabled}
            className={`
              px-4 py-3 rounded-lg text-left transition-all
              border border-[var(--card-border)]
              ${value === lang.value 
                ? 'gradient-button text-white' 
                : 'bg-[var(--card-bg)] text-[var(--text-primary)] hover:bg-[var(--card-hover)] hover:border-[var(--gradient-start)]/50'}
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