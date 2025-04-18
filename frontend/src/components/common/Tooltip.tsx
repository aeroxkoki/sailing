import React, { useState, useRef, useEffect } from 'react';

interface TooltipProps {
  children: React.ReactNode;
  content: React.ReactNode;
  position?: 'top' | 'right' | 'bottom' | 'left';
  delay?: number;
  className?: string;
}

const positionStyles = {
  top: 'bottom-full left-1/2 transform -translate-x-1/2 -translate-y-2 mb-1',
  right: 'left-full top-1/2 transform -translate-y-1/2 translate-x-2 ml-1',
  bottom: 'top-full left-1/2 transform -translate-x-1/2 translate-y-2 mt-1',
  left: 'right-full top-1/2 transform -translate-y-1/2 -translate-x-2 mr-1',
};

const arrowStyles = {
  top: 'top-full left-1/2 transform -translate-x-1/2 border-t-2 border-r-2 border-transparent border-gray-800',
  right: 'right-full top-1/2 transform -translate-y-1/2 border-r-2 border-b-2 border-transparent border-gray-800',
  bottom: 'bottom-full left-1/2 transform -translate-x-1/2 border-b-2 border-l-2 border-transparent border-gray-800',
  left: 'left-full top-1/2 transform -translate-y-1/2 border-l-2 border-t-2 border-transparent border-gray-800',
};

const Tooltip: React.FC<TooltipProps> = ({
  children,
  content,
  position = 'top',
  delay = 300,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleMouseEnter}
      onBlur={handleMouseLeave}
    >
      {children}
      {isVisible && (
        <div
          ref={tooltipRef}
          className={`
            absolute z-50 px-2 py-1 text-xs font-medium text-white
            bg-gray-800 rounded shadow-lg whitespace-nowrap
            ${positionStyles[position]}
            ${className}
          `}
          role="tooltip"
        >
          {content}
          <div 
            className={`
              absolute w-2 h-2 bg-gray-800 transform rotate-45
              ${arrowStyles[position]}
            `}
          />
        </div>
      )}
    </div>
  );
};

export default Tooltip;