"use client";

import React, { useEffect } from "react";
import { AlertTriangle, X } from "lucide-react";
import { Button } from "./button";

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDestructive = true,
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  // Listen for Escape key to close dialog
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl animate-in scale-in duration-200"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
      >
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={`mt-0.5 flex size-10 shrink-0 items-center justify-center rounded-full ${
            isDestructive ? "bg-destructive/10 text-destructive" : "bg-primary/10 text-primary"
          }`}>
            <AlertTriangle className="size-5" />
          </div>
          <div className="flex-1 space-y-1.5">
            <h3 id="confirm-dialog-title" className="text-lg font-semibold text-foreground flex items-center justify-between">
              {title}
              <button 
                onClick={onClose} 
                className="text-muted-foreground hover:text-foreground hover:opacity-100 cursor-pointer"
                aria-label="Close dialog"
              >
                <X className="size-4" />
              </button>
            </h3>
            <p id="confirm-dialog-description" className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
          </div>
        </div>

        {/* Footer actions */}
        <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
          <Button variant="ghost" onClick={onClose}>
            {cancelLabel}
          </Button>
          <Button
            variant={isDestructive ? "destructive" : "default"}
            onClick={() => {
              onConfirm();
              onClose();
            }}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
