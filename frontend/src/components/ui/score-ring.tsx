"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface ScoreRingProps {
  score: number; // 0 to 100
  size?: number; // width and height in px
  strokeWidth?: number;
  className?: string;
  showAnimation?: boolean;
  label?: string;
}

export function ScoreRing({
  score,
  size = 80,
  strokeWidth = 8,
  className,
  showAnimation = true,
  label,
}: ScoreRingProps) {
  // Clamp score between 0 and 100
  const normalizedScore = Math.max(0, Math.min(100, score || 0));
  const [animatedScore, setAnimatedScore] = React.useState(showAnimation ? 0 : normalizedScore);

  React.useEffect(() => {
    if (!showAnimation) {
      setAnimatedScore(normalizedScore);
      return;
    }
    const duration = 1200; // 1.2s animation
    const steps = 60;
    const stepTime = duration / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const progress = currentStep / steps;
      // Ease-out cubic
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(normalizedScore * easedProgress);

      if (currentStep >= steps) {
        setAnimatedScore(normalizedScore);
        clearInterval(timer);
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [normalizedScore, showAnimation]);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  // Determine color based on threshold: Green (>= 72), Amber (>= 60), Red (< 60)
  let strokeColor = "stroke-rose-500/80";
  let textColor = "text-rose-500";
  
  if (normalizedScore >= 72) {
    strokeColor = "stroke-emerald-500/80";
    textColor = "text-emerald-500";
  } else if (normalizedScore >= 60) {
    strokeColor = "stroke-amber-500/80";
    textColor = "text-amber-500";
  }

  return (
    <div
      className={cn("relative flex items-center justify-center select-none", className)}
      style={{ width: size, height: size }}
    >
      <svg className="h-full w-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        {/* Track circle */}
        <circle
          className="stroke-muted/40"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        {/* Animated fill circle */}
        <circle
          className={cn("transition-all duration-75 ease-out", strokeColor)}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="transparent"
        />
      </svg>
      {/* Centered text */}
      <div className="absolute flex flex-col items-center justify-center">
        <span className={cn("text-xl font-extrabold tracking-tighter leading-none flex items-baseline", textColor)}>
          {Math.round(animatedScore)}
          <span className="text-[10px] font-normal text-muted-foreground ml-0.5">%</span>
        </span>
        {label && (
          <span className="text-[9px] uppercase tracking-wider text-muted-foreground/80 mt-0.5 scale-90">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
