"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FlaskConical,
  LayoutDashboard,
  FileText,
  GitBranch,
  Rocket,
  Sparkles,
  Link2,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/pipelines", label: "Pipelines", icon: GitBranch },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/connectors", label: "Data Connectors", icon: Link2 },
  { href: "/playground", label: "Query Playground", icon: FlaskConical },
  { href: "/evaluations", label: "Evaluations", icon: Sparkles },
  { href: "/deployments", label: "Deployments", icon: Rocket },
];

export function AppSidebar() {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  const [isMounted, setIsMounted] = React.useState(false);

  // Sync collapse state with localStorage on mount
  React.useEffect(() => {
    const saved = localStorage.getItem("sidebar-collapsed");
    if (saved === "true") {
      setIsCollapsed(true);
    }
    setIsMounted(true);
  }, []);

  const toggleCollapse = () => {
    const nextState = !isCollapsed;
    setIsCollapsed(nextState);
    localStorage.setItem("sidebar-collapsed", String(nextState));
  };

  if (!isMounted) {
    // Prevent hydration layout shift by rendering skeleton width first
    return <aside className="h-screen w-60 shrink-0 border-r border-sidebar-border bg-sidebar" />;
  }

  return (
    <aside
      className={cn(
        "relative flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-all duration-300 ease-in-out",
        isCollapsed ? "w-16" : "w-60"
      )}
    >
      {/* Collapse Toggle Button */}
      <button
        onClick={toggleCollapse}
        className="absolute -right-3 top-6 flex size-6 items-center justify-center rounded-full border border-sidebar-border bg-sidebar text-sidebar-foreground shadow-md hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-all duration-200 cursor-pointer z-50 hover:scale-105 active:scale-95"
        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {isCollapsed ? <ChevronRight className="size-3.5" /> : <ChevronLeft className="size-3.5" />}
      </button>

      {/* Top Header Logo */}
      <Link
        href="/"
        className={cn(
          "flex h-14 items-center gap-2 border-b border-sidebar-border/60 px-4 hover:bg-sidebar-accent/40 transition-colors duration-200",
          isCollapsed && "justify-center"
        )}
      >
        <img
          src="/logo.png"
          alt="AutoRAG Logo"
          className="size-7 rounded-md object-cover shadow-[0_0_10px_oklch(from_var(--primary)_l_c_h_/_0.2)]"
        />
        {!isCollapsed && (
          <span className="text-sm font-bold tracking-tight bg-linear-to-r from-foreground to-primary bg-clip-text text-transparent">
            AutoRAG
          </span>
        )}
      </Link>

      {/* User / Org Section */}
      <div
        className={cn(
          "flex items-center gap-3 px-4 py-3 border-b border-sidebar-border/60 bg-sidebar/30",
          isCollapsed && "justify-center"
        )}
      >
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xs shadow-inner">
          AR
        </div>
        {!isCollapsed && (
          <div className="flex flex-col min-w-0">
            <span className="text-xs font-semibold text-foreground leading-none truncate">
              AutoRAG Workspace
            </span>
            <span className="text-[10px] text-muted-foreground mt-0.5 leading-none">
              Enterprise Plan
            </span>
          </div>
        )}
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/dashboard" ? pathname === "/dashboard" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              title={isCollapsed ? label : undefined}
              className={cn(
                "group relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all duration-200 cursor-pointer",
                active
                  ? "bg-primary/10 text-primary shadow-[inset_0_0_12px_oklch(from_var(--primary)_l_c_h_/_0.06)]"
                  : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                isCollapsed && "justify-center px-0 py-2.5"
              )}
            >
              {/* Active marker pill */}
              {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-r-md bg-primary" />
              )}
              <Icon
                className={cn(
                  "size-4 shrink-0 transition-transform duration-200 group-hover:scale-110",
                  active ? "text-primary" : "text-muted-foreground group-hover:text-sidebar-accent-foreground"
                )}
              />
              {!isCollapsed && (
                <span className="transition-opacity duration-300 truncate">{label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div
        className={cn(
          "flex items-center gap-2.5 border-t border-sidebar-border/60 px-4 py-3 bg-sidebar/20",
          isCollapsed && "justify-center"
        )}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        {!isCollapsed && (
          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-emerald-500 uppercase tracking-wider leading-none">
              Systems Live
            </span>
            <span className="text-[9px] text-muted-foreground mt-0.5 leading-none">
              AutoRAG · v0.1
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}
