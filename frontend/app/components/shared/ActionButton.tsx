import { FiCopy, FiDownload } from 'react-icons/fi';

interface ActionButtonProps {
  onClick: () => void;
  icon: 'copy' | 'download';
  successText: string;
  defaultText: string;
  isSuccess: boolean;
  disabled?: boolean;
}

export default function ActionButton({
  onClick,
  icon,
  successText,
  defaultText,
  isSuccess,
  disabled
}: ActionButtonProps) {
  const Icon = icon === 'copy' ? FiCopy : FiDownload;
  
  return (
    <button
      onClick={onClick}
      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                focus:outline-none flex items-center space-x-1 group relative"
      disabled={disabled || isSuccess}
    >
      <div className="relative w-5 h-5">
        <Icon 
          className={`w-5 h-5 absolute transition-all duration-300 ${
            isSuccess ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
          }`}
        />
        <svg 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className={`w-5 h-5 absolute transition-all duration-300 ${
            isSuccess 
              ? 'opacity-100 scale-100 text-[var(--success-text)]' 
              : 'opacity-0 scale-75'
          }`}
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      <span className={`text-sm transition-colors duration-300 ${
        isSuccess ? 'text-[var(--success-text)]' : ''
      }`}>
        {isSuccess ? successText : defaultText}
      </span>
    </button>
  );
}