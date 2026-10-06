"use client";

import { useCallback, useEffect, useState, useTransition, useRef } from "react";
import useSWR from "swr";
import { 
  Check, 
  Copy, 
  MessageSquareText, 
  PlugZap, 
  TriangleAlert, 
  Sparkles, 
  Send,
  Clock,
  Cpu,
  FileSearch,
  History as HistoryIcon,
  Bot
} from "lucide-react";

import { api, APIError, fetcher } from "@/lib/api";
import type { Pipeline, QueryResult } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { AnswerDisplay } from "@/components/answer-display";
import { SourceCitationModal } from "@/components/source-citation-modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text?: string;
  result?: QueryResult;
  error?: { title: string; message: string; isConnection: boolean };
  loading?: boolean;
}

const HISTORY_KEY = "autorag-query-history";
const MAX_HISTORY = 5;

function loadHistory(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.slice(0, MAX_HISTORY) : [];
  } catch {
    return [];
  }
}

function saveHistory(items: string[]) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, MAX_HISTORY)));
}

export default function Playground() {
  const { data: pipelines, isLoading: pipelinesLoading } = useSWR<Pipeline[]>(
    "/pipelines",
    fetcher,
  );
  
  const [pipelineId, setPipelineId] = useState("");
  const [q, setQ] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [openSourceIndex, setOpenSourceIndex] = useState<number | null>(null);
  const [activeMessageResult, setActiveMessageResult] = useState<QueryResult | null>(null);
  const [history, setHistory] = useState<string[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  useEffect(() => {
    if (!pipelineId && pipelines?.length) {
      setPipelineId(pipelines[0].id);
    }
  }, [pipelines, pipelineId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const pushHistory = useCallback((query: string) => {
    const trimmed = query.trim();
    if (!trimmed) return;
    setHistory((prev) => {
      const next = [trimmed, ...prev.filter((h) => h !== trimmed)].slice(0, MAX_HISTORY);
      saveHistory(next);
      return next;
    });
  }, []);

  const onSubmit = (textToSend = q) => {
    const trimmed = textToSend.trim();
    if (!trimmed || !pipelineId) return;

    // Add user message & loading AI state
    const userMsgId = `u-${Date.now()}`;
    const assistantMsgId = `a-${Date.now()}`;
    
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", text: trimmed },
      { id: assistantMsgId, role: "assistant", loading: true }
    ]);
    
    setQ("");
    pushHistory(trimmed);

    startTransition(async () => {
      try {
        const data = await api.query({ pipeline_id: pipelineId, q: trimmed });
        
        // Update loading assistant message with actual result
        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === assistantMsgId
              ? { id: assistantMsgId, role: "assistant", result: data, text: data.answer }
              : msg
          )
        );
      } catch (e) {
        const isConn = !(e instanceof APIError);
        const errDetail = e instanceof APIError 
          ? { title: e.code, message: e.message, isConnection: false }
          : { title: "Connection Failed", message: "Failed to connect to RAG backend. Make sure standard localhost:8000 runs.", isConnection: true };

        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === assistantMsgId
              ? { id: assistantMsgId, role: "assistant", error: errDetail }
              : msg
          )
        );
      }
    });
  };

  const onCopyAnswer = async (msgId: string, answerText: string) => {
    try {
      await navigator.clipboard.writeText(answerText);
      setCopiedId(msgId);
      window.setTimeout(() => setCopiedId(null), 2000);
    } catch {
      setCopiedId(null);
    }
  };

  const openSource = (index: number, result: QueryResult) => {
    setActiveMessageResult(result);
    setOpenSourceIndex(index);
  };

  const selectedSource =
    activeMessageResult && openSourceIndex != null 
      ? activeMessageResult.sources[openSourceIndex - 1] 
      : null;

  const pipelineOptions = pipelines
    ? pipelines.map((p) => ({
        value: p.id,
        label: p.name,
        description: `ID: ${p.id.slice(0, 8)}...`
      }))
    : [];

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <>
      <PageHeader
        title="Query Playground"
        description="Synchronous FastPath query. Re-write & HyDE settings evaluated automatically."
        actions={
          messages.length > 0 ? (
            <Button variant="outline" size="sm" onClick={clearChat} className="cursor-pointer">
              Clear Conversation
            </Button>
          ) : null
        }
      />

      <div className="mx-auto max-w-4xl px-6 py-8 flex flex-col h-[calc(100vh-140px)] justify-between gap-6 relative">
        
        {/* Chat Feed Panel */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-2 custom-thin-scrollbar">
          
          {/* Empty Conversation State */}
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center py-20 gap-4 max-w-lg mx-auto animate-fade-in-up">
              <div className="flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary animate-float">
                <Bot className="size-7" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-lg font-extrabold tracking-tight bg-linear-to-r from-foreground to-primary bg-clip-text text-transparent">
                  Ask anything about your documents
                </h3>
                <p className="text-xs text-muted-foreground max-w-sm">
                  Select a pipeline configuration, submit a test prompt, and examine grounded vector references.
                </p>
              </div>

              {/* History suggestions as pills */}
              {history.length > 0 ? (
                <div className="w-full space-y-2 pt-4 border-t border-border/40 mt-4">
                  <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider flex items-center justify-center gap-1.5">
                    <HistoryIcon className="size-3" /> Recent Queries
                  </span>
                  <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1">
                    {history.map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => onSubmit(item)}
                        className="max-w-[240px] truncate rounded-full border border-border/60 bg-card hover:border-primary/50 px-3 py-1 text-xs hover:bg-muted/40 transition-all text-muted-foreground hover:text-foreground cursor-pointer"
                        title={item}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap items-center justify-center gap-1.5 pt-4">
                  {["Summarize core takeaways", "Check validation scores", "Show retrieval anchors"].map((suggest) => (
                    <button
                      key={suggest}
                      onClick={() => {
                        setQ(suggest);
                      }}
                      className="rounded-full border border-border/60 bg-card hover:border-primary/50 px-3 py-1 text-xs hover:bg-muted/40 transition-all text-muted-foreground hover:text-foreground cursor-pointer"
                    >
                      {suggest}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg) => {
                const isUser = msg.role === "user";
                
                return (
                  <div 
                    key={msg.id} 
                    className={`flex gap-4 max-w-[85%] ${
                      isUser ? "ml-auto flex-row-reverse" : "mr-auto"
                    } animate-fade-in-up`}
                  >
                    {/* Avatar circle */}
                    <div className={`flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                      isUser ? "bg-primary/10 text-primary border border-primary/20" : "bg-muted/80 text-muted-foreground border"
                    }`}>
                      {isUser ? "U" : <Bot className="size-4 text-primary" />}
                    </div>

                    {/* Chat Bubble container */}
                    <div className="space-y-2">
                      <Card variant={isUser ? "default" : "glass"} className={`p-4 ${
                        isUser ? "bg-muted/30 border-border/60 rounded-tr-none" : "rounded-tl-none"
                      }`}>
                        {msg.loading ? (
                          <div className="flex items-center gap-1.5 py-1 px-3">
                            <span className="size-2 rounded-full bg-primary animate-bounce delay-100" />
                            <span className="size-2 rounded-full bg-primary animate-bounce delay-200" />
                            <span className="size-2 rounded-full bg-primary animate-bounce delay-300" />
                          </div>
                        ) : msg.error ? (
                          <div className="flex gap-2.5 text-xs text-rose-400">
                            {msg.error.isConnection ? (
                              <PlugZap className="size-4 shrink-0 text-rose-500" />
                            ) : (
                              <TriangleAlert className="size-4 shrink-0 text-rose-500" />
                            )}
                            <div className="space-y-1">
                              <p className="font-semibold text-foreground">{msg.error.title}</p>
                              <p className="text-muted-foreground leading-normal">{msg.error.message}</p>
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-4">
                            <AnswerDisplay 
                              answer={msg.text || ""} 
                              onCitationClick={(n) => openSource(n, msg.result!)} 
                            />
                            
                            {/* Actions toolbar */}
                            {!isUser && msg.text && (
                              <div className="flex items-center justify-end pt-2 border-t border-border/20">
                                <Button 
                                  type="button" 
                                  variant="ghost" 
                                  size="sm" 
                                  className="h-7 px-2 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
                                  onClick={() => onCopyAnswer(msg.id, msg.text!)}
                                >
                                  {copiedId === msg.id ? (
                                    <>
                                      <Check className="mr-1 size-3" />
                                      Copied
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="mr-1 size-3" />
                                      Copy response
                                    </>
                                  )}
                                </Button>
                              </div>
                            )}
                          </div>
                        )}
                      </Card>

                      {/* Message Metadata Tags */}
                      {!isUser && msg.result && (
                        <div className="flex flex-wrap items-center gap-1.5 text-[9px] text-muted-foreground px-1">
                          <span className="flex items-center gap-1 bg-muted/30 px-1.5 py-0.5 rounded-sm border border-border/40">
                            <Clock className="size-2.5 text-primary" />
                            {msg.result.latency_ms} ms
                          </span>
                          <span className="flex items-center gap-1 bg-muted/30 px-1.5 py-0.5 rounded-sm border border-border/40 uppercase">
                            <Cpu className="size-2.5 text-primary" />
                            {msg.result.llm_provider}
                          </span>
                          <span className="flex items-center gap-1 bg-muted/30 px-1.5 py-0.5 rounded-sm border border-border/40">
                            <FileSearch className="size-2.5 text-primary" />
                            {msg.result.sources.length} sources
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          
          <div ref={chatBottomRef} />
        </div>

        {/* Bottom chat input container */}
        <div className="space-y-3 pt-2">
          {/* Compact Target Pipeline Select Selector */}
          {pipelines && pipelines.length > 0 && (
            <div className="flex gap-2 items-center px-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                Target Pipeline Context:
              </span>
              <Select
                value={pipelineId}
                onChange={setPipelineId}
                options={pipelineOptions}
                disabled={isPending}
                className="max-w-[220px] h-7 text-xs"
              />
            </div>
          )}

          {/* Chat Glass Bar Input */}
          <div className="relative glass-card rounded-xl border border-border/60 p-2 flex items-center shadow-lg group focus-within:border-primary/50 transition-all duration-300">
            <textarea
              placeholder={pipelinesLoading ? "Loading models..." : "Ask a grounded prompt (Ctrl+Enter to send)..."}
              rows={1}
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                  e.preventDefault();
                  onSubmit();
                }
              }}
              disabled={isPending || !pipelineId}
              className="flex-1 resize-none bg-transparent py-2.5 px-3 text-sm text-foreground focus:outline-none placeholder:text-muted-foreground max-h-24 min-h-[40px] custom-thin-scrollbar"
            />
            
            <Button 
              onClick={() => onSubmit()} 
              disabled={isPending || !pipelineId || !q.trim()}
              variant="glow"
              className="size-9 rounded-lg p-0 flex items-center justify-center shrink-0 cursor-pointer"
            >
              <Send className="size-4 text-primary-foreground" />
            </Button>
          </div>
        </div>

      </div>

      {/* Citation modal viewer */}
      {selectedSource && openSourceIndex != null && activeMessageResult ? (
        <SourceCitationModal
          index={openSourceIndex}
          source={selectedSource}
          pipelineId={pipelineId}
          open
          onClose={() => {
            setOpenSourceIndex(null);
            setActiveMessageResult(null);
          }}
        />
      ) : null}
    </>
  );
}
