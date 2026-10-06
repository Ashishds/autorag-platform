"use client";

import { useEffect, useState, useTransition } from "react";
import useSWR from "swr";
import { 
  Rocket, 
  RotateCcw, 
  GitBranch, 
  Clock, 
  ShieldCheck, 
  Check, 
  X, 
  Sliders, 
  Layers, 
  AlertTriangle,
  History as HistoryIcon
} from "lucide-react";

import { api, APIError, fetcher } from "@/lib/api";
import type { Experiment, Pipeline, RunSummary } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";
import { useToast } from "@/components/ui/toast";

const REVIEWER_ID = "00000000-0000-0000-0000-000000000000";

export default function Deployments() {
  const { toast } = useToast();
  const { data: pipelines, isLoading: pipelinesLoading } = useSWR<Pipeline[]>(
    "/pipelines",
    fetcher,
  );
  const [pipelineId, setPipelineId] = useState("");
  const [runId, setRunId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!pipelineId && pipelines?.length) {
      setPipelineId(pipelines[0].id);
    }
  }, [pipelines, pipelineId]);

  const { data: experiments, mutate } = useSWR<Experiment[]>(
    pipelineId ? `/experiments?pipeline_id=${pipelineId}` : null,
    fetcher,
  );

  const { data: runs } = useSWR<RunSummary[]>(
    pipelineId ? `/runs?pipeline_id=${pipelineId}` : null,
    fetcher,
  );

  // Auto-select eligible run on mount/pipeline change
  useEffect(() => {
    if (!runs || runs.length === 0) return;
    const eligible = runs.find((r) => r.deploy_eligible);
    const completed = runs.find((r) => r.status === "completed");
    setRunId((eligible ?? completed ?? runs[0])?.run_id ?? "");
  }, [runs]);

  const onDeploy = () => {
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const dep = await api.deploy(pipelineId, runId);
        setMessage(`Deployed production candidate successfully! (Ref: ${dep.id})`);
        toast(`Config variant deployed to active Gateway.`, "success");
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Deploy failed");
      }
    });
  };

  const onRollback = () => {
    setError(null);
    setMessage(null);
    startTransition(async () => {
      try {
        const res = await api.rollback(pipelineId, "Manual rollback from dashboard");
        setMessage(`Rolled back active route to deployment version: ${res.deployment_id}`);
        toast(`Gateway route redirected to previous stable version.`, "info");
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Rollback failed");
      }
    });
  };

  const onApprove = (experimentId: string, approve: boolean) => {
    startTransition(async () => {
      try {
        await api.approveExperiment(experimentId, approve, REVIEWER_ID);
        await mutate();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Approval failed");
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

  const runOptions = runs
    ? runs.map((r) => ({
        value: r.run_id,
        label: `${r.run_id.slice(0, 8)} · ${r.unified_score != null ? `${Math.round(r.unified_score * 100)}%` : "N/A"}`,
        description: `${r.deploy_eligible ? "Gate Approved" : "Gate Blocked"} (${r.status})`
      }))
    : [];

  const renderConfigDiff = (config: Record<string, any>) => {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-muted/20 border border-border/40 rounded-lg p-3.5 font-mono text-xs">
        {Object.entries(config).map(([key, val]) => (
          <div key={key} className="flex flex-col gap-0.5 border-r border-border/20 last:border-0 pr-2">
            <span className="text-[10px] text-muted-foreground uppercase">{key.replace("_", " ")}</span>
            <span className="font-semibold text-emerald-400">→ {String(val)}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <>
      <PageHeader
        title="Deployments & Approvals"
        description="Activate pipeline configs, review experiments, and rollback gateways."
      />

      <div className="mx-auto max-w-4xl space-y-6 p-8">
        
        {/* Operations Dashboard card */}
        <Card variant="glass">
          <CardContent className="space-y-5 pt-6">
            <div className="flex items-center gap-2 border-b border-border/40 pb-3">
              <Sliders className="size-4.5 text-primary" />
              <span className="text-sm font-bold">Deploy Console Configurations</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Pipeline dropdown selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Select Active Pipeline</label>
                {pipelinesLoading ? (
                  <div className="h-10 w-full animate-pulse bg-muted/20 rounded" />
                ) : pipelines && pipelines.length > 0 ? (
                  <Select
                    value={pipelineId}
                    onChange={(val) => {
                      setPipelineId(val);
                      setError(null);
                      setMessage(null);
                    }}
                    options={pipelineOptions}
                    disabled={isPending}
                  />
                ) : (
                  <p className="text-xs text-muted-foreground">No pipelines found.</p>
                )}
              </div>

              {/* Evaluation runs selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground">Select Evaluated Candidate Run</label>
                {runs && runs.length > 0 ? (
                  <Select
                    value={runId}
                    onChange={(val) => {
                      setRunId(val);
                      setError(null);
                      setMessage(null);
                    }}
                    options={runOptions}
                    disabled={isPending}
                  />
                ) : (
                  <div className="h-10 border border-dashed rounded-md bg-muted/5 flex items-center justify-center text-xs text-muted-foreground px-3">
                    No runs available. Complete evaluations first.
                  </div>
                )}
              </div>
            </div>

            {/* Glowing Action Buttons */}
            <div className="flex flex-wrap gap-2.5 pt-3 border-t border-border/20">
              <Button 
                onClick={onDeploy} 
                disabled={isPending || !pipelineId || !runId}
                variant="glow"
                className="cursor-pointer h-10 px-6 flex items-center gap-1.5"
              >
                <Rocket className="size-4 text-primary-foreground group-hover:scale-115 transition-transform" />
                Deploy Config Route
              </Button>
              <Button 
                variant="outline" 
                onClick={onRollback} 
                disabled={isPending || !pipelineId}
                className="cursor-pointer h-10 px-6 border-amber-500/20 text-amber-500 bg-amber-500/5 hover:bg-amber-500 hover:text-white"
              >
                <RotateCcw className="mr-1.5 size-4" />
                Rollback Active Gateway
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Message banners */}
        {message && (
          <div className="flex items-center gap-2.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 p-4 text-sm text-emerald-400 animate-fade-in-up">
            <Check className="size-4 shrink-0 stroke-[3]" />
            <p className="font-medium">{message}</p>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2.5 rounded-md bg-rose-500/10 border border-rose-500/20 p-4 text-sm text-rose-400 animate-fade-in-up">
            <AlertTriangle className="size-4 shrink-0" />
            <p className="font-medium">{error}</p>
          </div>
        )}

        {/* Experiments Section with timeline flowchart */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">
            Active Testing Experiments & Approvals
          </h3>

          {experiments && experiments.length > 0 ? (
            <div className="space-y-4">
              {experiments.map((exp) => {
                
                return (
                  <Card key={exp.id} variant="glass" className="overflow-hidden animate-fade-in-up">
                    <CardContent className="p-6 space-y-5">
                      
                      {/* Top metadata row */}
                      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-3">
                        <div className="space-y-0.5">
                          <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                            Experiment Reference ID
                          </span>
                          <h4 className="font-mono text-xs font-semibold text-foreground select-all">
                            {exp.id}
                          </h4>
                        </div>

                        <div className="flex items-center gap-1.5">
                          {exp.approval_tier && (
                            <Badge variant="secondary" className="bg-primary/10 text-primary border border-primary/20 text-[10px] font-semibold">
                              Tier: {exp.approval_tier}
                            </Badge>
                          )}
                          <Badge variant="outline" className={`text-[10px] font-semibold ${
                            exp.approval_status === "approved" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                            exp.approval_status === "rejected" ? "bg-rose-500/10 text-rose-400 border-rose-500/20" :
                            "bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse"
                          }`}>
                            {exp.approval_status}
                          </Badge>
                        </div>
                      </div>

                      {/* Config Param Differences */}
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-muted-foreground">Proposed Configurations Changes</p>
                        {renderConfigDiff(exp.variant_config)}
                      </div>

                      {/* Visual Status Progression Timeline Flowchart */}
                      <div className="pt-2">
                        <p className="text-xs font-semibold text-muted-foreground mb-3">Status Progression</p>
                        <div className="grid grid-cols-3 gap-2 relative">
                          {/* Connector lines */}
                          <div className="absolute top-3.5 left-[15%] right-[15%] h-0.5 bg-border/40 z-0" />
                          
                          {/* Step 1: Registered */}
                          <div className="flex flex-col items-center gap-1 text-center z-10">
                            <div className="flex size-7 items-center justify-center rounded-full bg-emerald-500 text-black text-[10px] font-bold">
                              <Check className="size-3.5 stroke-[3]" />
                            </div>
                            <span className="text-[10px] font-bold text-foreground">Registered</span>
                          </div>

                          {/* Step 2: Approved / Audited */}
                          <div className="flex flex-col items-center gap-1 text-center z-10">
                            <div className={`flex size-7 items-center justify-center rounded-full text-[10px] font-bold ${
                              exp.approval_status === "approved" ? "bg-emerald-500 text-black" :
                              exp.approval_status === "rejected" ? "bg-rose-500 text-white" :
                              "bg-amber-500/20 text-amber-400 border border-amber-500"
                            }`}>
                              {exp.approval_status === "approved" ? <Check className="size-3.5 stroke-[3]" /> : 
                               exp.approval_status === "rejected" ? <X className="size-3.5" /> : 2}
                            </div>
                            <span className="text-[10px] font-bold text-foreground">Audit Checks</span>
                          </div>

                          {/* Step 3: Deployed */}
                          <div className="flex flex-col items-center gap-1 text-center z-10">
                            <div className={`flex size-7 items-center justify-center rounded-full text-[10px] font-bold ${
                              exp.approval_status === "approved" ? "bg-primary text-primary-foreground animate-pulse" : "bg-muted text-muted-foreground border border-border"
                            }`}>
                              {exp.approval_status === "approved" ? <Rocket className="size-3.5" /> : 3}
                            </div>
                            <span className="text-[10px] font-bold text-foreground">Deployed</span>
                          </div>
                        </div>
                      </div>

                      {/* Approval options for review */}
                      {exp.approval_status === "pending" && (
                        <div className="flex justify-end gap-2 pt-3 border-t border-border/20">
                          <Button 
                            size="sm" 
                            onClick={() => onApprove(exp.id, true)}
                            className="bg-emerald-500 text-black hover:bg-emerald-400 font-bold px-4 cursor-pointer"
                          >
                            Approve Variant
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => onApprove(exp.id, false)}
                            className="border-rose-500/20 text-rose-500 bg-rose-500/5 hover:bg-rose-500 hover:text-white px-4 cursor-pointer"
                          >
                            Reject Variant
                          </Button>
                        </div>
                      )}

                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="py-6">
              <EmptyState
                title="No Experiments Active"
                description="Experiments run automatically when self-improving cycles optimize settings. You can approve or reject proposed configurations changes here."
                icon={HistoryIcon}
              />
            </div>
          )}
        </div>

      </div>
    </>
  );
}
