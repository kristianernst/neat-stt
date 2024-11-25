import Button from './Button';

interface ConfigurationSummaryProps {
  language: string;
  numSpeakers: number;
  onOpenSettings: () => void;
  disabled?: boolean;
}

const languageEmoji: Record<string, string> = {
  english: "🇬🇧",
  danish: "🇩🇰",
  spanish: "🇪🇸",
  french: "🇫🇷",
  german: "🇩🇪"
};

export default function ConfigurationSummary({
  language,
  numSpeakers,
  onOpenSettings,
  disabled
}: ConfigurationSummaryProps) {
  return (
    <Button
      onClick={onOpenSettings}
      disabled={disabled}
      variant="primary"
      className="mx-auto flex items-center space-x-3 py-1.5 px-3"
    >
      <span className="text-lg" aria-label={`Language: ${language}`}>
        {languageEmoji[language] || language}
      </span>
      <span className="h-4 w-px bg-[var(--card-border)]" />
      <span className="text-[var(--text-secondary)] text-sm">
        {numSpeakers} {numSpeakers === 1 ? 'speaker' : 'speakers'}
      </span>
      <span className="h-4 w-px bg-[var(--card-border)]" />
      <span className="text-[var(--text-secondary)] text-xs group-hover:text-[var(--gradient-start)] transition-colors duration-300">
        Configure
      </span>
    </Button>
  );
} 