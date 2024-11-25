import React, { useRef, useState, useEffect, useCallback } from 'react';

interface SliderProps {
  min: number;
  max: number;
  value: number;
  onChange: (value: number) => void;
  className?: string;
  size?: 'sm' | 'md';
}

const Slider: React.FC<SliderProps> = ({
  min,
  max,
  value,
  onChange,
  className = '',
  size = 'md',
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localValue, setLocalValue] = useState(value);

  // Sync localValue with value prop when not dragging
  useEffect(() => {
    if (!isDragging) {
      setLocalValue(value);
    }
  }, [value, isDragging]);

  const calculateValue = useCallback(
    (clientX: number) => {
      if (ref.current) {
        const rect = ref.current.getBoundingClientRect();
        const percent = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
        return Math.max(min, Math.min(max, percent * (max - min) + min));
      }
      return value;
    },
    [min, max, value]
  );

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    const newValue = calculateValue(e.clientX);
    setLocalValue(newValue);
    onChange(newValue);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const newValue = calculateValue(e.clientX);
      setLocalValue(newValue);
      onChange(newValue);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, calculateValue, onChange]);

  const handleClick = (e: React.MouseEvent) => {
    handleMouseDown(e);
  };

  const trackHeight = size === 'sm' ? 'h-1' : 'h-1.5';
  const thumbPosition = ((localValue - min) / (max - min)) * 100;

  return (
    <div
      ref={ref}
      className={`relative ${trackHeight} rounded-full bg-[var(--text-secondary)]/20 
                 group hover:cursor-pointer ${className}`}
      onMouseDown={handleMouseDown}
    >
      <div
        className="absolute left-0 top-0 h-full rounded-full bg-[var(--text-secondary)] 
                   group-hover:bg-[var(--text-primary)] transition-colors"
        style={{ width: `${thumbPosition}%` }}
      />
    </div>
  );
};

export default React.memo(Slider);