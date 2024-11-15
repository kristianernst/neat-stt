import { FiSun, FiMoon } from 'react-icons/fi';

interface ThemeToggleProps {
  isDark: boolean;
  onThemeChange: (isDark: boolean) => void;
}

export default function ThemeToggle({ isDark, onThemeChange }: ThemeToggleProps) {
  return (
    <button
      onClick={() => onThemeChange(!isDark)}
      className="p-2 rounded-full 
                 bg-[var(--card-bg)]
                 border border-[var(--card-border)]
                 hover:scale-110 transition-all duration-300
                 hover:shadow-lg hover:shadow-purple-500/20"
      aria-label="Toggle theme"
    >
      {isDark ? (
        <FiSun className="w-5 h-5 text-[var(--gradient-start)]" />
      ) : (
        <FiMoon className="w-5 h-5 text-[var(--gradient-end)]" />
      )}
    </button>
  );
}