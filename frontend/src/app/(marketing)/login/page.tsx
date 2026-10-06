"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Sparkles, ArrowRight, Lock, Mail, Users, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [email, setEmail] = useState("developer@autorag.ai");
  const [password, setPassword] = useState("••••••••");
  const [orgId, setOrgId] = useState("00000000-0000-0000-0000-000000000000");
  const [isLoading, setIsLoading] = useState(false);

  // Clear existing session on load (implicit logout)
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("authToken");
    }
  }, []);

  const generateRandomOrg = () => {
    // Generate a RFC-4122 compliant UUID v4
    const uuid = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
    setOrgId(uuid);
    toast("Generated new organization namespace ID", "info");
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(orgId)) {
      toast("Invalid Organization ID format. Must be a valid UUID.", "error");
      setIsLoading(false);
      return;
    }

    setTimeout(() => {
      try {
        // Construct simulated JWT
        // Backend's get_tenant_context parses this unverified token for org_id and sub
        const header = { alg: "HS256", typ: "JWT" };
        const payload = {
          org_id: orgId,
          sub: "00000000-0000-0000-0000-000000000001", // Default developer actor ID
          email: email
        };

        const base64UrlEncode = (obj: any) => {
          const str = JSON.stringify(obj);
          // Handle standard and utf-8 chars safely in btoa
          const encoded = btoa(unescape(encodeURIComponent(str)));
          return encoded.replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
        };

        const mockJwt = `${base64UrlEncode(header)}.${base64UrlEncode(payload)}.signature-stub`;

        if (typeof window !== "undefined") {
          localStorage.setItem("authToken", mockJwt);
        }

        toast("Authentication successful! Welcome to the console.", "success");
        router.push("/dashboard");
      } catch (err: any) {
        toast(err?.message || "Failed to issue session token", "error");
      } finally {
        setIsLoading(false);
      }
    }, 800);
  };

  return (
    <div className="relative min-h-screen bg-black flex flex-col items-center justify-center p-4 overflow-hidden select-none">
      
      {/* Decorative ambient lights */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-emerald-500/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-teal-500/5 blur-[120px] pointer-events-none" />

      {/* Logotype Header */}
      <div className="mb-8 flex items-center gap-2">
        <img src="/logo.png" alt="AutoRAG Logo" className="size-9 rounded-lg object-cover shadow-lg shadow-emerald-500/10 border border-slate-800" />
        <span className="text-xl font-bold tracking-tight text-white">AutoRAG Console</span>
      </div>

      {/* Glassmorphism Credentials Card */}
      <Card className="w-full max-w-md border-slate-800 bg-slate-950/60 backdrop-blur-lg shadow-2xl relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-4/5 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
        
        <form onSubmit={handleLogin}>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-white">Access the Console</CardTitle>
            <CardDescription className="text-center text-slate-400">
              Enter your credentials to manage or tune RAG configurations
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-4">
            
            {/* Email Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400">Developer Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-slate-500 pointer-events-none" />
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 border-slate-800 bg-slate-900/30 text-white focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-400">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-slate-500 pointer-events-none" />
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 border-slate-800 bg-slate-900/30 text-white focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {/* Organization UUID Scope */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-400">Organization Namespace (UUID)</label>
                <button
                  type="button"
                  onClick={generateRandomOrg}
                  className="text-[10px] text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors cursor-pointer"
                >
                  <RefreshCw className="size-3" />
                  Generate New
                </button>
              </div>
              <div className="relative">
                <Users className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-slate-500 pointer-events-none" />
                <Input
                  type="text"
                  required
                  value={orgId}
                  onChange={(e) => setOrgId(e.target.value)}
                  className="pl-10 pr-10 border-slate-800 bg-slate-900/30 font-mono text-xs text-white focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50"
                  placeholder="00000000-0000-0000-0000-000000000000"
                />
              </div>
              <span className="text-[10px] text-slate-500 leading-normal block">
                Scoped queries and uploads are saved under this namespace UUID.
              </span>
            </div>

          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-semibold rounded-xl py-5 shadow-lg shadow-emerald-500/10 flex items-center justify-center gap-2 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="size-4 animate-spin" />
                  Signing In...
                </>
              ) : (
                <>
                  Enter Console
                  <ArrowRight className="size-4" />
                </>
              )}
            </Button>

            <div className="text-center w-full">
              <Link href="/" className="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                &larr; Back to landing page
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
