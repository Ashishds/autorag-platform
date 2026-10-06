"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import useSWR from "swr";
import {
  ArrowRight,
  FileText,
  GitBranch,
  FlaskConical,
  Rocket,
  Sparkles,
  Activity,
  CheckCircle,
  FileUp,
  CirclePlay,
  Check,
  AlertCircle,
  Clock,
  ExternalLink,
  ShieldCheck,
  Layers,
  History as HistoryIcon
} from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { ScoreRing } from "@/components/ui/score-ring";
import { fetcher } from "@/lib/api";
import type { Pipeline, DocumentRecord, RunSummary } from "@/lib/types";

const SCREENS = [
  {
    href: "/pipelines",
    title: "Pipelines",
    desc: "Create and configure RAG pipelines (direct config).",
    icon: GitBranch,
    badge: "Create pipeline",
    color: "from-blue-500/20 to-indigo-500/20 text-blue-400 border-blue-500/20",
    glow: "hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] hover:border-blue-500/30"
  },
  {
    href: "/documents",
    title: "Documents",
    desc: "Upload sources, crawl URLs and track ingestion status.",
    icon: FileText,
    badge: "Ingest knowledge",
    color: "from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/20",
    glow: "hover:shadow-[0_0_20px_rgba(16,185,129,0.15)] hover:border-emerald-500/30"
  },
  {
    href: "/playground",
    title: "Query Playground",
    desc: "Test retrieval performance in chat simulations.",
    icon: FlaskConical,
    badge: "Chat sandbox",
    color: "from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/20",
    glow: "hover:shadow-[0_0_20px_rgba(245,158,11,0.15)] hover:border-amber-500/30"
  },
  {
    href: "/evaluations",
    title: "Evaluations",
    desc: "Unified Score, RAGAS, and adversarial validations.",
    icon: Sparkles,
    badge: "Run benchmarks",
    color: "from-purple-500/20 to-pink-500/20 text-purple-400 border-purple-500/20",
    glow: "hover:shadow-[0_0_20px_rgba(168,85,247,0.15)] hover:border-purple-500/30"
  },
  {
    href: "/deployments",
    title: "Deployments & Approvals",
    desc: "Activate pipelines, review config variants, rollback.",
    icon: Rocket,
    badge: "Production gate",
    color: "from-rose-500/20 to-red-500/20 text-rose-400 border-rose-500/20",
    glow: "hover:shadow-[0_0_20px_rgba(244,63,94,0.15)] hover:border-rose-500/30"
  },
];

interface TimelineEvent {
  id: string;
  type: "pipeline" | "document" | "evaluation";
  title: string;
  desc: string;
  time: string;
  status?: string;
  score?: number;
}

