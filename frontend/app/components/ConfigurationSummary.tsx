interface ConfigurationSummaryProps {
  language: string;
  numSpeakers: number;
  onOpenSettings: () => void;
  disabled?: boolean;
}

export default function ConfigurationSummary({
  language,
  numSpeakers,
  onOpenSettings,
  disabled
}: ConfigurationSummaryProps) {
  const getLanguageLabel = () => {
    const languageMap: { [key: string]: string } = {
      english: "🇬🇧",
      danish: "🇩🇰",
      spanish: "🇪🇸",
      french: "🇫🇷",
      german: "🇩🇪"
    };
    return languageMap[language] || language;
  };

  return (
    <button
      onClick={onOpenSettings}
      disabled={disabled}
      className={`
        group flex items-center space-x-3 mx-auto
        py-1.5 px-3 rounded-full
        bg-[var(--card-bg)] hover:bg-[var(--card-hover)]
        border border-[var(--card-border)]
        transition-all duration-300
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-[var(--gradient-start)]/30'}
      `}
    >
      <span className="text-lg" aria-label={`Language: ${language}`}>
        {getLanguageLabel()}
      </span>
      <span className="h-4 w-px bg-[var(--card-border)]" />
      <span className="text-[var(--text-secondary)] text-sm">
        {numSpeakers} {numSpeakers === 1 ? 'speaker' : 'speakers'}
      </span>
      <span className="h-4 w-px bg-[var(--card-border)]" />
      <span className="text-[var(--text-secondary)] text-xs group-hover:text-[var(--gradient-start)] transition-colors duration-300">
        Configure
      </span>
    </button>
  );
} 