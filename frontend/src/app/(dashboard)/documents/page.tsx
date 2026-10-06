"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import useSWR from "swr";
import { 
  CheckCircle2, 
  FileUp, 
  Loader2, 
  Plus, 
  Trash2, 
  Upload, 
  Link2, 
  Youtube, 
  Globe, 
  FileText, 
  Check, 
  AlertCircle,
  FileCode,
  Sparkles,
  Server,
  Layers,
  ArrowRight
} from "lucide-react";

import { api, APIError, fetcher } from "@/lib/api";
import { FILE_ACCEPT, SUPPORTED_FORMAT_LABELS } from "@/lib/supported-formats";
import type { DocumentRecord, JobStatus, Pipeline } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Select } from "@/components/ui/select";
import { ProgressBar } from "@/components/ui/progress-bar";

async function pollJob(documentId: string, maxAttempts = 60): Promise<JobStatus> {
  let last: JobStatus | null = null;
  for (let i = 0; i < maxAttempts; i++) {
    last = await api.getJob(documentId);
    if (last.status === "completed" || last.status === "failed") {
      return last;
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  return last ?? api.getJob(documentId);
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatUploadedAt(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function Documents() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { data: pipelines, mutate: mutatePipelines, isLoading: pipelinesLoading } = useSWR<
    Pipeline[]
  >("/pipelines", fetcher);

  const [pipelineId, setPipelineId] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [creatingPipeline, setCreatingPipeline] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"file" | "url">("file");
  const [ingestUrl, setIngestUrl] = useState("");

  const { toast } = useToast();
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: "",
    description: "",
    onConfirm: () => {},
  });

  const selectedPipeline = pipelineId.trim();
  const activePipeline = pipelines?.find((p) => p.id === selectedPipeline);

  const docsKey = selectedPipeline
    ? `/ingest/documents?pipeline_id=${selectedPipeline}`
    : null;
  const { data: documents, mutate: mutateDocs, isLoading: docsLoading } = useSWR<
    DocumentRecord[]
  >(docsKey, fetcher, {
    refreshInterval: (latest) => {
      const pending = latest?.some((d) =>
        ["queued", "pre_processing", "processing"].includes(d.status),
      );
      return pending ? 3000 : 0;
    },
  });

  useEffect(() => {
    if (!pipelineId && pipelines?.length) {
      setPipelineId(pipelines[0].id);
    }
  }, [pipelines, pipelineId]);

  const pickFile = useCallback((file: File | null) => {
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  }, []);

  const onCreatePipeline = () => {
    setError(null);
    setCreatingPipeline(true);
    api
      .createPipeline({
        name: `Pipeline ${new Date().toLocaleString()}`,
        chunking_strategy: "semantic",
        retrieval_method: "hybrid",
      })
      .then((p) => {
        setPipelineId(p.id);
        toast(`Pipeline "${p.name}" created successfully.`, "success");
        return mutatePipelines();
      })
      .catch((e) => {
        setError(e instanceof APIError ? e.message : "Failed to create pipeline");
        toast(e instanceof APIError ? e.message : "Failed to create pipeline", "error");
      })
      .finally(() => setCreatingPipeline(false));
  };

  const onUpload = () => {
    if (!selectedFile || !selectedPipeline) return;
    setError(null);
    setJob(null);
    startTransition(async () => {
      try {
        const ingested = await api.ingest(selectedPipeline, selectedFile);
        toast(`Upload success! Ingestion queued for "${selectedFile.name}".`, "success");
        
        // Optimistic setup for job
        setJob({
          job_id: ingested.document_id,
          status: ingested.status,
          chunk_count: 0,
          error: null,
        });

        if (ingested.status === "completed" || ingested.status === "failed") {
          setJob(await api.getJob(ingested.document_id));
        } else {
          setJob(await pollJob(ingested.document_id));
        }
        setSelectedFile(null);
        await mutateDocs();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Upload failed");
        toast(e instanceof APIError ? e.message : "Upload failed", "error");
      }
    });
  };

  const onIngestUrl = () => {
    if (!ingestUrl.trim() || !selectedPipeline) return;
    setError(null);
    setJob(null);
    startTransition(async () => {
      try {
        const ingested = await api.ingestUrl(selectedPipeline, ingestUrl.trim());
        toast(`Web Crawler sync initiated for URL.`, "success");
        
        setJob({
          job_id: ingested.document_id,
          status: ingested.status,
          chunk_count: 0,
          error: null,
        });

        if (ingested.status === "completed" || ingested.status === "failed") {
          setJob(await api.getJob(ingested.document_id));
        } else {
          setJob(await pollJob(ingested.document_id));
        }
        setIngestUrl("");
        await mutateDocs();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "URL Ingestion failed");
        toast(e instanceof APIError ? e.message : "URL Ingestion failed", "error");
      }
    });
  };

  const onRetry = (documentId: string) => {
    setError(null);
    startTransition(async () => {
      try {
        const status = await api.retryJob(documentId);
        setJob(status);
        toast(`Retrying ingestion job...`, "info");
        await mutateDocs();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Retry failed");
        toast(e instanceof APIError ? e.message : "Retry failed", "error");
      }
    });
  };

  const onDelete = (doc: DocumentRecord) => {
    setConfirmDialog({
      isOpen: true,
      title: "Delete Document",
      description: `Are you sure you want to delete "${doc.filename}"? This permanently removes its chunks from the RAG pipeline search pool.`,
      onConfirm: () => {
        setError(null);
        setDeletingId(doc.id);
        startTransition(async () => {
          try {
            await api.deleteDocument(doc.id);
            toast(`Document "${doc.filename}" deleted.`, "success");
            if (job?.job_id === doc.id) setJob(null);
            await mutateDocs();
          } catch (e) {
            setError(e instanceof APIError ? e.message : "Delete failed");
            toast(e instanceof APIError ? e.message : "Delete failed", "error");
          } finally {
            setDeletingId(null);
          }
        });
      },
    });
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (!selectedPipeline) {
      setError("Pick a pipeline first.");
      return;
    }
    pickFile(e.dataTransfer.files?.[0] ?? null);
  };

  // Maps pipelines to Select options
  const pipelineOptions = pipelines 
    ? pipelines.map((p) => ({
        value: p.id,
        label: p.name,
        description: `ID: ${p.id.slice(0, 8)}...`
      }))
    : [];

  // Ingestion status timeline mapper
  const getWorkflowSteps = (status: string, errMessage: string | null) => {
    const steps = [
      { name: "Parse", desc: "Extracting raw document text", state: "pending" },
      { name: "PII Shield", desc: "Masking keys, names, credentials", state: "pending" },
      { name: "Chunking", desc: "Dividing into semantic nodes", state: "pending" },
      { name: "Embedding", desc: "Generating vector weights", state: "pending" },
      { name: "Index", desc: "Saving to vector repository", state: "pending" },
    ];

    if (status === "queued") {
      steps[0].state = "active";
    } else if (status === "pre_processing") {
      steps[0].state = "completed";
      steps[1].state = "active";
    } else if (status === "processing") {
      steps[0].state = "completed";
      steps[1].state = "completed";
      steps[2].state = "active";
      steps[3].state = "active";
    } else if (status === "completed") {
      steps.forEach((s) => (s.state = "completed"));
    } else if (status === "failed") {
      steps.forEach((s) => (s.state = "completed"));
      const lastActive = steps.find((s) => s.state === "active") || steps[4];
      lastActive.state = "failed";
    }

    return steps;
  };

  const workflowSteps = job ? getWorkflowSteps(job.status, job.error) : [];

  // File type detection icon helper
  const getFileIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (ext === "pdf") return <FileCode className="size-10 text-rose-400" />;
    if (ext === "docx" || ext === "doc") return <FileText className="size-10 text-blue-400" />;
    if (ext === "txt") return <FileText className="size-10 text-muted-foreground" />;
    return <FileUp className="size-10 text-emerald-400" />;
  };

  const getStatusDot = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed":
        return "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]";
      case "failed":
        return "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]";
      case "queued":
      case "pre_processing":
      case "processing":
        return "bg-amber-500 animate-pulse shadow-[0_0_8px_rgba(245,158,11,0.6)]";
      default:
        return "bg-muted shadow-none";
    }
  };

  return (
    <>
      <PageHeader title="Documents" description="Upload and track ingestion status." />

      <div className="mx-auto max-w-4xl space-y-6 p-8">
        
        {/* Step 1 — Select Pipeline */}
        <Card variant="glass">
          <CardContent className="space-y-4 pt-6">
            <div className="flex items-center gap-2 border-b border-border/40 pb-3">
              <div className="flex size-6 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                1
              </div>
              <span className="text-sm font-bold">Select Active Target Pipeline</span>
            </div>

            {pipelinesLoading ? (
              <div className="h-10 w-full animate-pulse bg-muted/20 rounded-md" />
            ) : pipelines && pipelines.length > 0 ? (
              <div className="flex flex-wrap items-center gap-3">
                <Select
                  value={pipelineId}
                  onChange={(val) => {
                    setPipelineId(val);
                    setError(null);
                  }}
                  options={pipelineOptions}
                  disabled={isPending}
                  className="max-w-md"
                />
                
                {activePipeline && (
                  <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-3 py-1 text-xs font-medium text-emerald-500">
                    <Check className="size-3.5 stroke-[3]" />
                    Target: {activePipeline.name}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground flex items-center justify-between">
                <span>No active pipelines found. Create one to begin.</span>
                <Button onClick={onCreatePipeline} size="sm" disabled={creatingPipeline}>
                  <Plus className="mr-1 size-3.5" />
                  {creatingPipeline ? "Creating..." : "Create Pipeline"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Step 2 — Ingestion Sandbox */}
        <Card variant="glass">
          <CardContent className="space-y-4 pt-6">
            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <div className="flex items-center gap-2">
                <div className="flex size-6 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary">
                  2
                </div>
                <span className="text-sm font-bold">Ingest Knowledge Sources</span>
              </div>

              {/* URL/File Tab Selectors */}
              <div className="flex gap-1 rounded-md bg-muted/50 p-0.5 text-xs border border-border/40">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab("file");
                    setError(null);
                  }}
                  className={cn(
                    "rounded-sm px-3 py-1.5 font-semibold transition-all cursor-pointer",
                    activeTab === "file"
                      ? "bg-background text-foreground shadow-xs border border-border/20"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <span className="flex items-center gap-1.5">
                    <FileUp className="size-3.5" />
                    File Upload
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab("url");
                    setError(null);
                  }}
                  className={cn(
                    "rounded-sm px-3 py-1.5 font-semibold transition-all cursor-pointer",
                    activeTab === "url"
                      ? "bg-background text-foreground shadow-xs border border-border/20"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <span className="flex items-center gap-1.5">
                    <Link2 className="size-3.5" />
                    Web Crawler
                  </span>
                </button>
              </div>
            </div>

            {/* File Drag Box */}
            {activeTab === "file" ? (
              <div className="space-y-4">
                <div
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click();
                  }}
                  onClick={() => {
                    if (!selectedPipeline) {
                      setError("Pick a pipeline first.");
                      return;
                    }
                    fileInputRef.current?.click();
                  }}
                  onDragEnter={(e) => {
                    e.preventDefault();
                    setDragActive(true);
                  }}
                  onDragLeave={(e) => {
                    e.preventDefault();
                    setDragActive(false);
                  }}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={onDrop}
                  className={cn(
                    "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-all duration-300",
                    dragActive
                      ? "border-primary bg-primary/5 scale-[0.99] shadow-inner"
                      : "border-border/60 hover:border-primary/50 hover:bg-muted/20",
                    !selectedPipeline && "pointer-events-none opacity-50",
                  )}
                >
                  {selectedFile ? (
                    <div className="flex flex-col items-center gap-2 animate-scale-in">
                      {getFileIcon(selectedFile.name)}
                      <span className="text-sm font-semibold truncate max-w-xs">{selectedFile.name}</span>
                      <span className="text-xs text-muted-foreground">{formatBytes(selectedFile.size)}</span>
                    </div>
                  ) : (
                    <>
                      <FileUp className="size-8 text-muted-foreground" />
                      <p className="text-sm font-medium">
                        Drag & drop a file here, or <span className="text-primary font-semibold hover:underline">browse</span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Files are parsed and encoded to vector weights in postgres
                      </p>
                    </>
                  )}
                </div>

                <div className="flex flex-wrap gap-1">
                  {SUPPORTED_FORMAT_LABELS.map((label) => (
                    <span key={label} className="text-[10px] font-medium bg-muted px-2 py-0.5 rounded-sm border border-border/40 text-muted-foreground">
                      {label}
                    </span>
                  ))}
                </div>

                <Button
                  type="button"
                  className="w-full cursor-pointer"
                  onClick={onUpload}
                  disabled={isPending || !selectedFile || !selectedPipeline}
                >
                  <FileUp className="mr-1.5 size-4" />
                  {isPending ? "Ingestion in Progress..." : "Ingest Document"}
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <p className="text-xs text-muted-foreground">
                    Connect website scrapers or submit YouTube links to extract captions and index.
                  </p>
                  <input
                    type="url"
                    placeholder="https://example.com/docs or https://youtube.com/watch?v=..."
                    value={ingestUrl}
                    onChange={(e) => setIngestUrl(e.target.value)}
                    disabled={isPending || !selectedPipeline}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>

                <div className="flex gap-4">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Youtube className="size-3.5 text-rose-500" />
                    <span>YouTube Subtitles</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Globe className="size-3.5 text-primary" />
                    <span>HTML / Web Pages</span>
                  </div>
                </div>

                <Button
                  type="button"
                  className="w-full cursor-pointer"
                  onClick={onIngestUrl}
                  disabled={isPending || !ingestUrl.trim() || !selectedPipeline}
                >
                  <Link2 className="mr-1.5 size-4" />
                  {isPending ? "Crawling..." : "Index Source URL"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {error ? (
          <div className="flex items-center gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            <AlertCircle className="size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept={FILE_ACCEPT}
          onChange={(e) => {
            pickFile(e.target.files?.[0] ?? null);
            e.target.value = "";
          }}
        />

        {/* Real-time Ingestion Pipeline visual checklist */}
        {job ? (
          <Card variant="gradient-border" className="animate-fade-in-up">
            <CardContent className="p-6 space-y-4">
              <div className="flex justify-between items-start border-b border-border/40 pb-3">
                <div className="space-y-0.5">
                  <span className="text-xs font-bold text-foreground">Ingestion Workflow Status</span>
                  <p className="font-mono text-[10px] text-muted-foreground break-all">Job Ref: {job.job_id}</p>
                </div>
                <Badge variant={job.status === "completed" ? "secondary" : "outline"} className={
                  job.status === "completed" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : ""
                }>
                  {job.status}
                </Badge>
              </div>

              {/* Stepper Checklist */}
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
                {workflowSteps.map((step, idx) => {
                  const isActive = step.state === "active";
                  const isDone = step.state === "completed";
                  const isFail = step.state === "failed";

                  return (
                    <div 
                      key={step.name} 
                      className={cn(
                        "rounded-lg p-2.5 border transition-all text-center flex flex-col items-center gap-1.5",
                        isActive ? "bg-primary/5 border-primary shadow-xs" :
                        isDone ? "bg-emerald-500/5 border-emerald-500/20 text-emerald-400" :
                        isFail ? "bg-rose-500/5 border-rose-500/20 text-rose-400" :
                        "bg-muted/10 border-border/40 text-muted-foreground/60"
                      )}
                    >
                      <div className={cn(
                        "flex size-5 items-center justify-center rounded-full text-[9px] font-bold",
                        isDone ? "bg-emerald-500 text-black" :
                        isActive ? "bg-primary text-primary-foreground animate-pulse" :
                        isFail ? "bg-rose-500 text-white" :
                        "bg-muted text-muted-foreground border border-border"
                      )}>
                        {isDone ? <Check className="size-3 stroke-[3]" /> : idx + 1}
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-[11px] font-bold leading-none">{step.name}</p>
                        <p className="text-[9px] text-muted-foreground leading-tight hidden sm:block">{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Progress Detail */}
              <div className="flex justify-between items-center text-xs pt-3 border-t border-border/20">
                <span className="text-muted-foreground flex items-center gap-1.5">
                  <Layers className="size-3.5 text-primary" />
                  Total Chunks Saved: <strong className="text-foreground">{job.chunk_count}</strong>
                </span>
                
                {job.status === "failed" || job.status === "queued" ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-8 cursor-pointer"
                    onClick={() => onRetry(job.job_id)}
                    disabled={isPending}
                  >
                    <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                    Retry Ingestion
                  </Button>
                ) : null}
              </div>
              
              {job.error && (
                <p className="text-xs text-rose-400 bg-rose-500/5 border border-rose-500/20 rounded p-2.5 mt-2">
                  Error: {job.error}
                </p>
              )}
            </CardContent>
          </Card>
        ) : null}

        {/* Document Ingestion Index Table */}
        <Card variant="glass">
          <CardContent className="space-y-4 pt-6">
            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <h4 className="text-sm font-bold text-foreground">Document Library</h4>
              <span className="text-xs text-muted-foreground">
                Showing {documents?.length ?? 0} files
              </span>
            </div>

            {!selectedPipeline ? (
              <p className="text-sm text-muted-foreground text-center py-6">Select a pipeline to view documents.</p>
            ) : docsLoading ? (
              <div className="space-y-2 py-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-8 w-full animate-pulse bg-muted/20 rounded" />
                ))}
              </div>
            ) : !documents?.length ? (
              <div className="py-6">
                <p className="text-xs text-muted-foreground text-center">
                  No documents ingested yet — upload files or crawl sites above.
                </p>
              </div>
            ) : (
              <div className="overflow-hidden rounded-lg border border-border/50 bg-background/30 backdrop-blur-md">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm text-left">
                    <thead>
                      <tr className="border-b border-border/40 bg-muted/20 text-xs font-semibold text-muted-foreground">
                        <th className="px-4 py-3">Filename</th>
                        <th className="px-4 py-3">Size</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Chunks</th>
                        <th className="px-4 py-3">Uploaded</th>
                        <th className="px-4 py-3 text-right" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/20">
                      {documents.map((doc) => (
                        <tr 
                          key={doc.id} 
                          className="hover:bg-muted/10 transition-colors duration-200"
                        >
                          <td className="max-w-[200px] truncate px-4 py-3 font-medium text-foreground" title={doc.filename}>
                            {doc.filename}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                            {formatBytes(doc.file_size)}
                          </td>
                          <td className="px-4 py-3">
                            <span className="flex items-center gap-1.5">
                              <span className={cn("size-2 rounded-full", getStatusDot(doc.status))} />
                              <span className="text-xs text-muted-foreground capitalize">
                                {doc.status.replace("_", " ")}
                              </span>
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono font-bold text-xs text-foreground">
                            {doc.chunk_count}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                            {formatUploadedAt(doc.created_at)}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              className="size-8 p-0 text-muted-foreground hover:text-rose-500 hover:bg-rose-500/5 cursor-pointer rounded-full"
                              disabled={deletingId === doc.id || isPending}
                              onClick={() => onDelete(doc)}
                              aria-label={`Delete ${doc.filename}`}
                            >
                              <Trash2 className="size-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        description={confirmDialog.description}
        onConfirm={confirmDialog.onConfirm}
        onClose={() => setConfirmDialog((prev) => ({ ...prev, isOpen: false }))}
      />
    </>
  );
}
