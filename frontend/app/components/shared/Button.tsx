import { ReactNode } from 'react';

interface ButtonProps {
  onClick?: () => void;
  disabled?: boolean;
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'error' | 'gradient';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export default function Button({
  onClick,
  disabled,
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button'
}: ButtonProps) {
  const baseStyles = 'transition-all duration-300 rounded-lg focus:outline-none';
  
  const variantStyles = {
    primary: 'text-[var(--text-primary)] bg-[var(--card-bg)] hover:bg-[var(--card-hover)]',
    secondary: 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]',
    error: 'bg-[var(--error-bg)] text-[var(--error-text)] hover:bg-[var(--error-bg)]/80',
    gradient: 'gradient-button'
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3'
  };

  const disabledStyles = disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer';

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`
        ${baseStyles}
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${disabledStyles}
        ${className}
      `}
    >
      {children}
    </button>
  );
} 