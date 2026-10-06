"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Copy, Play, X } from "lucide-react";

import type { Source } from "@/lib/types";
import { cn } from "@/lib/utils";

function excerptHeading(content: string): string {
  const first = content.trim().split("\n")[0]?.trim() ?? "";
  if (/^abstract$/i.test(first.replace(/[#*]/g, "").trim())) return "Abstract";
  if (/^introduction$/i.test(first.replace(/[#*]/g, "").trim())) return "Introduction";
  return "Excerpt";
}

function excerptBody(content: string): string {
  const lines = content.trim().split("\n");
  const first = lines[0]?.trim().replace(/[#*]/g, "").trim() ?? "";
  if (/^(abstract|introduction)$/i.test(first) && lines.length > 1) {
    return lines.slice(1).join("\n").trim();
  }
  return content.trim();
}

export function SourceCitationModal({
  index,
  source,
  pipelineId,
  open,
  onClose,
}: {
  index: number;
  source: Source;
  pipelineId: string;
  open: boolean;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const metadata = useMemo(
    () => ({
      chunk_id: source.chunk_id,
      document_id: source.document_id,
      filename: source.filename,
      pipeline_id: pipelineId,
      page_number: source.page_number,
      chunk_index: source.chunk_index,
      source_type: source.source_type,
      media_path: source.media_path,
    }),
    [source, pipelineId],
  );

  const metadataJson = useMemo(() => JSON.stringify(metadata, null, 2), [metadata]);

  const onCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(metadataJson);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [metadataJson]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const heading = excerptHeading(source.content);
  const body = excerptBody(source.content);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="source-modal-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-background/70 backdrop-blur-sm"
        aria-label="Close source"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative z-10 flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden",
          "rounded-xl border border-border bg-card shadow-2xl",
        )}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 id="source-modal-title" className="text-base font-semibold">
            Source [{index}]
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="size-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4">
          <section>
            <h3 className="mb-2 text-sm font-semibold">{heading}</h3>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
              {body || "(empty chunk)"}
            </p>
            {source.media_path && (
              <div className="mt-4 flex">
                <a
                  href={source.media_path}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-xs font-semibold text-white shadow-md hover:bg-red-700 transition-colors duration-200"
                >
                  <Play className="size-3.5 fill-current" />
                  Play Video Segment
                </a>
              </div>
            )}
          </section>

          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Metadata</h3>
              <button
                type="button"
                onClick={onCopy}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <Copy className="size-3.5" />
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <pre className="overflow-x-auto rounded-lg border border-border bg-muted/40 p-3 font-mono text-xs leading-relaxed text-muted-foreground">
              {metadataJson}
            </pre>
          </section>
        </div>
      </div>
    </div>
  );
}
