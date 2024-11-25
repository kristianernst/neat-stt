interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function LoadingSpinner({ size = 'md', className = '' }: LoadingSpinnerProps) {
  const sizeStyles = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  return (
    <div className={`
      animate-spin border-4 border-[var(--gradient-start)] 
      border-t-transparent rounded-full
      ${sizeStyles[size]}
      ${className}
    `} />
  );
} 