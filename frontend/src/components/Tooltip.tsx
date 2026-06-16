import React, { useState } from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  id: string;
}

export function Tooltip({ content, children, id }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  const showTooltip = () => setIsVisible(true);
  const hideTooltip = () => setIsVisible(false);

  // Clone children to inject accessibility props (focus triggers & aria-describedby link)
  const triggerElement = React.cloneElement(children as React.ReactElement<any>, {
    'aria-describedby': id,
    onMouseEnter: showTooltip,
    onMouseLeave: hideTooltip,
    onFocus: showTooltip,
    onBlur: hideTooltip,
  });

  return (
    <div className="relative inline-block">
      {triggerElement}
      <div
        id={id}
        role="tooltip"
        aria-hidden={!isVisible}
        className={`absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 text-[10px] font-medium leading-normal tracking-wide rounded-md shadow-lg transition-all duration-150 z-50 pointer-events-none w-48 text-center border bg-surface border-surface-border text-on-surface-variant ${
          isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
        }`}
        style={{
          // Use solid high-contrast colors fallback in high-contrast themes
          borderColor: 'var(--border-glass)',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
        }}
      >
        {content}
        {/* Tooltip arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-surface"></div>
      </div>
    </div>
  );
}
