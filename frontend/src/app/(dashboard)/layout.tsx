import type { ReactNode } from "react";
import { AppSidebar } from "@/components/app-sidebar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar />
      <main className="relative flex-1 overflow-y-auto noise-overlay flex flex-col">
        <div className="flex-1 animate-fade-in-up">
          {children}
        </div>
      </main>
    </div>
  );
}
