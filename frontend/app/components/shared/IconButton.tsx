import { ReactNode, useState } from 'react';

interface IconButtonProps {
  onClick: () => void;
  icon: ReactNode;
  successIcon?: ReactNode;
  label: string;
  successLabel?: string;
  disabled?: boolean;
  successDuration?: number;
}

export default function IconButton({
  onClick,
  icon,
  successIcon,
  label,
  successLabel,
  disabled = false,
  successDuration = 2000
}: IconButtonProps) {
  const [success, setSuccess] = useState(false);

  const handleClick = () => {
    onClick();
    setSuccess(true);
    setTimeout(() => setSuccess(false), successDuration);
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled || success}
      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                focus:outline-none flex items-center space-x-1 group relative"
    >
      <div className="relative w-5 h-5">
        <div className={`absolute transition-all duration-300 ${
          success ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
        }`}>
          {icon}
        </div>
        <div className={`absolute transition-all duration-300 ${
          success ? 'opacity-100 scale-100 text-[var(--success-text)]' : 'opacity-0 scale-75'
        }`}>
          {successIcon}
        </div>
      </div>
      <span className={`text-sm transition-colors duration-300 ${
        success ? 'text-[var(--success-text)]' : ''
      }`}>
        {success ? successLabel || 'Success!' : label}
      </span>
    </button>
  );
} 