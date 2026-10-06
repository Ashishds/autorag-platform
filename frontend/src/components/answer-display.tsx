"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const INLINE_RE = /(\*\*[^*]+\*\*|\*[^*]+\*|\[\d+\])/g;
const UL_RE = /^[*-]\s+/;
const OL_RE = /^\d+\.\s+/;

function CitationBadge({
  n,
  onClick,
}: {
  n: number;
  onClick: (index: number) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onClick(n)}
      className="mx-0.5 inline-flex size-5 -translate-y-px items-center justify-center rounded bg-primary/15 align-middle text-[10px] font-bold text-primary hover:bg-primary/30"
      title={`Jump to source ${n}`}
    >
      {n}
    </button>
  );
}

function renderInline(text: string, onCitationClick: (index: number) => void): ReactNode[] {
  const parts = text.split(INLINE_RE).filter(Boolean);
  return parts.map((part, i) => {
    const cite = part.match(/^\[(\d+)\]$/);
    if (cite) {
      return (
        <CitationBadge
          key={`c-${i}-${cite[1]}`}
          n={Number.parseInt(cite[1], 10)}
          onClick={onCitationClick}
        />
      );
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={`b-${i}`} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={`i-${i}`}>{part.slice(1, -1)}</em>;
    }
    return <span key={`t-${i}`}>{part}</span>;
  });
}

type Block =
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] };

function parseBlocks(answer: string): Block[] {
  const blocks: Block[] = [];
  let ul: string[] = [];
  let ol: string[] = [];

  const flush = () => {
    if (ul.length) {
      blocks.push({ type: "ul", items: ul });
      ul = [];
    }
    if (ol.length) {
      blocks.push({ type: "ol", items: ol });
      ol = [];
    }
  };

  for (const raw of answer.split("\n")) {
    const line = raw.trim();
    if (!line) {
      flush();
      continue;
    }
    if (UL_RE.test(line)) {
      if (ol.length) {
        blocks.push({ type: "ol", items: ol });
        ol = [];
      }
      ul.push(line.replace(UL_RE, ""));
      continue;
    }
    if (OL_RE.test(line)) {
      if (ul.length) {
        blocks.push({ type: "ul", items: ul });
        ul = [];
      }
      ol.push(line.replace(OL_RE, ""));
      continue;
    }
    flush();
    blocks.push({ type: "p", text: line });
  }
  flush();
  return blocks;
}

export function AnswerDisplay({
  answer,
  onCitationClick,
  className,
}: {
  answer: string;
  onCitationClick: (index: number) => void;
  className?: string;
}) {
  const blocks = parseBlocks(answer);

  return (
    <div className={cn("space-y-3 text-sm leading-relaxed text-foreground/90", className)}>
      {blocks.map((block, i) => {
        if (block.type === "p") {
          return (
            <p key={`p-${i}`}>{renderInline(block.text, onCitationClick)}</p>
          );
        }
        if (block.type === "ul") {
          return (
            <ul key={`ul-${i}`} className="list-disc space-y-1.5 pl-5">
              {block.items.map((item, j) => (
                <li key={`uli-${i}-${j}`}>{renderInline(item, onCitationClick)}</li>
              ))}
            </ul>
          );
        }
        return (
          <ol key={`ol-${i}`} className="list-decimal space-y-1.5 pl-5">
            {block.items.map((item, j) => (
              <li key={`oli-${i}-${j}`}>{renderInline(item, onCitationClick)}</li>
            ))}
          </ol>
        );
      })}
    </div>
  );
}
