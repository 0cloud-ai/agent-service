"use client";

import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  Home,
  Loader2,
  MessageSquare,
} from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

// ── Types (mirror backend DTOs) ─────────────────────────────────────

type Counts = {
  directories: number;
  sessions: number;
  messages: number;
};

type ChildStats = {
  name: string;
  total: Counts;
};

type StatsResponse = {
  path: string;
  direct: Counts;
  total: Counts;
  children: ChildStats[];
};

type SessionItem = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

type Pagination = {
  next_cursor: string | null;
  has_more: boolean;
  total: number;
};

type SessionListResponse = {
  path: string;
  sessions: SessionItem[];
  pagination: Pagination;
};

// ── Helpers ─────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Tree Node ───────────────────────────────────────────────────────

function TreeNode({
  name,
  path,
  total,
  activePath,
  onSelect,
}: {
  name: string;
  path: string;
  total: Counts;
  activePath: string;
  onSelect: (path: string) => void;
}) {
  const [expanded, setExpanded] = React.useState(false);
  const [children, setChildren] = React.useState<ChildStats[] | null>(null);
  const [loading, setLoading] = React.useState(false);
  const isActive = activePath === path;

  const handleExpand = async () => {
    if (!expanded && children === null) {
      setLoading(true);
      try {
        const res = await fetch(`/api/v1/stats${path}`);
        if (res.ok) {
          const data: StatsResponse = await res.json();
          setChildren(data.children);
        }
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  };

  const hasChildren = total.directories > 0;
  const Icon = expanded ? FolderOpen : Folder;

  return (
    <div>
      <div
        className={cn(
          "group flex items-center gap-1 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50 cursor-pointer",
          isActive && "bg-muted font-medium",
        )}
      >
        <button
          type="button"
          className="shrink-0 p-0.5"
          onClick={handleExpand}
        >
          {loading ? (
            <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
          ) : hasChildren ? (
            expanded ? (
              <ChevronDown className="size-3.5 text-muted-foreground" />
            ) : (
              <ChevronRight className="size-3.5 text-muted-foreground" />
            )
          ) : (
            <span className="inline-block size-3.5" />
          )}
        </button>
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-1.5"
          onClick={() => onSelect(path)}
        >
          <Icon className="size-4 shrink-0 text-blue-500" />
          <span className="truncate">{name}</span>
          <span className="ml-auto shrink-0 text-xs text-muted-foreground">
            {total.sessions}
          </span>
        </button>
      </div>
      {expanded && children && children.length > 0 && (
        <div className="ml-4 border-l pl-1">
          {children.map((child) => (
            <TreeNode
              key={child.name}
              name={child.name}
              path={`${path}/${child.name}`}
              total={child.total}
              activePath={activePath}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Directory Tree (left panel) ─────────────────────────────────────

function DirectoryTree({
  activePath,
  onSelect,
}: {
  activePath: string;
  onSelect: (path: string) => void;
}) {
  const [rootStats, setRootStats] = React.useState<StatsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/v1/stats");
        if (res.ok) setRootStats(await res.json());
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!rootStats) return null;

  return (
    <div className="flex flex-col gap-0.5 p-2">
      <div
        className={cn(
          "flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm hover:bg-muted/50 cursor-pointer",
          activePath === "/" && "bg-muted font-medium",
        )}
        onClick={() => onSelect("/")}
      >
        <Home className="size-4 shrink-0" />
        <span>All Sessions</span>
        <span className="ml-auto text-xs text-muted-foreground">
          {rootStats.total.sessions}
        </span>
      </div>
      {rootStats.children.map((child) => (
        <TreeNode
          key={child.name}
          name={child.name}
          path={`/${child.name}`}
          total={child.total}
          activePath={activePath}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

// ── Session List (right panel) ──────────────────────────────────────

function SessionList({ path }: { path: string }) {
  const [data, setData] = React.useState<SessionListResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const fetchSessions = React.useCallback(async (p: string) => {
    setLoading(true);
    setError(null);
    try {
      const url = p === "/" ? "/api/v1/sessions" : `/api/v1/sessions${p}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchSessions(path);
  }, [path, fetchSessions]);

  const loadMore = async () => {
    if (!data?.pagination.next_cursor) return;
    try {
      const url =
        path === "/" ? "/api/v1/sessions" : `/api/v1/sessions${path}`;
      const res = await fetch(
        `${url}?cursor=${data.pagination.next_cursor}&limit=20`,
      );
      if (res.ok) {
        const more: SessionListResponse = await res.json();
        setData({
          ...more,
          sessions: [...data.sessions, ...more.sessions],
        });
      }
    } catch {
      /* ignore */
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      </div>
    );
  }

  if (!data || data.sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <MessageSquare className="size-12 opacity-50" />
        <p className="mt-2 text-sm">No sessions in this directory</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {data.sessions.map((session) => (
        <div
          key={session.id}
          className="flex flex-col gap-1 border-b px-4 py-3 hover:bg-muted/30"
        >
          <div className="flex items-start justify-between gap-2">
            <span className="text-sm font-medium leading-snug">
              {session.title}
            </span>
            <span className="shrink-0 text-xs text-muted-foreground">
              {timeAgo(session.updated_at)}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <MessageSquare className="size-3" />
              {session.message_count} messages
            </span>
            <span>{session.id}</span>
          </div>
        </div>
      ))}
      {data.pagination.has_more && (
        <div className="p-4">
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={loadMore}
          >
            Load more
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Breadcrumbs ─────────────────────────────────────────────────────

function Breadcrumbs({
  path,
  onNavigate,
}: {
  path: string;
  onNavigate: (path: string) => void;
}) {
  const segments = path === "/" ? [] : path.replace(/^\//, "").split("/");

  return (
    <div className="flex items-center gap-1 text-sm">
      <Button
        variant="ghost"
        size="sm"
        className="h-7 gap-1 px-2"
        onClick={() => onNavigate("/")}
      >
        <Home className="size-3.5" />
        <span>root</span>
      </Button>
      {segments.map((seg, i) => {
        const p = "/" + segments.slice(0, i + 1).join("/");
        const isLast = i === segments.length - 1;
        return (
          <React.Fragment key={p}>
            <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 px-2",
                isLast && "font-medium text-foreground",
              )}
              onClick={() => onNavigate(p)}
            >
              {seg}
            </Button>
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

export function FileBrowser() {
  const [activePath, setActivePath] = React.useState("/");

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Left: Directory Tree */}
      <div className="flex w-64 shrink-0 flex-col overflow-hidden border-r">
        <div className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <Folder className="size-5" />
          <span className="font-medium">Explorer</span>
        </div>
        <ScrollArea className="min-h-0 flex-1">
          <DirectoryTree activePath={activePath} onSelect={setActivePath} />
        </ScrollArea>
      </div>

      {/* Right: Session List */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex h-14 shrink-0 items-center border-b px-4">
          <Breadcrumbs path={activePath} onNavigate={setActivePath} />
        </div>
        <ScrollArea className="min-h-0 flex-1">
          <SessionList path={activePath} />
        </ScrollArea>
      </div>
    </div>
  );
}
