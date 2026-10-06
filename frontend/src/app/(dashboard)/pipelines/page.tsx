"use client";

import { useState, useTransition } from "react";
import useSWR from "swr";
import Link from "next/link";
import { Plus, RefreshCw, Trash2, Upload, Settings, GitBranch, ArrowRight, X, Sliders, ChevronDown } from "lucide-react";

import { api, APIError, fetcher } from "@/lib/api";
import type { Pipeline } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Select } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";

const CHUNKING_OPTIONS = [
  { value: "auto", label: "Auto Chunking", description: "Recommended dynamic parser" },
  { value: "semantic", label: "Semantic Chunking", description: "Sentence clustering based on distance" },
  { value: "hierarchical", label: "Hierarchical Chunking", description: "Parent-child text relation structures" }
];

const RETRIEVAL_OPTIONS = [
  { value: "hybrid", label: "Hybrid Search", description: "Dense vector + keyword reciprocal rank fusion" },
  { value: "hybrid_hyde", label: "Hybrid + HyDE", description: "Search query expansion via hypothetical document" },
  { value: "dense", label: "Dense Vector Search", description: "Strict semantic vector similarity search" }
];

const JUDGE_OPTIONS = [
  { value: "gemini-2.5-pro", label: "Gemini 2.5 Pro", description: "Recommended reasoning evaluator" },
  { value: "gpt-4o", label: "GPT-4o", description: "Standard evaluation baseline judge" },
  { value: "cohere", label: "Cohere Command R+", description: "RAG-optimized contextual evaluation" }
];

const APPROVAL_OPTIONS = [
  { value: "auto", label: "Fully Autonomous", description: "Auto-deploy all score-improving variations" },
  { value: "human_in_loop", label: "Guardrails", description: "Auto-deploy low-risk; review critical score deviations" },
  { value: "mandatory_gate", label: "Mandatory Review", description: "Require manual approval sign-offs for all updates" }
];

