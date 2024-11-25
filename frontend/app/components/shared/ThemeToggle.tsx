import { FiSun, FiMoon } from 'react-icons/fi';
import Button from './Button';

interface ThemeToggleProps {
  isDark: boolean;
  onThemeChange: (isDark: boolean) => void;
}

export default function ThemeToggle({ isDark, onThemeChange }: ThemeToggleProps) {
  return (
    <Button
      onClick={() => onThemeChange(!isDark)}
      variant="primary"
      className="p-2 rounded-full hover:scale-110"
      aria-label="Toggle theme"
    >
      {isDark ? (
        <FiSun className="w-5 h-5 text-[var(--gradient-start)]" />
      ) : (
        <FiMoon className="w-5 h-5 text-[var(--gradient-end)]" />
      )}
    </Button>
  );
}