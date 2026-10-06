"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ProgressBarProps {
  value: number; // 0 to 100
  label?: string;
  className?: string;
  showAnimation?: boolean;
}

export function ProgressBar({
  value,
  label,
  className,
  showAnimation = true,
}: ProgressBarProps) {
  const normalizedValue = Math.max(0, Math.min(100, value || 0));
  const [animatedWidth, setAnimatedWidth] = React.useState(showAnimation ? 0 : normalizedValue);

  React.useEffect(() => {
    if (!showAnimation) {
      setAnimatedWidth(normalizedValue);
      return;
    }
    const timer = setTimeout(() => {
      setAnimatedWidth(normalizedValue);
    }, 100);
    return () => clearTimeout(timer);
  }, [normalizedValue, showAnimation]);

  // Threshold colors for progress fills
  let progressColor = "bg-rose-500/80";
  let textColor = "text-rose-500 font-medium";
  if (normalizedValue >= 72) {
    progressColor = "bg-emerald-500/80";
    textColor = "text-emerald-500 font-medium";
  } else if (normalizedValue >= 60) {
    progressColor = "bg-amber-500/80";
    textColor = "text-amber-500 font-medium";
  }

  return (
    <div className={cn("space-y-1.5 w-full", className)}>
      {(label || value !== undefined) && (
        <div className="flex items-center justify-between text-xs">
          {label && <span className="font-medium text-muted-foreground">{label}</span>}
          <span className={cn(textColor)}>{normalizedValue}%</span>
        </div>
      )}
      <div className="h-2 w-full rounded-full bg-muted/40 overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-1000 ease-out", progressColor)}
          style={{ width: `${animatedWidth}%` }}
        />
      </div>
    </div>
  );
}
