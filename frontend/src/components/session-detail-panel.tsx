"use client";

import { Info, UserPlus } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useSessionStore } from "@/stores/session-store";

export function SessionDetailPanel() {
  const { selectedSession, members } = useSessionStore();

  if (!selectedSession) return null;

  return (
    <div className="flex h-full w-1/4 max-w-[360px] min-w-[280px] shrink-0 flex-col overflow-hidden border-l bg-background">
      <div className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <Info className="size-4" />
        <span className="font-semibold">Session Details</span>
      </div>
      <ScrollArea className="min-h-0 flex-1 [&>[data-slot=scroll-area-viewport]>div]:!block">
        <div className="space-y-6 p-4">
          {/* Session Info */}
          <section className="space-y-3">
            <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Information
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Harness</span>
                <span>{selectedSession.harness}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Messages</span>
                <span>{selectedSession.message_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created</span>
                <span>
                  {new Date(selectedSession.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Updated</span>
                <span>
                  {new Date(selectedSession.updated_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </section>

          {/* Members */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                Members ({members.length})
              </p>
              <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs" disabled>
                <UserPlus className="size-3" />
                Add
              </Button>
            </div>
            <div className="space-y-1">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center gap-3 rounded-md p-2 hover:bg-muted"
                >
                  <Avatar className="size-8">
                    <AvatarFallback className="text-xs">
                      {member.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {member.name}
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <span>{member.joined_via}</span>
                      {member.type !== "user" && (
                        <Badge
                          variant="outline"
                          className="h-4 px-1 text-[10px]"
                        >
                          {member.type}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {members.length === 0 && (
                <p className="text-sm text-muted-foreground">No members</p>
              )}
            </div>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
}