export default function Pipelines() {
  const { data: pipelines, mutate, isLoading } = useSWR<Pipeline[]>("/pipelines", fetcher);
  
  // Pipeline creation form states
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [chunking, setChunking] = useState("auto");
  const [retrieval, setRetrieval] = useState("hybrid");
  const [judge, setJudge] = useState("gemini-2.5-pro");
  const [approvalMode, setApprovalMode] = useState("human_in_loop");

  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  // Settings editing states
  const [editingPipelineId, setEditingPipelineId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editChunking, setEditChunking] = useState("auto");
  const [editRetrieval, setEditRetrieval] = useState("hybrid");
  const [editJudge, setEditJudge] = useState("gemini-2.5-pro");
  const [editApprovalMode, setEditApprovalMode] = useState("human_in_loop");

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

  const onCreate = () => {
    setError(null);
    startTransition(async () => {
      try {
        const created = await api.createPipeline({ 
          name, 
          description: desc,
          chunking_strategy: chunking, 
          retrieval_method: retrieval,
          llm_judge: judge,
          approval_mode: approvalMode
        });
        toast(`Pipeline "${created.name}" created successfully.`, "success");
        
        // Reset state
        setName("");
        setDesc("");
        setChunking("auto");
        setRetrieval("hybrid");
        setJudge("gemini-2.5-pro");
        setApprovalMode("human_in_loop");
        setIsCreating(false);
        await mutate();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Failed to create pipeline");
        toast(e instanceof APIError ? e.message : "Failed to create pipeline", "error");
      }
    });
  };

  const onDelete = (p: Pipeline) => {
    setConfirmDialog({
      isOpen: true,
      title: "Delete Pipeline",
      description: `Are you sure you want to delete pipeline "${p.name}"? This permanently removes its documents, chunks, evaluations, and deployments. This cannot be undone.`,
      onConfirm: () => {
        setError(null);
        setDeletingId(p.id);
        startTransition(async () => {
          try {
            await api.deletePipeline(p.id);
            toast(`Pipeline "${p.name}" deleted successfully.`, "success");
            await mutate();
          } catch (e) {
            setError(e instanceof APIError ? e.message : "Failed to delete pipeline");
            toast(e instanceof APIError ? e.message : "Failed to delete pipeline", "error");
          } finally {
            setDeletingId(null);
          }
        });
      },
    });
  };

  const onSaveSettings = (pId: string) => {
    setError(null);
    startTransition(async () => {
      try {
        await api.updatePipeline(pId, {
          name: editName,
          description: editDesc,
          chunking_strategy: editChunking as any,
          retrieval_method: editRetrieval as any,
          llm_judge: editJudge,
          approval_mode: editApprovalMode as any,
        });
        toast("Pipeline settings updated successfully.", "success");
        setEditingPipelineId(null);
        await mutate();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Failed to update pipeline");
        toast(e instanceof APIError ? e.message : "Failed to update pipeline", "error");
      }
    });
  };

  return (
    <>
      <PageHeader
        title="Pipelines"
        description="Create and configure RAG pipelines (direct config)."
        actions={
          <Button variant="outline" size="sm" onClick={() => mutate()} className="cursor-pointer">
            <RefreshCw className="mr-1.5 size-3.5" />
            Refresh
          </Button>
        }
      />

      <div className="mx-auto max-w-4xl space-y-6 p-8">
        
        {/* Creation Header Control Panel */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">
              Pipeline Configurations
            </h3>
            {!isCreating && (
              <Button onClick={() => setIsCreating(true)} size="sm" className="cursor-pointer">
                <Plus className="mr-1.5 size-4" />
                New Pipeline
              </Button>
            )}
          </div>

          {/* Inline creation expandable glass card */}
          {isCreating && (
            <Card variant="gradient-border" className="overflow-hidden animate-fade-in-up duration-300">
              <CardContent className="p-6 space-y-6">
                <div className="flex items-center justify-between border-b border-border/40 pb-3">
                  <div className="flex items-center gap-2">
                    <Sliders className="size-4.5 text-primary animate-pulse" />
                    <span className="text-sm font-bold">Configure New RAG Pipeline</span>
                  </div>
                  <Button variant="ghost" size="icon" className="size-7 cursor-pointer" onClick={() => setIsCreating(false)}>
                    <X className="size-4 text-muted-foreground" />
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Pipeline Name</label>
                    <Input
                      placeholder="e.g. Finance Gold Set"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      disabled={isPending}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Description</label>
                    <Input
                      placeholder="Context details or knowledge focus area"
                      value={desc}
                      onChange={(e) => setDesc(e.target.value)}
                      disabled={isPending}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Chunking Strategy</label>
                    <Select
                      value={chunking}
                      onChange={setChunking}
                      options={CHUNKING_OPTIONS}
                      disabled={isPending}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Retrieval Method</label>
                    <Select
                      value={retrieval}
                      onChange={setRetrieval}
                      options={RETRIEVAL_OPTIONS}
                      disabled={isPending}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Judge Evaluator LLM</label>
                    <Select
                      value={judge}
                      onChange={setJudge}
                      options={JUDGE_OPTIONS}
                      disabled={isPending}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground">Automation Mode</label>
                    <Select
                      value={approvalMode}
                      onChange={setApprovalMode}
                      options={APPROVAL_OPTIONS}
                      disabled={isPending}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2.5 pt-2 border-t border-border/20">
                  <Button variant="ghost" size="sm" className="cursor-pointer" onClick={() => setIsCreating(false)}>
                    Cancel
                  </Button>
                  <Button onClick={onCreate} size="sm" disabled={isPending || !name.trim()} className="cursor-pointer">
                    {isPending ? "Creating..." : "Save Pipeline"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {error ? (
          <div className="flex items-center gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            <X className="size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2].map((i) => (
              <Card key={i} variant="glass" className="h-28 animate-pulse bg-muted/20" />
            ))}
          </div>
        ) : pipelines && pipelines.length > 0 ? (
          <div className="space-y-4">
            {pipelines.map((p) => {
              // Color border logic per status
              const borderAccent =
                p.status === "active" ? "border-l-[4px] border-l-emerald-500" :
                p.status === "error" ? "border-l-[4px] border-l-rose-500" :
                "border-l-[4px] border-l-amber-500";

              return (
                <Card 
                  key={p.id} 
                  variant="glass" 
                  className={`overflow-hidden transition-all duration-300 hover:translate-x-[2px] ${borderAccent} hover:shadow-[0_0_20px_oklch(from_var(--primary)_l_c_h_/_0.06)]`}
                >
                  <CardContent className="p-6 space-y-5">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-bold text-base text-foreground">{p.name}</h4>
                          <span className={`inline-flex items-center rounded-sm px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                            p.status === "active" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                            p.status === "error" ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" :
                            "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          }`}>
                            {p.status}
                          </span>
                        </div>
                        {p.description && (
                          <p className="text-xs text-muted-foreground max-w-xl">{p.description}</p>
                        )}
                        <span className="text-[10px] text-muted-foreground font-mono block select-all">
                          ID: {p.id}
                        </span>
                      </div>

                      {/* Controls Area */}
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline" className="bg-background/40 hover:bg-background/40 cursor-default px-2 py-0.5 text-[10px] font-semibold border-border/80">
                          {p.chunking_strategy}
                        </Badge>
                        <Badge variant="outline" className="bg-background/40 hover:bg-background/40 cursor-default px-2 py-0.5 text-[10px] font-semibold border-border/80">
                          {p.retrieval_method}
                        </Badge>
                        <Badge variant="outline" className="bg-emerald-500/5 hover:bg-emerald-500/5 cursor-default text-emerald-400 border-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold">
                          {p.approval_mode}
                        </Badge>

                        <div className="flex items-center gap-1.5 ml-2 border-l border-border/40 pl-3">
                          <Button variant="outline" size="sm" asChild className="h-8 px-2.5 cursor-pointer">
                            <Link href="/documents">
                              <Upload className="mr-1 size-3.5" />
                              Upload
                            </Link>
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 px-2.5 cursor-pointer"
                            onClick={() => {
                              if (editingPipelineId === p.id) {
                                setEditingPipelineId(null);
                              } else {
                                setEditingPipelineId(p.id);
                                setEditName(p.name);
                                setEditDesc(p.description ?? "");
                                setEditChunking(p.chunking_strategy);
                                setEditRetrieval(p.retrieval_method);
                                setEditJudge(p.llm_judge);
                                setEditApprovalMode(p.approval_mode);
                              }
                            }}
                          >
                            <Settings className="mr-1.5 size-3.5" />
                            Settings
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onDelete(p)}
                            disabled={deletingId === p.id}
                            className="h-8 px-2.5 cursor-pointer text-rose-500 hover:bg-rose-500 hover:text-white"
                          >
                            <Trash2 className="mr-1.5 size-3.5" />
                            {deletingId === p.id ? "Deleting..." : "Delete"}
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Inline Settings Slide-Down Panel */}
                    {editingPipelineId === p.id && (
                      <div className="border-t border-border/40 pt-5 space-y-4 animate-fade-in-up">
                        <div className="flex items-center gap-1.5">
                          <Sliders className="size-4 text-primary" />
                          <h5 className="text-xs font-bold text-foreground uppercase tracking-wider">
                            Modify Pipeline Settings & Rules
                          </h5>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-muted/10 rounded-lg p-4 border border-border/30">
                          <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-muted-foreground">Pipeline Name</label>
                            <Input
                              value={editName}
                              onChange={(e) => setEditName(e.target.value)}
                              placeholder="Name"
                            />
                          </div>
                          
                          <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-muted-foreground">Description</label>
                            <Input
                              value={editDesc}
                              onChange={(e) => setEditDesc(e.target.value)}
                              placeholder="Description"
                            />
                          </div>

                          <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-muted-foreground">Automation Mode</label>
                            <Select
                              value={editApprovalMode}
                              onChange={setEditApprovalMode}
                              options={APPROVAL_OPTIONS}
                            />
                          </div>

                          <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-muted-foreground">Judge Evaluator LLM</label>
                            <Select
                              value={editJudge}
                              onChange={setEditJudge}
                              options={JUDGE_OPTIONS}
                            />
                          </div>

                          <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-muted-foreground">Chunking Strategy</label>
                            <Select
                              value={editChunking}
                              onChange={setEditChunking}
                              options={CHUNKING_OPTIONS}
                            />
                          </div>

                          <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-muted-foreground">Retrieval Method</label>
                            <Select
                              value={editRetrieval}
                              onChange={setEditRetrieval}
                              options={RETRIEVAL_OPTIONS}
                            />
                          </div>
                        </div>

                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingPipelineId(null)}
                            className="cursor-pointer"
                          >
                            Cancel
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => onSaveSettings(p.id)}
                            disabled={isPending || !editName.trim()}
                            className="cursor-pointer"
                          >
                            {isPending ? "Saving..." : "Save Policy"}
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="py-8">
            <EmptyState
              title="No Pipelines Configured"
              description="A pipeline orchestrates chunking, vector indexing, retrieval and scoring methods. Create your first pipeline configuration to get started."
              icon={GitBranch}
              actionLabel="Create Pipeline"
              onAction={() => setIsCreating(true)}
            />
          </div>
        )}
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
