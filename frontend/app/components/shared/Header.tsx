import ThemeToggle from './ThemeToggle';
import { useState, useEffect } from 'react';

interface HeaderProps {
  isDark: boolean;
  onThemeChange: (isDark: boolean) => void;
}

export default function Header({ isDark, onThemeChange }: HeaderProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const controlHeader = () => {
      const currentScrollY = window.scrollY;
      setIsVisible(currentScrollY < lastScrollY || currentScrollY < 10);
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', controlHeader);
    return () => window.removeEventListener('scroll', controlHeader);
  }, [lastScrollY]);

  return (
    <header className={`
      fixed top-0 left-0 right-0 
      bg-[var(--header-bg)] z-50 
      border-b border-[var(--card-border)]
      transition-transform duration-300
      ${isVisible ? 'translate-y-0' : '-translate-y-full'}
    `}>
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center mb-2">
          <h1 className="text-2xl font-bold gradient-text">
            Audio Transcription
          </h1>
          <ThemeToggle isDark={isDark} onThemeChange={onThemeChange} />
        </div>
        <p className="text-[var(--text-secondary)]">
          Transform your audio into text with speaker detection
        </p>
      </div>
    </header>
  );
}