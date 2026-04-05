"use client";

import { PanelRight, MessageSquare, Send } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/stores/session-store";
import { useUIStore } from "@/stores/ui-store";
import type { Message } from "@/lib/types";

export function SessionChat() {
  const { selectedSession, messages, isLoadingMessages } = useSessionStore();
  const { isDetailPanelOpen, toggleDetailPanel } = useUIStore();

  if (!selectedSession) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        <div className="text-center">
          <MessageSquare className="mx-auto size-12 opacity-50" />
          <p className="mt-2 text-sm">Select a session to view</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
      <header className="flex h-14 shrink-0 items-center justify-between border-b bg-background px-4">
        <div className="flex items-center gap-3">
          <MessageSquare className="size-5" />
          <span className="font-medium">{selectedSession.title}</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          onClick={toggleDetailPanel}
        >
          <PanelRight
            className={cn("size-4", isDetailPanelOpen && "text-primary")}
          />
        </Button>
      </header>

      <ScrollArea className="min-h-0 flex-1">
        <div className="px-6 py-6 lg:px-10">
          <div className="mx-auto max-w-3xl space-y-8">
            {isLoadingMessages ? (
              <p className="text-sm text-muted-foreground">Loading messages...</p>
            ) : messages.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground">
                No messages yet
              </p>
            ) : (
              messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))
            )}
          </div>
        </div>
      </ScrollArea>

      <div className="shrink-0 border-t bg-background px-6 py-4 lg:px-10">
        <div className="mx-auto max-w-3xl rounded-lg border bg-muted/30">
          <Textarea
            placeholder="Write a message..."
            className="min-h-[80px] resize-none border-0 bg-transparent focus-visible:ring-0"
            disabled
          />
          <div className="flex items-center justify-end gap-2 border-t px-3 py-2">
            <Button size="sm" className="gap-1" disabled>
              <Send className="size-3" />
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.type === "event") {
    return (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
          {message.action}
        </Badge>
        <span>{message.actor}</span>
        {message.target && (
          <span className="font-mono text-[11px]">{message.target}</span>
        )}
        {message.detail && <span>— {message.detail}</span>}
      </div>
    );
  }

  const isAssistant = message.role === "assistant";

  return (
    <div className="space-y-3">
      <div className="flex items-start gap-3">
        <Avatar className="mt-0.5 size-10 shrink-0">
          <AvatarFallback className="bg-primary text-xs font-medium text-primary-foreground">
            {isAssistant ? "AI" : "U"}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">
              {isAssistant ? "Assistant" : "User"}
            </span>
            {isAssistant && (
              <Badge variant="secondary" className="h-5 px-1.5 text-[10px]">
                AI
              </Badge>
            )}
          </div>
          <span className="text-xs text-muted-foreground">
            {new Date(message.created_at).toLocaleString()}
          </span>
        </div>
      </div>
      <div className="pl-13 text-sm leading-relaxed whitespace-pre-wrap">
        {message.content}
      </div>
    </div>
  );
}
