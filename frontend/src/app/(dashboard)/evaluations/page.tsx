"use client";

import { useEffect, useState, useTransition } from "react";
import useSWR from "swr";
import { 
  BarChart3, 
  Loader2, 
  Sparkles, 
  Activity, 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  Play, 
  RefreshCw,
  GitBranch,
  Check,
  AlertCircle
} from "lucide-react";

import { api, APIError, fetcher } from "@/lib/api";
import type { EvaluationResult, Pipeline } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { ScoreRing } from "@/components/ui/score-ring";
import { ProgressBar } from "@/components/ui/progress-bar";
import { EmptyState } from "@/components/ui/empty-state";

export default function Evaluations() {
  const { data: pipelines, isLoading: pipelinesLoading } = useSWR<Pipeline[]>(
    "/pipelines",
    fetcher,
  );
  
  const [pipelineId, setPipelineId] = useState("");
  const [runId, setRunId] = useState("");
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!pipelineId && pipelines?.length) {
      setPipelineId(pipelines[0].id);
    }
  }, [pipelines, pipelineId]);

  const pollScore = async (id: string) => {
    for (let i = 0; i < 60; i++) {
      const data = await api.getScore(id);
      if ("unified_score" in data) {
        setResult(data as EvaluationResult);
        setStatus("completed");
        return;
      }
      setStatus(data.status);
      if (data.status === "failed") return;
      await new Promise((r) => setTimeout(r, 3000));
    }
  };

  const onEvaluate = () => {
    setError(null);
    setResult(null);
    setStatus("Initiating validation environment...");
    startTransition(async () => {
      try {
        const queued = await api.evaluate(pipelineId);
        setRunId(queued.run_id);
        setStatus("queued");
        await pollScore(queued.run_id);
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Evaluation failed");
      }
    });
  };

  const pipelineOptions = pipelines
    ? pipelines.map((p) => ({
        value: p.id,
        label: p.name,
        description: `ID: ${p.id.slice(0, 8)}...`
      }))
    : [];

  // Polling timeline status mapping
  const getTimelineMessage = (currStatus: string | null) => {
    if (!currStatus) return "";
    switch (currStatus.toLowerCase()) {
      case "queued":
        return "Initializing evaluation environment...";
      case "pre_processing":
        return "Compiling test dataset & generating answers...";
      case "running":
        return "Scoring pipeline outputs via judge agents...";
      case "scoring":
        return "Calculating cosine distance and RAGAS weights...";
      default:
        return currStatus;
    }
  };

  return (
    <>
      <PageHeader
        title="Evaluations"
        description="Unified Score, RAGAS, and adversarial validation benchmarks."
      />

      <div className="mx-auto max-w-4xl space-y-6 p-8">
        
        {/* Pipeline Selector Card */}
        <Card variant="glass">
          <CardContent className="space-y-4 pt-6">
            <div className="flex items-center gap-2 border-b border-border/40 pb-3">
              <GitBranch className="size-4.5 text-primary" />
              <span className="text-sm font-bold">Select Pipeline to Bench</span>
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
                    setResult(null);
                    setRunId("");
                  }}
                  options={pipelineOptions}
                  disabled={isPending}
                  className="max-w-md"
                />

                <Button 
                  onClick={onEvaluate} 
                  disabled={isPending || !pipelineId}
                  variant="glow"
                  className="cursor-pointer h-10 px-6"
                >
                  {isPending ? (
                    <>
                      <Loader2 className="mr-1.5 size-4 animate-spin" />
                      Evaluating...
                    </>
                  ) : (
                    <>
                      <Play className="mr-1.5 size-4" />
                      Run Evaluation
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">
                No active pipelines found. Please create one on the Pipelines page.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Polling/Running Status Tracker */}
        {isPending && status && (
          <Card variant="gradient-border" className="animate-fade-in-up">
            <CardContent className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-border/40 pb-3">
                <span className="text-xs font-bold text-foreground">Benchmark Job Tracker</span>
                <Badge variant="outline" className="animate-pulse">
                  Active Run
                </Badge>
              </div>

              {/* Visual Timeline Stepper */}
              <div className="relative pl-6 border-l border-border/60 ml-2 space-y-4 text-xs">
                <div className="flex items-center gap-2">
                  <span className={`size-2 rounded-full ${["queued", "pre_processing", "running", "scoring", "completed"].includes(status.toLowerCase()) ? "bg-emerald-500" : "bg-primary animate-pulse"}`} />
                  <span className="font-semibold">Queue Context Registered</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`size-2 rounded-full ${["pre_processing", "running", "scoring", "completed"].includes(status.toLowerCase()) ? "bg-emerald-500" : status === "queued" ? "bg-primary animate-pulse" : "bg-muted"}`} />
                  <span className="font-semibold">Compile Test Cases</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`size-2 rounded-full ${["running", "scoring", "completed"].includes(status.toLowerCase()) ? "bg-emerald-500" : status === "pre_processing" ? "bg-primary animate-pulse" : "bg-muted"}`} />
                  <span className="font-semibold">Judge Evaluator Run</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`size-2 rounded-full ${status === "completed" ? "bg-emerald-500" : ["running", "scoring"].includes(status.toLowerCase()) ? "bg-primary animate-pulse" : "bg-muted"}`} />
                  <span className="font-semibold">Benchmarking Summary Scores</span>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between border-t border-border/20 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <Clock className="size-3.5" />
                  Status: {getTimelineMessage(status)}
                </span>
                {runId && <span className="font-mono text-[10px]">ID: {runId.slice(0, 8)}...</span>}
              </div>
            </CardContent>
          </Card>
        )}

        {error ? (
          <div className="flex items-center gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-3 text-sm text-destructive">
            <AlertCircle className="size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        {/* Evaluation Scores Results Overview */}
        {result ? (
          <div className="space-y-6 animate-fade-in-up">
            
            {/* Unified Score Hero Section */}
            <Card variant="glass" className="relative overflow-hidden">
              <div className="absolute inset-0 bg-linear-to-r from-primary/5 to-transparent pointer-events-none" />
              <CardContent className="p-8 flex flex-col md:flex-row items-center justify-between gap-8">
                
                {/* Unified Radial Gauge */}
                <div className="flex items-center gap-6">
                  <ScoreRing 
                    score={result.unified_score * 100} 
                    size={130} 
                    strokeWidth={10} 
                    label="Unified" 
                  />
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">
                      Validation Verdict
                    </span>
                    <h3 className="text-xl font-extrabold text-foreground">
                      Golden Set Score Summary
                    </h3>
                    <p className="text-xs text-muted-foreground max-w-sm leading-normal">
                      The unified index merges precision, faithfulness, cost weighting, and adversarial safety limits.
                    </p>
                  </div>
                </div>

                {/* Verdict Badge */}
                <div className="flex flex-col items-center md:items-end gap-2.5">
                  <Badge variant={result.deploy_eligible ? "secondary" : "outline"} className={
                    result.deploy_eligible 
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 px-3 py-1 text-xs font-bold uppercase tracking-wider animate-glow-pulse" 
                      : "bg-rose-500/10 text-rose-400 border-rose-500/20 px-3 py-1 text-xs font-bold uppercase tracking-wider"
                  }>
                    {result.deploy_eligible ? "Gate Approved" : "Gate Rejected"}
                  </Badge>
                  <span className="text-[10px] text-muted-foreground text-center md:text-right">
                    Deploy threshold limit: <strong className="text-primary font-bold">&ge; 72%</strong>
                  </span>
                </div>

              </CardContent>
            </Card>

            {/* Score Breakdown Grid */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              
              <Card variant="glass">
                <CardContent className="p-5 flex flex-col items-center gap-3 text-center">
                  <ScoreRing score={result.retrieval_score * 100} size={70} strokeWidth={6} />
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-foreground">Retrieval Score</p>
                    <p className="text-[10px] text-muted-foreground">Cosine search alignment</p>
                  </div>
                </CardContent>
              </Card>

              <Card variant="glass">
                <CardContent className="p-5 flex flex-col items-center gap-3 text-center">
                  <ScoreRing score={result.quality_score * 100} size={70} strokeWidth={6} />
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-foreground">Quality Score</p>
                    <p className="text-[10px] text-muted-foreground">Answer structure index</p>
                  </div>
                </CardContent>
              </Card>

              <Card variant="glass">
                <CardContent className="p-5 flex flex-col items-center gap-3 text-center">
                  <ScoreRing score={result.faithfulness_score * 100} size={70} strokeWidth={6} />
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-foreground">Faithfulness</p>
                    <p className="text-[10px] text-muted-foreground">Hallucination safeguards</p>
                  </div>
                </CardContent>
              </Card>

              <Card variant="glass">
                <CardContent className="p-5 flex flex-col items-center gap-3 text-center">
                  <ScoreRing 
                    score={result.adversarial_pass_rate != null ? result.adversarial_pass_rate * 100 : 0} 
                    size={70} 
                    strokeWidth={6} 
                  />
                  <div className="space-y-0.5">
                    <p className="text-xs font-bold text-foreground">Adversarial Pass</p>
                    <p className="text-[10px] text-muted-foreground">Injection vector immunity</p>
                  </div>
                </CardContent>
              </Card>

            </div>

            {/* Diagnostic Recommendation Panel */}
            {result.diagnosis && result.diagnosis.length > 0 && (
              <Card variant="glass">
                <CardHeader className="pb-3 border-b border-border/40">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="size-4.5 text-amber-500" />
                    <CardTitle className="text-md">Evaluation Diagnosis & Warnings</CardTitle>
                  </div>
                  <CardDescription>
                    Contextual recommendations to tune chunk bounds and retrieval anchors.
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6 space-y-4">
                  {result.diagnosis.map((diagnose, index) => (
                    <div 
                      key={index} 
                      className="flex gap-3 items-start pb-3 border-b border-border/20 last:border-0 last:pb-0"
                    >
                      <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-amber-400">
                        <AlertCircle className="size-3.5" />
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-xs font-bold text-foreground">{diagnose}</p>
                        <p className="text-[11px] text-muted-foreground leading-normal">
                          Improve score threshold outputs by adjusting pipeline hyper-parameters or reviewing source document parsing rules.
                        </p>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

          </div>
        ) : !isPending && (
          <div className="py-8">
            <EmptyState
              title="No Evaluation Run Yet"
              description="Evaluations run pipelines against frozen validation sheets, yielding precision metrics, faithfulness rankings, and security check approvals."
              icon={BarChart3}
              actionLabel="Run Evaluation Check"
              onAction={onEvaluate}
            />
          </div>
        )}

      </div>
    </>
  );
}