export default function DashboardHome() {
  const { data: pipelines, isLoading: pipelinesLoading } = useSWR<Pipeline[]>("/pipelines", fetcher);
  
  // Select first pipeline to query docs & runs
  const primaryPipeline = pipelines?.[0];
  const pipelineId = primaryPipeline?.id ?? "";

  const { data: documents } = useSWR<DocumentRecord[]>(
    pipelineId ? `/ingest/documents?pipeline_id=${pipelineId}` : null,
    fetcher
  );

  const { data: runs } = useSWR<RunSummary[]>(
    pipelineId ? `/runs?pipeline_id=${pipelineId}` : null,
    fetcher
  );

  // Stepper completion checks
  const hasPipelines = pipelines && pipelines.length > 0;
  const hasDocuments = documents && documents.length > 0;
  const hasRuns = runs && runs.length > 0;

  // Extract latest run scores and trends
  const completedRuns = runs?.filter((r) => r.unified_score !== null) ?? [];
  const latestRun = completedRuns[0];
  const latestRunScore = latestRun?.unified_score ?? null;

  // Sparkline calculation
  const scoreHistory = completedRuns
    .map((r) => r.unified_score! * 100)
    .reverse() // oldest to newest
    .slice(-10); // last 10 runs

  // Calculate trends
  let scoreTrend = undefined;
  if (completedRuns.length >= 2) {
    const latest = completedRuns[0].unified_score! * 100;
    const prev = completedRuns[1].unified_score! * 100;
    const diff = parseFloat((latest - prev).toFixed(1));
    scoreTrend = {
      value: Math.abs(diff),
      isPositive: diff >= 0
    };
  }

  // Aggregate a clean activity feed from live lists
  const [activities, setActivities] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    const list: TimelineEvent[] = [];

    // Pipelines
    if (pipelines) {
      pipelines.forEach((p) => {
        list.push({
          id: `p-${p.id}`,
          type: "pipeline",
          title: "Pipeline Configured",
          desc: `"${p.name}" initialized with ${p.chunking_strategy} chunking.`,
          time: "Recently",
          status: p.status
        });
      });
    }

    // Documents
    if (documents) {
      documents.slice(0, 5).forEach((d) => {
        list.push({
          id: `d-${d.id}`,
          type: "document",
          title: "Document Ingested",
          desc: `"${d.filename}" parsed and chunked.`,
          time: d.created_at ? new Date(d.created_at).toLocaleDateString() : "Recently",
          status: d.status
        });
      });
    }

    // Evaluations
    if (runs) {
      runs.slice(0, 5).forEach((r) => {
        list.push({
          id: `r-${r.run_id}`,
          type: "evaluation",
          title: "Evaluation Run Completed",
          desc: `Scored against frozen golden set.`,
          time: r.created_at ? new Date(r.created_at).toLocaleDateString() : "Recently",
          score: r.unified_score ? Math.round(r.unified_score * 100) : undefined,
          status: r.status ?? "completed"
        });
      });
    }

    // Sort or just pick mixed recent events
    setActivities(list.slice(0, 6));
  }, [pipelines, documents, runs]);

  return (
    <>
      <PageHeader
        title="Dashboard Overview"
        description="Autonomous RAG optimization platform — Command center monitoring."
      />

      <div className="p-8 space-y-6 max-w-7xl mx-auto">
        
        {/* Stat Cards Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Pipelines"
            value={pipelines?.length ?? 0}
            description="Active configurations"
            icon={GitBranch}
            variant="glass"
          />
          <StatCard
            title="Documents Ingested"
            value={documents?.length ?? 0}
            description="Knowledge base assets"
            icon={FileText}
            variant="glass"
          />
          <StatCard
            title="Latest RAG Score"
            value={latestRunScore !== null ? `${Math.round(latestRunScore * 100)}%` : "N/A"}
            description={latestRunScore !== null ? "Unified Evaluator Score" : "No evaluations run yet"}
            trend={scoreTrend}
            sparklineData={scoreHistory.length > 1 ? scoreHistory : undefined}
            icon={Sparkles}
            variant="glass"
          />
          
          <Card variant="glass" className="relative overflow-hidden group">
            <div className="absolute inset-0 bg-linear-to-r from-emerald-500/5 to-transparent pointer-events-none" />
            <CardContent className="p-6 flex items-center justify-between h-full">
              <div className="space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  System Status
                </span>
                <h3 className="text-xl font-extrabold text-foreground flex items-center gap-2">
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                  </span>
                  Operational
                </h3>
                <p className="text-[10px] text-muted-foreground">All evaluators & agents online</p>
              </div>
              <Activity className="size-8 text-emerald-500/40 group-hover:scale-110 transition-transform duration-300" />
            </CardContent>
          </Card>
        </div>

        {/* Stepper & Action Grid Split Layout */}
        <div className="grid gap-6 lg:grid-cols-3">
          
          {/* Stepper + Quick Actions */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Getting Started Stepper */}
            <Card variant="glass" className="relative overflow-hidden">
              <CardHeader className="pb-3 border-b border-border/40">
                <div className="flex items-center gap-2">
                  <Layers className="size-4.5 text-primary" />
                  <CardTitle className="text-md">Getting Started Guide</CardTitle>
                </div>
                <CardDescription>
                  Three steps to establish and evaluate your first pipeline.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="relative">
                  {/* Connector Line */}
                  <div className="absolute top-4 left-4 right-4 h-0.5 bg-border/40 z-0 hidden sm:block">
                    <div 
                      className="h-full bg-primary transition-all duration-500" 
                      style={{ 
                        width: hasRuns ? "100%" : hasDocuments ? "50%" : hasPipelines ? "0%" : "0%" 
                      }} 
                    />
                  </div>

                  <ol className="grid gap-6 sm:grid-cols-3 relative z-10">
                    <li className="flex flex-col items-center sm:items-start gap-2 text-center sm:text-left">
                      <div className={`flex size-8 items-center justify-center rounded-full text-xs font-bold transition-all duration-300 ${
                        hasPipelines 
                          ? "bg-primary text-primary-foreground shadow-[0_0_12px_rgba(16,185,129,0.35)]" 
                          : "bg-muted text-muted-foreground border border-border"
                      }`}>
                        {hasPipelines ? <Check className="size-4 stroke-[3]" /> : "1"}
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-xs font-semibold">1. Create Pipeline</p>
                        <p className="text-[11px] text-muted-foreground">Initialize default parameters</p>
                      </div>
                      {!hasPipelines && (
                        <Button asChild variant="link" size="sm" className="h-auto p-0 text-xs">
                          <Link href="/pipelines">
                            Start <ArrowRight className="size-3 ml-0.5" />
                          </Link>
                        </Button>
                      )}
                    </li>

                    <li className="flex flex-col items-center sm:items-start gap-2 text-center sm:text-left">
                      <div className={`flex size-8 items-center justify-center rounded-full text-xs font-bold transition-all duration-300 ${
                        hasDocuments 
                          ? "bg-primary text-primary-foreground shadow-[0_0_12px_rgba(16,185,129,0.35)]" 
                          : "bg-muted text-muted-foreground border border-border"
                      }`}>
                        {hasDocuments ? <Check className="size-4 stroke-[3]" /> : "2"}
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-xs font-semibold">2. Upload Documents</p>
                        <p className="text-[11px] text-muted-foreground">Ingest files or site URLs</p>
                      </div>
                      {!hasDocuments && (
                        <Button asChild variant="link" size="sm" className="h-auto p-0 text-xs" disabled={!hasPipelines}>
                          <Link href="/documents">
                            Upload <ArrowRight className="size-3 ml-0.5" />
                          </Link>
                        </Button>
                      )}
                    </li>

                    <li className="flex flex-col items-center sm:items-start gap-2 text-center sm:text-left">
                      <div className={`flex size-8 items-center justify-center rounded-full text-xs font-bold transition-all duration-300 ${
                        hasRuns 
                          ? "bg-primary text-primary-foreground shadow-[0_0_12px_rgba(16,185,129,0.35)]" 
                          : "bg-muted text-muted-foreground border border-border"
                      }`}>
                        {hasRuns ? <Check className="size-4 stroke-[3]" /> : "3"}
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-xs font-semibold">3. Run Evaluation</p>
                        <p className="text-[11px] text-muted-foreground">Verify score indicators</p>
                      </div>
                      {!hasRuns && (
                        <Button asChild variant="link" size="sm" className="h-auto p-0 text-xs" disabled={!hasDocuments}>
                          <Link href="/evaluations">
                            Benchmark <ArrowRight className="size-3 ml-0.5" />
                          </Link>
                        </Button>
                      )}
                    </li>
                  </ol>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions Grid */}
            <div className="grid gap-4 sm:grid-cols-2">
              {SCREENS.map(({ href, title, desc, icon: Icon, badge, color, glow }) => (
                <Link key={href} href={href} className="group block">
                  <Card 
                    variant="glass" 
                    className={`h-full border border-border/60 hover:translate-y-[-2px] transition-all duration-300 ${glow}`}
                  >
                    <CardContent className="p-5 flex flex-col justify-between h-full gap-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className={`flex size-9 items-center justify-center rounded-lg bg-linear-to-br ${color}`}>
                            <Icon className="size-4.5" />
                          </div>
                          <span className={`text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full border bg-background/50 ${color.split(" ").slice(-2).join(" ")}`}>
                            {badge}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors flex items-center gap-1">
                          {title}
                        </h4>
                        <p className="text-[11px] text-muted-foreground leading-normal">{desc}</p>
                      </div>
                      
                      <div className="flex items-center gap-1 text-[11px] font-semibold text-primary/80 group-hover:text-primary transition-colors pt-2 border-t border-border/20">
                        Open console
                        <ArrowRight className="size-3 transition-transform duration-200 group-hover:translate-x-1" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>

          </div>

          {/* Recent Activity Timeline */}
          <div className="space-y-6">
            <Card variant="glass" className="h-full flex flex-col">
              <CardHeader className="pb-3 border-b border-border/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <HistoryIcon className="size-4.5 text-primary" />
                    <CardTitle className="text-md">Recent Activity</CardTitle>
                  </div>
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                    <Clock className="size-3" /> Live Feed
                  </span>
                </div>
                <CardDescription>
                  Audit log of evaluations and file updates.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6 flex-1">
                {activities.length === 0 ? (
                  <div className="flex flex-col items-center justify-center text-center py-12 text-muted-foreground gap-2">
                    <AlertCircle className="size-8 text-muted-foreground/50 animate-float" />
                    <p className="text-xs font-semibold">No recent events logged</p>
                    <p className="text-[10px] max-w-[200px]">Create pipelines and upload documents to view activity traces.</p>
                  </div>
                ) : (
                  <div className="relative border-l border-border/50 ml-3 pl-4 space-y-5">
                    {activities.map((act) => (
                      <div key={act.id} className="relative group/item">
                        {/* Dot indicator */}
                        <div className={`absolute -left-[21px] top-1 flex size-2.5 items-center justify-center rounded-full border-2 border-card transition-colors ${
                          act.type === "evaluation" ? "bg-purple-500" :
                          act.type === "document" ? "bg-emerald-500" : "bg-blue-500"
                        }`} />
                        
                        <div className="space-y-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-bold text-foreground">{act.title}</span>
                            <span className="text-[9px] text-muted-foreground font-mono">{act.time}</span>
                          </div>
                          <p className="text-[11px] text-muted-foreground leading-normal">{act.desc}</p>
                          {act.score !== undefined && (
                            <div className="inline-flex items-center gap-1.5 mt-1">
                              <span className={`text-[10px] font-extrabold px-1.5 py-0.5 rounded-sm ${
                                act.score >= 72 ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                                act.score >= 60 ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                                "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              }`}>
                                Unified Score: {act.score}%
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

        </div>

      </div>
    </>
  );
}
