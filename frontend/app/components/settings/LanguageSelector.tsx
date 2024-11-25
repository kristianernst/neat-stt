import Button from '../shared/Button';

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
] as const;

export default function LanguageSelector({ value, onChange, disabled }: LanguageSelectorProps) {
  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-[var(--text-primary)]">
        Select Language
      </label>
      <div className="grid grid-cols-1 gap-2">
        {languages.map((lang) => (
          <Button
            key={lang.value}
            onClick={() => onChange(lang.value)}
            disabled={disabled}
            variant={value === lang.value ? 'gradient' : 'primary'}
            className="justify-start"
          >
            {lang.label}
          </Button>
        ))}
      </div>
    </div>
  );
}