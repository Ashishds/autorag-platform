"use client";

import { useState, useEffect, useTransition, Suspense } from "react";
import useSWR from "swr";
import { useSearchParams, useRouter } from "next/navigation";
import { 
  Plus, 
  RefreshCw, 
  Trash2, 
  Settings, 
  Play, 
  Pause, 
  Globe, 
  Database, 
  Chrome, 
  BookOpen, 
  Box, 
  FolderArchive,
  Cloud,
  CheckCircle2,
  AlertTriangle,
  X,
  Link2,
  ExternalLink
} from "lucide-react";

import { api, APIError, fetcher } from "@/lib/api";
import type { Connector, Pipeline } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

// Mapping from connector type to provider value required by backend oauth endpoint
const OAUTH_PROVIDER_MAP: Record<string, string> = {
  google_drive: "google_drive",
  notion: "notion",
  dropbox: "dropbox",
  onedrive: "microsoft",
  sharepoint: "microsoft",
};

// SVG brand icons or fallbacks for various connectors
function ConnectorIcon({ type, className = "size-5" }: { type: string; className?: string }) {
  switch (type) {
    case "s3":
      return <Database className={`${className} text-amber-500`} />;
    case "web":
      return <Globe className={`${className} text-sky-400`} />;
    case "google_drive":
      return <Chrome className={`${className} text-emerald-400`} />;
    case "notion":
      return <BookOpen className={`${className} text-stone-200`} />;
    case "dropbox":
      return <Box className={`${className} text-blue-400`} />;
    case "onedrive":
      return <Cloud className={`${className} text-sky-500`} />;
    case "sharepoint":
      return <FolderArchive className={`${className} text-teal-400`} />;
    default:
      return <Link2 className={className} />;
  }
}

function ConnectorsDashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const authStatus = searchParams.get("auth_status");
  const authError = searchParams.get("error");
  const authConnectorId = searchParams.get("connector_id");

  const { data: pipelines } = useSWR<Pipeline[]>("/pipelines", fetcher);
  
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [connectorsLoading, setConnectorsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

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

  // Create Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState("");
  const [type, setType] = useState<string>("s3");
  const [pipelineId, setPipelineId] = useState("");
  const [syncInterval, setSyncInterval] = useState<number>(60);
  
  // Dynamic config form states
  const [s3Bucket, setS3Bucket] = useState("");
  const [s3Prefix, setS3Prefix] = useState("");
  const [s3AccessKey, setS3AccessKey] = useState("");
  const [s3SecretKey, setS3SecretKey] = useState("");
  const [s3Region, setS3Region] = useState("us-east-1");

  const [webUrl, setWebUrl] = useState("");
  const [webMaxDepth, setWebMaxDepth] = useState<number>(3);

  // Edit / Settings Modal states
  const [editingConnector, setEditingConnector] = useState<Connector | null>(null);
  const [editName, setEditName] = useState("");
  const [editSyncInterval, setEditSyncInterval] = useState<number>(60);

  // Load all connectors across pipelines
  const loadAllConnectors = async () => {
    if (!pipelines || pipelines.length === 0) {
      setConnectors([]);
      return;
    }
    setConnectorsLoading(true);
    try {
      const results = await Promise.all(
        pipelines.map((p) => api.listConnectorsByPipeline(p.id).catch(() => []))
      );
      setConnectors(results.flat());
    } catch (e) {
      console.error(e);
      setError("Failed to load connectors.");
    } finally {
      setConnectorsLoading(false);
    }
  };

  useEffect(() => {
    loadAllConnectors();
  }, [pipelines]);

  // Handle OAuth callback status from URL
  useEffect(() => {
    if (authStatus === "success") {
      toast("OAuth Authorization successful! Sync has been triggered.", "success");
      // Clear query parameters
      router.replace("/connectors");
      loadAllConnectors();
    } else if (authStatus === "error" && authError) {
      toast(`OAuth Authorization failed: ${decodeURIComponent(authError)}`, "error");
      router.replace("/connectors");
    }
  }, [authStatus, authError]);

  const handleCreate = () => {
    if (!name.trim() || !pipelineId) {
      setError("Name and Pipeline are required.");
      return;
    }

    setError(null);

    let config: Record<string, any> = {};
    if (type === "s3") {
      if (!s3Bucket) {
        setError("Bucket name is required for Amazon S3.");
        return;
      }
      config = {
        bucket: s3Bucket,
        prefix: s3Prefix,
        aws_access_key_id: s3AccessKey,
        aws_secret_access_key: s3SecretKey,
        region_name: s3Region,
      };
    } else if (type === "web") {
      if (!webUrl) {
        setError("Base URL is required for Web Crawler.");
        return;
      }
      config = {
        url: webUrl,
        max_depth: webMaxDepth,
      };
    }

    startTransition(async () => {
      try {
        const created = await api.createConnector({
          name,
          type,
          pipeline_id: pipelineId,
          config,
          sync_interval_minutes: syncInterval,
        });

        toast(`Connector "${created.name}" created successfully.`, "success");
        setShowCreateModal(false);
        resetCreateForm();
        
        // Auto trigger sync for S3 and Web Crawler immediately
        if (type === "s3" || type === "web") {
          await api.triggerConnectorSync(created.id);
        }
        
        await loadAllConnectors();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Failed to create connector");
        toast(e instanceof APIError ? e.message : "Failed to create connector", "error");
      }
    });
  };

  const handleUpdate = () => {
    if (!editingConnector) return;
    setError(null);

    startTransition(async () => {
      try {
        await api.updateConnector(editingConnector.id, {
          name: editName,
          sync_interval_minutes: editSyncInterval,
        });
        toast(`Connector "${editName}" settings updated.`, "success");
        setEditingConnector(null);
        await loadAllConnectors();
      } catch (e) {
        setError(e instanceof APIError ? e.message : "Failed to update connector");
        toast(e instanceof APIError ? e.message : "Failed to update connector", "error");
      }
    });
  };

  const handleDelete = (c: Connector) => {
    setConfirmDialog({
      isOpen: true,
      title: "Delete Connector",
      description: `Are you sure you want to delete connector "${c.name}"? This will stop synchronization and automatically remove all documents ingested by this connector from AutoRAG. This cannot be undone.`,
      onConfirm: () => {
        setError(null);
        startTransition(async () => {
          try {
            await api.deleteConnector(c.id);
            toast(`Connector "${c.name}" deleted successfully.`, "success");
            await loadAllConnectors();
          } catch (e) {
            toast(e instanceof APIError ? e.message : "Failed to delete connector", "error");
          }
        });
      },
    });
  };

  const handleSync = (c: Connector) => {
    startTransition(async () => {
      try {
        await api.triggerConnectorSync(c.id);
        toast(`Sync triggered for "${c.name}". Running in background.`, "success");
        await loadAllConnectors();
      } catch (e) {
        toast(e instanceof APIError ? e.message : "Failed to trigger synchronization.", "error");
      }
    });
  };

  const handleToggleStatus = (c: Connector) => {
    const nextStatus = c.status === "active" ? "paused" : "active";

    startTransition(async () => {
      try {
        await api.updateConnector(c.id, { status: nextStatus as any });
        toast(`Connector "${c.name}" ${nextStatus === "active" ? "resumed" : "paused"}.`, "success");
        await loadAllConnectors();
      } catch (e) {
        toast(e instanceof APIError ? e.message : "Failed to toggle connector status.", "error");
      }
    });
  };

  const resetCreateForm = () => {
    setName("");
    setType("s3");
    setPipelineId(pipelines?.[0]?.id ?? "");
    setSyncInterval(60);
    setS3Bucket("");
    setS3Prefix("");
    setS3AccessKey("");
    setS3SecretKey("");
    setS3Region("us-east-1");
    setWebUrl("");
    setWebMaxDepth(3);
  };

  // Populate first pipeline when pipelines load
  useEffect(() => {
    if (pipelines?.length && !pipelineId) {
      setPipelineId(pipelines[0].id);
    }
  }, [pipelines]);

  const BASE_API_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

  return (
    <>
      <PageHeader
        title="Data Connectors"
        description="Integrate with third-party systems to automatically sync documents into your RAG pipelines."
      />

      <div className="mx-auto max-w-6xl space-y-6 p-8">
        
        {error && (
          <div className="flex items-center gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-destructive animate-in fade-in duration-300">
            <AlertTriangle className="size-5 shrink-0" />
            <div className="flex-1 text-sm font-medium">{error}</div>
            <button onClick={() => setError(null)} className="text-destructive hover:text-destructive/80">
              <X className="size-4" />
            </button>
          </div>
        )}

        {/* Action Header Card */}
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm text-muted-foreground">
            {connectors.length} configured connectors
          </div>
          <div className="flex gap-2">
            <Button onClick={() => { resetCreateForm(); setShowCreateModal(true); }}>
              <Plus className="mr-2 size-4" />
              New Connector
            </Button>
            <Button variant="outline" onClick={loadAllConnectors} disabled={connectorsLoading}>
              <RefreshCw className={`mr-2 size-4 ${connectorsLoading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Connectors List */}
        {connectorsLoading && connectors.length === 0 ? (
          <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-border bg-card">
            <span className="text-sm text-muted-foreground animate-pulse">Loading connectors...</span>
          </div>
        ) : connectors.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card p-12 text-center">
            <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Link2 className="size-6" />
            </div>
            <h3 className="text-lg font-semibold text-foreground">No connectors connected</h3>
            <p className="mt-2 text-sm text-muted-foreground max-w-sm">
              Connect external data sources like S3, Google Drive, or Web Crawlers to keep your pipeline files continuously in sync.
            </p>
            <Button className="mt-6" onClick={() => { resetCreateForm(); setShowCreateModal(true); }}>
              <Plus className="mr-2 size-4" />
              Set up a connector
            </Button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {connectors.map((c) => {
              const matchedPipeline = pipelines?.find((p) => p.id === c.pipeline_id);
              const isOAuth = !!OAUTH_PROVIDER_MAP[c.type];
              // Check if OAuth connector has tokens saved
              const isAuthorized = isOAuth && !!c.config?.oauth_tokens;
              const oauthProvider = OAUTH_PROVIDER_MAP[c.type];
              const authorizeUrl = `${BASE_API_URL}/oauth/${c.id}/${oauthProvider}/authorize`;

              return (
                <Card key={c.id} className="relative flex flex-col justify-between overflow-hidden border border-border bg-card/50 transition-all hover:border-primary/40 hover:bg-card">
                  <CardContent className="p-6 flex-1 flex flex-col justify-between">
                    <div>
                      {/* Top Row: Brand & Badge */}
                      <div className="flex items-start justify-between gap-3 mb-4">
                        <div className="flex items-center gap-3">
                          <div className="flex size-10 items-center justify-center rounded-lg bg-accent/80">
                            <ConnectorIcon type={c.type} className="size-5" />
                          </div>
                          <div>
                            <h4 className="font-semibold text-foreground leading-none mb-1">{c.name}</h4>
                            <span className="text-xs text-muted-foreground font-mono uppercase">{c.type.replace("_", " ")}</span>
                          </div>
                        </div>

                        {/* Status Badge */}
                        <div className="flex items-center gap-2">
                          <span className={`relative flex size-2`}>
                            <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${
                              c.status === "active" ? "bg-emerald-400" : c.status === "paused" ? "bg-amber-400" : "bg-destructive"
                            }`} />
                            <span className={`relative inline-flex rounded-full size-2 ${
                              c.status === "active" ? "bg-emerald-500" : c.status === "paused" ? "bg-amber-500" : "bg-destructive"
                            }`} />
                          </span>
                          <span className="text-xs font-semibold capitalize text-muted-foreground">{c.status}</span>
                        </div>
                      </div>

                      {/* Middle Description / Meta */}
                      <div className="space-y-2 text-sm border-t border-border pt-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Pipeline:</span>
                          <span className="font-medium text-foreground truncate max-w-[150px]">
                            {matchedPipeline ? matchedPipeline.name : "Unknown"}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Sync Interval:</span>
                          <span className="text-foreground">
                            {c.sync_interval_minutes >= 1440 
                              ? `Every ${c.sync_interval_minutes / 1440} day(s)` 
                              : `Every ${c.sync_interval_minutes} mins`}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Last Synced:</span>
                          <span className="text-foreground text-xs truncate max-w-[150px]">
                            {c.last_synced_at ? new Date(c.last_synced_at).toLocaleString() : "Never synced"}
                          </span>
                        </div>

                        {/* Additional dynamic config summary text */}
                        {c.type === "s3" && c.config?.bucket && (
                          <div className="text-xs font-mono bg-accent/40 rounded p-1.5 truncate mt-2">
                            s3://{c.config.bucket}/{c.config.prefix || ""}
                          </div>
                        )}
                        {c.type === "web" && c.config?.url && (
                          <div className="text-xs font-mono bg-accent/40 rounded p-1.5 truncate mt-2">
                            {c.config.url}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Bottom row: action buttons */}
                    <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-4">
                      {isOAuth && !isAuthorized ? (
                        <Button 
                          asChild
                          size="sm" 
                          className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center justify-center gap-1.5"
                        >
                          <a href={authorizeUrl}>
                            <ExternalLink className="size-3.5" />
                            Connect Source
                          </a>
                        </Button>
                      ) : (
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="flex-1 flex items-center justify-center gap-1.5"
                          onClick={() => handleSync(c)}
                          disabled={isPending || c.status !== "active"}
                        >
                          <RefreshCw className="size-3.5" />
                          Sync Now
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0 flex items-center justify-center"
                        onClick={() => handleToggleStatus(c)}
                        title={c.status === "active" ? "Pause synchronization" : "Resume synchronization"}
                      >
                        {c.status === "active" ? <Pause className="size-3.5 text-amber-500" /> : <Play className="size-3.5 text-emerald-500" />}
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0 flex items-center justify-center"
                        onClick={() => {
                          setEditingConnector(c);
                          setEditName(c.name);
                          setEditSyncInterval(c.sync_interval_minutes);
                        }}
                        title="Connector settings"
                      >
                        <Settings className="size-3.5 text-muted-foreground" />
                      </Button>

                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 w-8 p-0 flex items-center justify-center text-destructive hover:bg-destructive hover:text-destructive-foreground border-destructive/25"
                        onClick={() => handleDelete(c)}
                        title="Delete connector"
                      >
                        <Trash2 className="size-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}

        {/* Create Modal Dialog */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl animate-in scale-in duration-200">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h3 className="text-lg font-semibold text-foreground">Set up Data Connector</h3>
                <button onClick={() => setShowCreateModal(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="size-5" />
                </button>
              </div>

              <div className="mt-4 space-y-4 max-h-[70vh] overflow-y-auto pr-1">
                {/* Connector Name */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Connector Name</label>
                  <Input
                    placeholder="e.g. Documentation Bucket or Marketing Notion"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>

                {/* Target RAG Pipeline */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Target RAG Pipeline</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={pipelineId}
                    onChange={(e) => setPipelineId(e.target.value)}
                  >
                    <option value="" disabled>Select pipeline</option>
                    {(pipelines ?? []).map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>

                {/* Source Provider Grid */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Connection Type</label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { id: "s3", label: "Amazon S3" },
                      { id: "web", label: "Web Crawler" },
                      { id: "google_drive", label: "Google Drive" },
                      { id: "notion", label: "Notion" },
                      { id: "dropbox", label: "Dropbox" },
                      { id: "onedrive", label: "OneDrive" },
                      { id: "sharepoint", label: "SharePoint" },
                    ].map((prov) => (
                      <button
                        key={prov.id}
                        type="button"
                        onClick={() => setType(prov.id)}
                        className={`flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center transition-all ${
                          type === prov.id
                            ? "border-primary bg-primary/10 text-primary-foreground font-semibold"
                            : "border-border bg-accent/40 text-muted-foreground hover:border-muted hover:text-foreground"
                        }`}
                      >
                        <ConnectorIcon type={prov.id} className="size-5" />
                        <span className="text-[11px] truncate max-w-full leading-tight">{prov.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Dynamic Configuration Fields */}
                {type === "s3" && (
                  <div className="space-y-3 rounded-lg border border-border bg-accent/20 p-4 animate-in fade-in duration-200">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">AWS S3 Credentials & Paths</h4>
                    
                    <div className="space-y-1.5">
                      <label className="text-xs text-muted-foreground">S3 Bucket Name</label>
                      <Input placeholder="my-doc-bucket" value={s3Bucket} onChange={(e) => setS3Bucket(e.target.value)} />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs text-muted-foreground">Folder Prefix (Optional)</label>
                      <Input placeholder="docs/" value={s3Prefix} onChange={(e) => setS3Prefix(e.target.value)} />
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-1.5">
                        <label className="text-xs text-muted-foreground">AWS Access Key ID</label>
                        <Input placeholder="AKIA..." value={s3AccessKey} onChange={(e) => setS3AccessKey(e.target.value)} />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-xs text-muted-foreground">AWS Secret Access Key</label>
                        <Input type="password" placeholder="••••••••••••" value={s3SecretKey} onChange={(e) => setS3SecretKey(e.target.value)} />
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs text-muted-foreground">AWS Region</label>
                      <Input placeholder="us-east-1" value={s3Region} onChange={(e) => setS3Region(e.target.value)} />
                    </div>
                  </div>
                )}

                {type === "web" && (
                  <div className="space-y-3 rounded-lg border border-border bg-accent/20 p-4 animate-in fade-in duration-200">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">Crawler Settings</h4>
                    
                    <div className="space-y-1.5">
                      <label className="text-xs text-muted-foreground">Starting Base URL</label>
                      <Input placeholder="https://docs.mycompany.com/faq" value={webUrl} onChange={(e) => setWebUrl(e.target.value)} />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-xs text-muted-foreground">Max Crawl Depth: {webMaxDepth} link hops</label>
                      <input 
                        type="range" 
                        min="1" 
                        max="5" 
                        value={webMaxDepth} 
                        onChange={(e) => setWebMaxDepth(parseInt(e.target.value))}
                        className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-primary" 
                      />
                      <span className="text-[10px] text-muted-foreground">Depth determines how far out of the base page the scraper follows local links.</span>
                    </div>
                  </div>
                )}

                {OAUTH_PROVIDER_MAP[type] && (
                  <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-4 text-xs text-emerald-400 animate-in fade-in duration-200">
                    <p className="font-semibold mb-1">OAuth Connection Required</p>
                    Once this connector is created, you will need to click the **Connect Source** button on its card to authenticate with {type.replace("_", " ")} and authorize AutoRAG read permissions.
                  </div>
                )}

                {/* Synchronization Schedule */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Background Sync Interval</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={syncInterval}
                    onChange={(e) => setSyncInterval(parseInt(e.target.value))}
                  >
                    <option value={60}>Every hour (Recommended)</option>
                    <option value={360}>Every 6 hours</option>
                    <option value={720}>Every 12 hours</option>
                    <option value={1440}>Daily (Every 24 hours)</option>
                    <option value={10080}>Weekly (Every 7 days)</option>
                  </select>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
                <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreate} disabled={isPending}>
                  {isPending ? "Creating..." : "Save Connector"}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal Dialog */}
        {editingConnector && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-in fade-in duration-200">
            <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl animate-in scale-in duration-200">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h3 className="text-lg font-semibold text-foreground">Connector Settings</h3>
                <button onClick={() => setEditingConnector(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="size-5" />
                </button>
              </div>

              <div className="mt-4 space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Connector Name</label>
                  <Input
                    placeholder="Connector name"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Sync Interval</label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={editSyncInterval}
                    onChange={(e) => setEditSyncInterval(parseInt(e.target.value))}
                  >
                    <option value={60}>Every hour</option>
                    <option value={360}>Every 6 hours</option>
                    <option value={720}>Every 12 hours</option>
                    <option value={1440}>Daily</option>
                    <option value={10080}>Weekly</option>
                  </select>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2 border-t border-border pt-4">
                <Button variant="ghost" onClick={() => setEditingConnector(null)}>
                  Cancel
                </Button>
                <Button onClick={handleUpdate} disabled={isPending || !editName.trim()}>
                  {isPending ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
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

export default function ConnectorsPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-background">
        <span className="text-sm text-muted-foreground animate-pulse">Loading view...</span>
      </div>
    }>
      <ConnectorsDashboard />
    </Suspense>
  );
}
