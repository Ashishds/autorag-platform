"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { X, CheckCircle2, AlertTriangle, Info } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto dismiss after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`flex items-start gap-3 rounded-lg border p-4 shadow-lg animate-in slide-in-from-bottom-5 duration-300 ${
              t.type === "success"
                ? "bg-emerald-950/90 border-emerald-500/30 text-emerald-400"
                : t.type === "error"
                ? "bg-destructive/90 border-destructive/30 text-destructive-foreground"
                : "bg-zinc-900/90 border-zinc-700/30 text-zinc-200"
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {t.type === "success" && <CheckCircle2 className="size-4 text-emerald-400" />}
              {t.type === "error" && <AlertTriangle className="size-4 text-destructive-foreground" />}
              {t.type === "info" && <Info className="size-4 text-zinc-200" />}
            </div>
            <div className="flex-1 text-sm font-medium leading-relaxed">{t.message}</div>
            <button
              onClick={() => removeToast(t.id)}
              className="text-muted-foreground hover:text-foreground hover:opacity-100 shrink-0 cursor-pointer"
            >
              <X className="size-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
