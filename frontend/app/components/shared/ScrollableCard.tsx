import { memo, useRef, useCallback, useState, useEffect } from 'react';
import Card from './Card';

interface ScrollableCardProps {
  children: React.ReactNode;
  className?: string;
  maxHeight?: string;
}

export default memo(function ScrollableCard({ 
  children, 
  className = '',
  maxHeight = '600px'
}: ScrollableCardProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showTopGradient, setShowTopGradient] = useState(false);
  const [showBottomGradient, setShowBottomGradient] = useState(true);

  const handleScroll = useCallback(() => {
    if (!scrollRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const isAtTop = scrollTop < 10;
    const isAtBottom = Math.ceil(scrollTop + clientHeight) >= scrollHeight - 10;

    setShowTopGradient(!isAtTop);
    setShowBottomGradient(!isAtBottom);
  }, []);

  useEffect(() => {
    const scrollElement = scrollRef.current;
    if (scrollElement) {
      scrollElement.addEventListener('scroll', handleScroll);
      handleScroll();
    }
    return () => scrollElement?.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return (
    <div className="relative">
      {/* Top gradient fade */}
      <div 
        className={`absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-[var(--card-bg)] to-transparent 
                    pointer-events-none z-10 transition-opacity duration-200`}
        style={{ opacity: showTopGradient ? 1 : 0 }}
      />
      
      <Card className={className}>
        <div 
          ref={scrollRef} 
          className="overflow-y-auto custom-scrollbar"
          style={{ maxHeight }}
        >
          {children}
        </div>
      </Card>

      {/* Bottom gradient fade */}
      <div 
        className={`absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[var(--card-bg)] to-transparent 
                    pointer-events-none z-10 transition-opacity duration-200`}
        style={{ opacity: showBottomGradient ? 1 : 0 }}
      />
    </div>
  );
}); 