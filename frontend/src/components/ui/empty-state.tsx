import * as React from "react";
import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title: string;
  description: string;
  icon: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center p-8 border border-dashed border-border rounded-xl bg-card/30 backdrop-blur-xs max-w-md mx-auto animate-fade-in-up",
        className
      )}
    >
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary mb-4 animate-float">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-sm font-semibold tracking-tight text-foreground">{title}</h3>
      <p className="text-xs text-muted-foreground mt-1.5 mb-5 max-w-[280px]">
        {description}
      </p>
      {actionLabel && onAction && (
        <Button onClick={onAction} size="sm" variant="outline" className="text-xs hover:border-primary/50 transition-all">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
