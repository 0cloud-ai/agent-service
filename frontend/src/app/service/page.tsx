"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { conversationsApi, serviceInfoApi } from "@/lib/api";
import type {
  Conversation,
  ConversationMessage,
  ConversationDetail,
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Send, Plus, MessageSquare, ArrowLeft, X } from "lucide-react";

// ── Helpers ──────────────────────────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const STATUS_FILTERS = ["all", "open", "escalated", "closed"] as const;
type StatusFilter = (typeof STATUS_FILTERS)[number];

function statusBadgeVariant(
  status: Conversation["status"],
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "open":
      return "default";
    case "escalated":
      return "destructive";
    case "closed":
      return "secondary";
  }
}

// ── Page ─────────────────────────────────────────────────────────────

export default function ServicePage() {
  const { user, isLoading: authLoading } = useAuthStore();
  const router = useRouter();

  // Service info
  const [serviceName, setServiceName] = useState("Agent Service");

  // Conversations
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ConversationDetail | null>(null);
  const [isNewChat, setIsNewChat] = useState(false);

  // Input
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Auth guard ───────────────────────────────────────────────────

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    }
  }, [authLoading, user, router]);

  // ── Load service info ────────────────────────────────────────────

  useEffect(() => {
    serviceInfoApi
      .get()
      .then((info) => setServiceName(info.name || "Agent Service"))
      .catch(() => {});
  }, []);

  // ── Load conversations ───────────────────────────────────────────

  const loadConversations = useCallback(async () => {
    try {
      const params: { status?: string } =
        statusFilter !== "all" ? { status: statusFilter } : {};
      const res = await conversationsApi.list(params);
      setConversations(res.conversations);
    } catch {
      // ignore
    }
  }, [statusFilter]);

  useEffect(() => {
    if (user) loadConversations();
  }, [user, loadConversations]);

  // ── Load conversation detail ─────────────────────────────────────

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    conversationsApi
      .getDetail(selectedId, { order: "asc" })
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selectedId]);

  // ── Scroll to bottom on new messages ─────────────────────────────

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [detail?.messages]);

  // ── Send message ─────────────────────────────────────────────────

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    try {
      if (isNewChat) {
        const res = await conversationsApi.create(text);
        setIsNewChat(false);
        setSelectedId(res.conversation.id);
        await loadConversations();
      } else if (selectedId) {
        await conversationsApi.sendMessage(selectedId, text);
        const updated = await conversationsApi.getDetail(selectedId, {
          order: "asc",
        });
        setDetail(updated);
        await loadConversations();
      }
      setInput("");
    } catch {
      // ignore
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Auth loading / guard ─────────────────────────────────────────

  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  // ── Select conversation ──────────────────────────────────────────

  const selectConversation = (id: string) => {
    setSelectedId(id);
    setIsNewChat(false);
  };

  const startNewChat = () => {
    setSelectedId(null);
    setDetail(null);
    setIsNewChat(true);
    setInput("");
  };

  // ── Render ───────────────────────────────────────────────────────

  return (
    <div className="flex h-screen bg-background">
      {/* Left panel */}
      <div className="flex w-72 shrink-0 flex-col border-r">
        {/* Header */}
        <div className="flex items-center gap-2 border-b px-4 py-3">
          <Link
            href="/"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="size-4" />
          </Link>
          <h1 className="truncate text-sm font-semibold">{serviceName}</h1>
        </div>

        {/* Status filter */}
        <div className="flex gap-1 border-b px-3 py-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={cn(
                "rounded-full px-2.5 py-0.5 text-xs font-medium capitalize transition-colors",
                statusFilter === f
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Conversation list */}
        <ScrollArea className="flex-1">
          <div className="flex flex-col">
            {conversations.length === 0 && (
              <p className="px-4 py-8 text-center text-xs text-muted-foreground">
                No conversations
              </p>
            )}
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={cn(
                  "flex flex-col gap-1 border-b px-4 py-3 text-left transition-colors",
                  selectedId === conv.id
                    ? "bg-muted"
                    : "hover:bg-muted/50",
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="flex-1 truncate text-sm font-medium">
                    {conv.title}
                  </span>
                  <Badge variant={statusBadgeVariant(conv.status)}>
                    {conv.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex flex-1 flex-wrap gap-1">
                    {conv.labels.map((label) => (
                      <Badge
                        key={label}
                        variant="outline"
                        className="text-[10px]"
                      >
                        {label}
                      </Badge>
                    ))}
                  </div>
                  <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <MessageSquare className="size-3" />
                    {conv.message_count}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {timeAgo(conv.updated_at)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>

        {/* New conversation button */}
        <div className="border-t p-3">
          <Button
            variant="outline"
            className="w-full"
            onClick={startNewChat}
          >
            <Plus className="size-4" />
            New Conversation
          </Button>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex flex-1 flex-col">
        {!selectedId && !isNewChat ? (
          /* Empty state */
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-muted-foreground">
            <MessageSquare className="size-10 opacity-30" />
            <p className="text-sm">
              Select a conversation or start a new one
            </p>
          </div>
        ) : isNewChat ? (
          /* New chat */
          <div className="flex flex-1 flex-col items-center justify-center px-4">
            <div className="w-full max-w-2xl">
              <h2 className="mb-6 text-center text-xl font-semibold text-foreground">
                What can I help you with?
              </h2>
              <div className="relative">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Send a message..."
                  className="min-h-24 resize-none pr-12"
                  autoFocus
                />
                <Button
                  size="icon"
                  className="absolute right-2 bottom-2"
                  onClick={handleSend}
                  disabled={!input.trim() || sending}
                >
                  <Send className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* Conversation view */
          <>
            {/* Conversation header */}
            <div className="flex items-center gap-2 border-b px-4 py-3">
              <h2 className="flex-1 truncate text-sm font-semibold">
                {detail?.title ?? "Loading..."}
              </h2>
              {detail && (
                <Badge variant={statusBadgeVariant(detail.status)}>
                  {detail.status}
                </Badge>
              )}
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => {
                  setSelectedId(null);
                  setDetail(null);
                }}
              >
                <X className="size-4" />
              </Button>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1">
              <div className="mx-auto flex max-w-3xl flex-col gap-3 px-4 py-4">
                {detail?.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      "flex",
                      msg.role === "user" ? "justify-end" : "justify-start",
                    )}
                  >
                    <div
                      className={cn(
                        "max-w-[80%] rounded-2xl px-4 py-2.5",
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-foreground",
                      )}
                    >
                      <p className="whitespace-pre-wrap text-sm">
                        {msg.content}
                      </p>
                      <p
                        className={cn(
                          "mt-1 text-[10px]",
                          msg.role === "user"
                            ? "text-primary-foreground/60"
                            : "text-muted-foreground",
                        )}
                      >
                        {timeAgo(msg.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input area */}
            <div className="border-t px-4 py-3">
              <div className="mx-auto flex max-w-3xl items-end gap-2">
                <Textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Send a message..."
                  className="min-h-10 resize-none"
                  rows={1}
                />
                <Button
                  size="icon"
                  onClick={handleSend}
                  disabled={!input.trim() || sending}
                >
                  <Send className="size-4" />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
