// frontend/src/components/ui/ScrollFade.tsx
// Horizontal scroll container with fade-edge indicators.
// Shows a gradient fade on left/right edges when content overflows,
// giving a visual cue that scrolling is possible.
// Usage: <ScrollFade className="gap-3">{children}</ScrollFade>

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/cn';

export interface ScrollFadeProps {
  children: React.ReactNode;
  className?: string;
  /** Extra classes applied to the inner scrollable div */
  innerClassName?: string;
  /** Fade width in pixels. Default 32. */
  fadeWidth?: number;
}

export function ScrollFade({
  children,
  className,
  innerClassName,
  fadeWidth = 32,
}: ScrollFadeProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showLeft, setShowLeft] = useState(false);
  const [showRight, setShowRight] = useState(false);

  const update = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    setShowLeft(scrollLeft > 4);
    setShowRight(scrollLeft + clientWidth < scrollWidth - 4);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    update();
    el.addEventListener('scroll', update, { passive: true });
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => {
      el.removeEventListener('scroll', update);
      ro.disconnect();
    };
  }, [update]);

  return (
    <div className={cn('relative', className)}>
      {/* Left fade */}
      {showLeft && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute left-0 top-0 bottom-0 z-10"
          style={{
            width: fadeWidth,
            background: 'linear-gradient(to right, rgba(249,250,251,0.95), transparent)',
          }}
        />
      )}

      {/* Scrollable content */}
      <div
        ref={scrollRef}
        className={cn('overflow-x-auto scrollbar-thin', innerClassName)}
      >
        {children}
      </div>

      {/* Right fade */}
      {showRight && (
        <div
          aria-hidden="true"
          className="pointer-events-none absolute right-0 top-0 bottom-0 z-10"
          style={{
            width: fadeWidth,
            background: 'linear-gradient(to left, rgba(249,250,251,0.95), transparent)',
          }}
        />
      )}
    </div>
  );
}
