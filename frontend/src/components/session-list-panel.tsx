"use client";

import { useEffect } from "react";
import { Plus, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useWorkspaceStore } from "@/stores/workspace-store";
import { useSessionStore } from "@/stores/session-store";
import type { Session } from "@/lib/types";

export function SessionListPanel() {
  const { currentPath, sessions, isLoadingSessions, fetchSessions } =
    useWorkspaceStore();
  const { selectedSession, selectSession } = useSessionStore();

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions, currentPath]);

  return (
    <div className="flex h-full w-1/4 max-w-[320px] min-w-[240px] shrink-0 flex-col overflow-hidden border-r bg-background">
      <div className="flex h-14 shrink-0 items-center justify-between border-b px-4">
        <div className="truncate text-sm font-medium text-foreground">
          {currentPath}
        </div>
        <Button variant="ghost" size="icon" className="size-7 shrink-0">
          <Plus className="size-4" />
        </Button>
      </div>
      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        {isLoadingSessions ? (
          <div className="p-4 text-sm text-muted-foreground">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No sessions in this directory
          </div>
        ) : (
          sessions.map((session) => (
            <SessionItem
              key={session.id}
              session={session}
              isSelected={selectedSession?.id === session.id}
              onSelect={() => selectSession(session)}
            />
          ))
        )}
      </ScrollArea>
    </div>
  );
}

function SessionItem({
  session,
  isSelected,
  onSelect,
}: {
  session: Session;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full border-b p-4 text-left text-sm leading-tight last:border-b-0 hover:bg-muted/50",
        isSelected && "bg-muted",
      )}
    >
      <div className="min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate font-medium">{session.title}</span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Harness: {session.harness}
        </p>
        <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
          <MessageSquare className="size-3" />
          <span>{session.message_count} messages</span>
          <span className="ml-auto">
            {new Date(session.updated_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </button>
  );
}
