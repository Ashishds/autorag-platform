"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight } from "lucide-react";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  const pathname = usePathname();
  const segments = pathname ? pathname.split("/").filter(Boolean) : [];

  const getSegmentLabel = (segment: string) => {
    switch (segment.toLowerCase()) {
      case "dashboard":
        return "Overview";
      case "pipelines":
        return "Pipelines";
      case "documents":
        return "Documents";
      case "connectors":
        return "Data Connectors";
      case "playground":
        return "Query Playground";
      case "evaluations":
        return "Evaluations";
      case "deployments":
        return "Deployments";
      default:
        return segment.charAt(0).toUpperCase() + segment.slice(1);
    }
  };

  return (
    <div className="flex items-start justify-between gap-4 border-b border-border px-8 py-6 animate-fade-in-up">
      <div className="space-y-1.5">
        {/* Breadcrumbs */}
        {segments.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1 select-none">
            <span className="hover:text-foreground transition-colors">AutoRAG</span>
            {segments.map((segment, index) => {
              const href = "/" + segments.slice(0, index + 1).join("/");
              const isLast = index === segments.length - 1;
              const label = getSegmentLabel(segment);
              return (
                <div key={href} className="flex items-center gap-1.5">
                  <ChevronRight className="size-3 text-muted-foreground/60" />
                  {isLast ? (
                    <span className="font-medium text-foreground">{label}</span>
                  ) : (
                    <Link href={href} className="hover:text-foreground transition-colors">
                      {label}
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        )}

        <div className="relative inline-block pb-1">
          <h1 className="text-2xl font-bold tracking-tight bg-linear-to-r from-foreground via-foreground to-primary bg-clip-text text-transparent">
            {title}
          </h1>
          <span className="absolute bottom-0 left-0 h-0.5 w-12 bg-linear-to-r from-primary to-primary/20 rounded-full" />
        </div>
        {description ? (
          <p className="text-sm text-muted-foreground max-w-xl">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
