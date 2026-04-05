"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FolderOpen,
  Users,
  Cpu,
  Wrench,
  Inbox,
  ExternalLink,
  LogOut,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { SessionsView } from "@/components/workspace/sessions-view";
import { MembersView } from "@/components/workspace/members-view";
import { ProvidersView } from "@/components/workspace/providers-view";
import { HarnessView } from "@/components/workspace/harness-view";
import { ServiceInboxView } from "@/components/workspace/service-inbox-view";

// ── Types ──────────────────────────────────────────────────────────

type WorkspaceView =
  | "sessions"
  | "members"
  | "providers"
  | "harness"
  | "service-inbox";

type NavItem = {
  id: WorkspaceView;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

// ── Nav config ─────────────────────────────────────────────────────

const explorerItems: NavItem[] = [
  { id: "sessions", label: "Sessions", icon: FolderOpen },
];

const managementItems: NavItem[] = [
  { id: "members", label: "Members", icon: Users },
  { id: "providers", label: "Providers", icon: Cpu },
  { id: "harness", label: "Harness", icon: Wrench },
];

const serviceItems: NavItem[] = [
  { id: "service-inbox", label: "Service Inbox", icon: Inbox },
];

// ── Component ──────────────────────────────────────────────────────

export function WorkspaceShell() {
  const [activeView, setActiveView] = useState<WorkspaceView>("sessions");
  const { user, logout } = useAuthStore();
  const router = useRouter();

  return (
    <div className="flex h-screen w-full bg-background">
      {/* Sidebar */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-muted/30">
        {/* Workspace header */}
        <div className="flex h-12 items-center px-4">
          <span className="text-sm font-semibold tracking-tight text-foreground">
            Workspace
          </span>
        </div>

        <Separator />

        {/* Navigation */}
        <ScrollArea className="flex-1">
          <nav className="flex flex-col gap-1 p-2">
            {/* Explorer */}
            <SectionLabel>Explorer</SectionLabel>
            {explorerItems.map((item) => (
              <NavButton
                key={item.id}
                item={item}
                active={activeView === item.id}
                onClick={() => setActiveView(item.id)}
              />
            ))}

            {/* Management */}
            <SectionLabel className="mt-4">Management</SectionLabel>
            {managementItems.map((item) => (
              <NavButton
                key={item.id}
                item={item}
                active={activeView === item.id}
                onClick={() => setActiveView(item.id)}
              />
            ))}

            {/* Service */}
            <SectionLabel className="mt-4">Service</SectionLabel>
            {serviceItems.map((item) => (
              <NavButton
                key={item.id}
                item={item}
                active={activeView === item.id}
                onClick={() => setActiveView(item.id)}
              />
            ))}
            <button
              onClick={() => router.push("/service")}
              className={cn(
                "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-muted-foreground transition-colors",
                "hover:bg-muted hover:text-foreground",
              )}
            >
              <ExternalLink className="size-4" />
              <span>Service Panel</span>
            </button>
          </nav>
        </ScrollArea>

        {/* User footer */}
        <Separator />
        <div className="flex items-center gap-2 p-3">
          <div className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-medium text-foreground">
            {user?.name?.charAt(0).toUpperCase() ?? "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium leading-tight text-foreground">
              {user?.name ?? "User"}
            </p>
            <p className="truncate text-xs leading-tight text-muted-foreground">
              {user?.email ?? ""}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={logout}
            aria-label="Logout"
          >
            <LogOut className="size-3.5" />
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex flex-1 flex-col overflow-hidden">
        <ViewContent view={activeView} />
      </main>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────

function SectionLabel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "px-2 pt-2 pb-1 text-xs font-medium tracking-wide text-muted-foreground/70 uppercase",
        className,
      )}
    >
      {children}
    </span>
  );
}

function NavButton({
  item,
  active,
  onClick,
}: {
  item: NavItem;
  active: boolean;
  onClick: () => void;
}) {
  const Icon = item.icon;
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
        active
          ? "bg-muted font-medium text-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Icon className="size-4" />
      <span>{item.label}</span>
    </button>
  );
}

function ViewContent({ view }: { view: WorkspaceView }) {
  switch (view) {
    case "sessions":
      return <SessionsView />;
    case "members":
      return <MembersView />;
    case "providers":
      return <ProvidersView />;
    case "harness":
      return <HarnessView />;
    case "service-inbox":
      return <ServiceInboxView />;
  }
}
