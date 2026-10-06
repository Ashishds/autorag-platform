import * as React from "react";
import { ArrowUpRight, ArrowDownRight, LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: {
    value: number | string;
    isPositive: boolean;
  };
  icon?: LucideIcon;
  sparklineData?: number[];
  variant?: "default" | "glass" | "glow" | "gradient-border";
  className?: string;
}

export function StatCard({
  title,
  value,
  description,
  trend,
  icon: Icon,
  sparklineData,
  variant = "glass",
  className,
}: StatCardProps) {
  // Generate SVG path for sparkline
  const generateSparklinePath = (data: number[]) => {
    if (!data || data.length < 2) return "";
    const width = 100;
    const height = 30;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min === 0 ? 1 : max - min;
    
    return data
      .map((val, index) => {
        const x = (index / (data.length - 1)) * width;
        const y = height - ((val - min) / range) * height + 2; // Offset slightly for boundary spacing
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  };

  const pathData = sparklineData ? generateSparklinePath(sparklineData) : "";

  return (
    <Card variant={variant} className={cn("overflow-hidden animate-fade-in-up", className)}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between space-y-0 pb-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {title}
          </p>
          {Icon && (
            <div className="rounded-md bg-primary/10 p-1.5 text-primary">
              <Icon className="h-4 w-4" />
            </div>
          )}
        </div>
        <div className="flex items-end justify-between mt-2">
          <div className="space-y-1">
            <h3 className="text-2xl font-bold tracking-tight">{value}</h3>
            {(description || trend) && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                {trend && (
                  <span
                    className={cn(
                      "flex items-center font-medium",
                      trend.isPositive ? "text-emerald-500" : "text-rose-500"
                    )}
                  >
                    {trend.isPositive ? (
                      <ArrowUpRight className="mr-0.5 h-3.5 w-3.5 shrink-0" />
                    ) : (
                      <ArrowDownRight className="mr-0.5 h-3.5 w-3.5 shrink-0" />
                    )}
                    {trend.value}%
                  </span>
                )}
                {description && <span>{description}</span>}
              </div>
            )}
          </div>
          
          {sparklineData && sparklineData.length > 1 && (
            <div className="h-8 w-24 shrink-0 overflow-visible">
              <svg className="h-full w-full overflow-visible" viewBox="0 0 100 35">
                <path
                  d={pathData}
                  fill="none"
                  stroke="oklch(from var(--primary) l c h)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
