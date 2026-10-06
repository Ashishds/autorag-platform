"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Sparkles,
  GitBranch,
  FileText,
  FlaskConical,
  Rocket,
  ShieldCheck,
  Check,
  Play,
  RefreshCw,
  Cpu,
  Layers,
  Activity,
  Database,
  Cloud,
  Server,
  ArrowUpRight,
  X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LandingPage() {
  const [query, setQuery] = useState("How does AutoRAG prevent hallucinations?");
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [simLogs, setSimLogs] = useState<string[]>([]);
  const [showMetrics, setShowMetrics] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // Counter values for sandbox stats
  const [retrievalVal, setRetrievalVal] = useState(0);
  const [faithfulVal, setFaithfulVal] = useState(0);
  const [adversarialVal, setAdversarialVal] = useState(0);
  const [unifiedVal, setUnifiedVal] = useState(0);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setIsLoggedIn(!!localStorage.getItem("authToken"));
    }
  }, []);

  const steps = [
    {
      name: "Rewrite Stage",
      desc: "Expanding search queries using Gemini 3.5 Flash clarity heuristic...",
      log: "Rewrite: 'Autonomous techniques and verification gates to block LLM hallucinations in RAG pipelines.'"
    },
    {
      name: "Hybrid Retrieval",
      desc: "Running dense pgvector + keyword tsvector search inside Postgres...",
      log: "RRF: Retrieved 20 candidate chunks. Reciprocal Rank Fusion completed."
    },
    {
      name: "Rerank Stage",
      desc: "Applying Cohere Rerank v3.5 to filter top-k chunks...",
      log: "Rerank: Reduced candidates to 5 high-relevance chunks. Low score chunks pruned."
    },
    {
      name: "Generation Stage",
      desc: "Querying LLM with strict grounding context constraints...",
      log: "Generate: Output created. Grounded in source document chunks [1], [2], and [4]."
    },
    {
      name: "Self-Evaluation",
      desc: "Scoring response quality, faithfulness, and latency vs golden set...",
      log: "Eval: RAGAS metrics completed. Faithfulness: 1.00, Relevance: 0.94."
    }
  ];

  const runSimulation = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setCurrentStep(0);
    setSimLogs([]);
    setShowMetrics(false);
  };

  useEffect(() => {
    if (!isSimulating) return;

    if (currentStep < steps.length) {
      const timer = setTimeout(() => {
        setSimLogs((prev) => [...prev, steps[currentStep].log]);
        setCurrentStep((prev) => prev + 1);
      }, 1200);
      return () => clearTimeout(timer);
    } else {
      setIsSimulating(false);
      setShowMetrics(true);
    }
  }, [isSimulating, currentStep]);

  // Scoring ticker animation when metrics show up
  useEffect(() => {
    if (showMetrics) {
      let r = 0;
      let f = 0;
      let a = 0;
      let u = 0;
      const interval = setInterval(() => {
        r = Math.min(0.89, r + 0.05);
        f = Math.min(1.00, f + 0.05);
        a = Math.min(100, a + 5);
        u = Math.min(0.85, u + 0.05);

        setRetrievalVal(parseFloat(r.toFixed(2)));
        setFaithfulVal(parseFloat(f.toFixed(2)));
        setAdversarialVal(Math.round(a));
        setUnifiedVal(parseFloat(u.toFixed(2)));

        if (r >= 0.89 && f >= 1.00 && a >= 100 && u >= 0.85) {
          clearInterval(interval);
        }
      }, 30);
      return () => clearInterval(interval);
    } else {
      setRetrievalVal(0);
      setFaithfulVal(0);
      setAdversarialVal(0);
      setUnifiedVal(0);
    }
  }, [showMetrics]);

  // Intersection observer for scroll animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("animate-fade-in-up");
            entry.target.classList.remove("opacity-0");
          }
        });
      },
      { threshold: 0.1 }
    );

    document.querySelectorAll(".fade-on-scroll").forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="relative min-h-screen bg-black text-slate-100 overflow-x-hidden selection:bg-emerald-500/30 selection:text-emerald-300">
      
      {/* Repeating Dot Grid overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-35 pointer-events-none z-0" />

      {/* Background glow meshes animated for subtle floating depth */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-500/10 blur-[120px] animate-float" />
        <div className="absolute top-[40%] right-[-10%] w-[60%] h-[60%] rounded-full bg-teal-500/5 blur-[150px] animate-float [animation-delay:1.5s]" />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] rounded-full bg-emerald-600/5 blur-[120px] animate-float [animation-delay:0.7s]" />
      </div>

      {/* Floating Header */}
      <header className="sticky top-4 z-50 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between rounded-full border border-slate-800 bg-slate-950/80 px-6 backdrop-blur-md shadow-2xl">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="AutoRAG Logo" className="size-9 rounded-lg object-cover shadow-md shadow-emerald-500/10 border border-slate-800" />
            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              AutoRAG
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#sandbox" className="hover:text-white transition-colors">Optimizer Demo</a>
            <a href="#deployment" className="hover:text-white transition-colors">BYOC</a>
          </nav>

          <div className="flex items-center gap-3">
            <Button asChild variant="ghost" className="rounded-full text-slate-400 hover:text-white hover:bg-slate-900 cursor-pointer">
              <Link href={isLoggedIn ? "/dashboard" : "/login"}>
                {isLoggedIn ? "Console" : "Sign In"}
              </Link>
            </Button>
            <Button asChild className="rounded-full bg-emerald-500 text-black hover:bg-emerald-400 font-semibold shadow-lg shadow-emerald-500/25 transition-all hover:scale-105 active:scale-95 cursor-pointer">
              <Link href={isLoggedIn ? "/dashboard" : "/login"}>
                {isLoggedIn ? "Go to Console" : "Get Started"}
                <ArrowRight className="size-4 ml-1.5" />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative mx-auto max-w-7xl px-4 pt-36 pb-16 sm:px-6 lg:px-8 text-center z-10">
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/5 px-4 py-1.5 text-xs sm:text-sm font-medium text-emerald-400 shadow-inner animate-fade-in-up">
          <Activity className="size-3.5 animate-pulse" />
          <span>Self-Improving Loop Active · Deploy Gate DEPLOY ≥ 0.72</span>
        </div>

        <h1 className="mt-8 text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl animate-fade-in-up [animation-delay:0.2s]">
          <span className="block bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            RAG pipelines that
          </span>
          <span className="block bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            evaluate and self-improve.
          </span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 sm:text-xl animate-fade-in-up [animation-delay:0.3s]">
          Stop tuning chunk sizes and rerankers by hand. AutoRAG ingests documents, scores its own quality against frozen evaluation sets, diagnoses errors, and deploys the optimal configuration automatically.
        </p>

        <div className="mt-10 flex flex-wrap justify-center gap-4 animate-fade-in-up [animation-delay:0.4s]">
          <Button asChild size="lg" className="rounded-full bg-emerald-500 text-black hover:bg-emerald-400 px-8 font-semibold shadow-xl shadow-emerald-500/20 transition-all hover:scale-105 cursor-pointer">
            <Link href={isLoggedIn ? "/dashboard" : "/login"}>
              {isLoggedIn ? "Go to Developer Console" : "Launch Developer Console"}
            </Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="rounded-full border-slate-800 bg-slate-950/40 text-slate-300 hover:text-white hover:bg-slate-900 px-8 cursor-pointer">
            <a href="#sandbox">Watch Self-Tuner</a>
          </Button>
        </div>
      </section>

      {/* Interactive Sandbox Section */}
      <section id="sandbox" className="mx-auto max-w-5xl px-4 py-12 sm:px-6 lg:px-8 z-10 relative opacity-0 fade-on-scroll">
        <div className="relative rounded-2xl border border-slate-800 bg-slate-950/60 p-6 md:p-8 backdrop-blur-md shadow-2xl overflow-hidden">
          <div className="absolute top-0 right-0 w-[30%] h-[30%] rounded-full bg-emerald-500/5 blur-[80px]" />
          
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Cpu className="size-5 text-emerald-400" />
                Live Optimization Sandbox
              </h2>
              <p className="text-sm text-slate-400">
                Type a question or press optimize to run Flow 2 (Query FastPath) combined with the Flow 3 (Evaluator & Judge) diagnostics loop.
              </p>
            </div>

            {/* Input box */}
            <div className="flex gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isSimulating}
                className="flex-1 rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 focus:outline-none disabled:opacity-50"
              />
              <Button
                onClick={runSimulation}
                disabled={isSimulating}
                className="rounded-xl bg-emerald-500 text-black hover:bg-emerald-400 font-semibold px-6 disabled:opacity-70 flex items-center gap-2 cursor-pointer"
              >
                {isSimulating ? (
                  <>
                    <RefreshCw className="size-4 animate-spin" />
                    Tuning...
                  </>
                ) : (
                  <>
                    <Play className="size-4 fill-current" />
                    Optimize
                  </>
                )}
              </Button>
            </div>

            {/* Sandbox screen layout */}
            <div className="grid gap-6 md:grid-cols-5">
              {/* Steps Checklist */}
              <div className="md:col-span-2 flex flex-col gap-3.5 border-r border-slate-900 pr-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Pipeline Stages</span>
                {steps.map((s, idx) => {
                  const isActive = isSimulating && currentStep === idx;
                  const isDone = currentStep > idx;
                  return (
                    <div
                      key={s.name}
                      className={`flex items-start gap-3 rounded-lg p-2.5 transition-colors ${
                        isActive ? "bg-slate-900/80 border border-slate-850" : ""
                      }`}
                    >
                      <div className={`flex size-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                        isDone ? "bg-emerald-500 text-black" :
                        isActive ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500" :
                        "bg-slate-900 text-slate-600"
                      }`}>
                        {isDone ? <Check className="size-3 stroke-[3]" /> : idx + 1}
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <span className={`text-xs font-medium ${isActive ? "text-emerald-400" : isDone ? "text-slate-300" : "text-slate-500"}`}>
                          {s.name}
                        </span>
                        <span className="text-[10px] text-slate-500 leading-tight">{s.desc}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Logs and Output */}
              <div className="md:col-span-3 flex flex-col gap-4 bg-slate-950/90 rounded-xl border border-slate-800/80 p-4 font-mono text-[11px] leading-relaxed min-h-[220px] shadow-[0_0_30px_rgba(16,185,129,0.03)]">
                <div className="flex items-center justify-between border-b border-slate-900 pb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="size-2.5 rounded-full bg-rose-500/80" />
                    <span className="size-2.5 rounded-full bg-amber-500/80" />
                    <span className="size-2.5 rounded-full bg-emerald-500/80" />
                    <span className="text-[10px] text-slate-500 font-semibold ml-2 select-none">autorag-tuner.sh</span>
                  </div>
                  <span className="flex items-center gap-1.5">
                    <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-emerald-500 text-[9px] font-bold">ONLINE</span>
                  </span>
                </div>
                
                <div className="flex-1 flex flex-col gap-2 overflow-y-auto max-h-[160px] text-slate-400">
                  {simLogs.length === 0 && !isSimulating && (
                    <span className="text-slate-600 italic">Click "Optimize" to view RAG tracer logs.</span>
                  )}
                  {isSimulating && simLogs.length === 0 && (
                    <span className="text-slate-500 animate-pulse">Initializing optimizer pipeline...</span>
                  )}
                  {simLogs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-emerald-500 shrink-0">&gt;</span>
                      <span>{log}</span>
                    </div>
                  ))}
                </div>

                {/* Final Score Reveal with animated countup */}
                {showMetrics && (
                  <div className="mt-auto border-t border-emerald-900/30 pt-4 bg-emerald-950/10 rounded-lg p-3 border border-emerald-900/20 animate-fade-in-up">
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div className="flex flex-col gap-1 border-r border-slate-900">
                        <span className="text-[8px] uppercase text-slate-500">Retrieval</span>
                        <span className="text-xs font-bold text-emerald-400">{retrievalVal}</span>
                      </div>
                      <div className="flex flex-col gap-1 border-r border-slate-900">
                        <span className="text-[8px] uppercase text-slate-500">Faithful</span>
                        <span className="text-xs font-bold text-emerald-400">{faithfulVal}</span>
                      </div>
                      <div className="flex flex-col gap-1 border-r border-slate-900">
                        <span className="text-[8px] uppercase text-slate-500">Adversarial</span>
                        <span className="text-xs font-bold text-emerald-400">{adversarialVal}%</span>
                      </div>
                      <div className="flex flex-col gap-1">
                        <span className="text-[8px] uppercase text-slate-400 font-bold">Unified</span>
                        <span className="text-sm font-black text-emerald-400">{unifiedVal} ★</span>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-[9px] text-slate-400">
                      <span>Status: <strong className="text-emerald-400">DEPLOY-ELIGIBLE</strong></span>
                      <Button asChild size="sm" className="h-5 px-2 text-[9px] bg-emerald-500 text-black hover:bg-emerald-400 cursor-pointer">
                        <Link href="/login">Deploy Candidate</Link>
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Grid Section */}
      <section id="features" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 border-t border-slate-900/50">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl bg-linear-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Complete self-improvement mechanics.
          </h2>
          <p className="mt-4 text-slate-400 text-base">
            AutoRAG runs in continuous validation loops. Pipeline configurations compete on identical baselines to verify progress.
          </p>
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {/* Card 1 */}
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-xs hover:border-emerald-500/25 transition-all duration-300 hover:translate-y-[-2px] opacity-0 fade-on-scroll">
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                <GitBranch className="size-5" />
              </div>
              <CardTitle className="text-white">DB-Level RRF Fusion</CardTitle>
              <CardDescription>
                Fuses dense embeddings (pgvector) and BM25 keywords (tsvector) inside a single Postgres transaction using Reciprocal Rank Fusion.
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Card 2 */}
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-xs hover:border-emerald-500/25 transition-all duration-300 hover:translate-y-[-2px] opacity-0 fade-on-scroll">
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                <ShieldCheck className="size-5" />
              </div>
              <CardTitle className="text-white">Hallucination Guardrails</CardTitle>
              <CardDescription>
                Non-bypassable deploy filters requiring 100% pass rate on adversarial anchors and a faithfulness score of &ge; 0.50.
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Card 3 */}
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-xs hover:border-emerald-500/25 transition-all duration-300 hover:translate-y-[-2px] opacity-0 fade-on-scroll">
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                <RefreshCw className="size-5" />
              </div>
              <CardTitle className="text-white">LangGraph Loop</CardTitle>
              <CardDescription>
                A state-saved, checkpointed graph workflow orchestrating optimization runs, proposing variants, and awaiting approval.
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Card 4 */}
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-xs hover:border-emerald-500/25 transition-all duration-300 hover:translate-y-[-2px] opacity-0 fade-on-scroll">
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                <FileText className="size-5" />
              </div>
              <CardTitle className="text-white">PII Entity Masking</CardTitle>
              <CardDescription>
                Automatically masks sensitive names, keys, and values at ingestion before embedding, securing document indices.
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Card 5 */}
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-xs hover:border-emerald-500/25 transition-all duration-300 hover:translate-y-[-2px] opacity-0 fade-on-scroll">
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                <Layers className="size-5" />
              </div>
              <CardTitle className="text-white">Frozen Golden Sets</CardTitle>
              <CardDescription>
                Validates updates using exact historic metrics sets. Variant configs compete on identical baselines to verify progress.
              </CardDescription>
            </CardHeader>
          </Card>

          {/* Card 6 */}
          <Card className="border-slate-800 bg-slate-950/40 backdrop-blur-xs hover:border-emerald-500/25 transition-all duration-300 hover:translate-y-[-2px] opacity-0 fade-on-scroll">
            <CardHeader>
              <div className="flex size-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 mb-2">
                <Rocket className="size-5" />
              </div>
              <CardTitle className="text-white">Instant Deploys</CardTitle>
              <CardDescription>
                No restarts. Updates adjust variables dynamically on active router endpoints with a single-click rollback fail-safe.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* Deployment Options Section */}
      <section id="deployment" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 border-t border-slate-900 bg-slate-950/20">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl bg-linear-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Flexible Deployment Architectures
          </h2>
          <p className="mt-4 text-slate-400 text-base">
            Choose the operational architecture that matches your compute, scale, and compliance constraints.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Mode 1 */}
          <div className="flex flex-col rounded-2xl border border-slate-850 bg-slate-950/50 p-8 shadow-xl hover:border-emerald-500/15 transition-colors duration-300 opacity-0 fade-on-scroll">
            <div className="flex items-center gap-3">
              <Cpu className="size-6 text-emerald-400" />
              <h3 className="text-xl font-bold text-white">Local Dev Mode</h3>
            </div>
            <p className="mt-4 text-sm text-slate-400 flex-1 leading-relaxed">
              Set <code className="text-emerald-400 font-mono text-xs">ENV=local</code> to run parsing, chunking, and evaluation inline inside the FastAPI process. Perfect for rapid offline tuning.
            </p>
            <hr className="my-6 border-slate-900" />
            <ul className="space-y-3.5 text-xs text-slate-350">
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                No message brokers required (Redis-free)
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Local file storage fallback
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Instant debugging of chunking strategies
              </li>
            </ul>
            <Button asChild className="mt-8 rounded-xl bg-slate-950 border border-slate-800 text-white hover:bg-slate-900 cursor-pointer">
              <Link href={isLoggedIn ? "/dashboard" : "/login"}>
                {isLoggedIn ? "Go to Console" : "Launch Console"}
              </Link>
            </Button>
          </div>

          {/* Mode 2 */}
          <div className="flex flex-col rounded-2xl border border-emerald-500/30 bg-slate-950/70 p-8 shadow-2xl relative hover:border-emerald-500/50 transition-colors duration-300 opacity-0 fade-on-scroll">
            <div className="absolute top-0 right-6 translate-y-[-50%] rounded-full bg-emerald-500 px-3 py-1 text-[10px] font-bold text-black uppercase tracking-wider">
              Scale Out
            </div>
            <div className="flex items-center gap-3">
              <Layers className="size-6 text-emerald-400" />
              <h3 className="text-xl font-bold text-white">Production Cluster</h3>
            </div>
            <p className="mt-4 text-sm text-slate-400 flex-1 leading-relaxed">
              Deploys distributed Celery workers with a Redis broker to process multi-document ingestion and batch Q&A evaluation pipelines asynchronously.
            </p>
            <hr className="my-6 border-slate-900" />
            <ul className="space-y-3.5 text-xs text-slate-350">
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Asynchronous task queues
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                S3-compatible storage integrations
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Parallelized LLM-as-judge scoring
              </li>
            </ul>
            <Button asChild className="mt-8 rounded-xl bg-emerald-500 text-black hover:bg-emerald-400 font-bold shadow-lg shadow-emerald-500/20 cursor-pointer">
              <Link href={isLoggedIn ? "/dashboard" : "/login"}>Deploy Cluster</Link>
            </Button>
          </div>

          {/* Mode 3 */}
          <div className="flex flex-col rounded-2xl border border-slate-850 bg-slate-950/50 p-8 shadow-xl hover:border-emerald-500/15 transition-colors duration-300 opacity-0 fade-on-scroll">
            <div className="flex items-center gap-3">
              <Server className="size-6 text-emerald-400" />
              <h3 className="text-xl font-bold text-white">VPC / Private Cloud</h3>
            </div>
            <p className="mt-4 text-sm text-slate-400 flex-1 leading-relaxed">
              Deploy containerized services (API, Celery, Postgres + pgvector, Redis) using Docker Compose or Kubernetes within your private VPC boundary.
            </p>
            <hr className="my-6 border-slate-900" />
            <ul className="space-y-3.5 text-xs text-slate-350">
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Complete data privacy & air-gapped runs
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Secure SSL and custom network routes
              </li>
              <li className="flex items-center gap-2.5">
                <Check className="size-4 text-emerald-400 shrink-0" />
                Horizontal scaling of task worker nodes
              </li>
            </ul>
            <Button asChild className="mt-8 rounded-xl bg-slate-950 border border-slate-800 text-white hover:bg-slate-900 cursor-pointer">
              <Link href={isLoggedIn ? "/dashboard" : "/login"}>View Compose Config</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/60 py-12 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-7xl px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="AutoRAG Logo" className="size-5 rounded object-cover opacity-70" />
            <span className="font-semibold text-slate-400">AutoRAG Optimization Platform</span>
          </div>
          <div className="flex gap-6">
            <a href="https://github.com/Ashishds/axirec" target="_blank" className="hover:text-slate-300 transition-colors">GitHub</a>
            <Link href={isLoggedIn ? "/dashboard" : "/login"} className="hover:text-slate-300 transition-colors">
              Developer Console
            </Link>
          </div>
          <span>&copy; 2026 AutoRAG. All rights reserved.</span>
        </div>
      </footer>

    </div>
  );
}
