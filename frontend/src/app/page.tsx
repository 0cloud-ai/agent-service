"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useUIStore } from "@/stores/ui-store";
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SessionListPanel } from "@/components/session-list-panel";
import { SessionChat } from "@/components/session-chat";
import { SessionDetailPanel } from "@/components/session-detail-panel";

export default function Home() {
  const { user, isLoading, validateToken } = useAuthStore();
  const { isDetailPanelOpen } = useUIStore();
  const router = useRouter();

  useEffect(() => {
    validateToken();
  }, [validateToken]);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-0 overflow-hidden">
        <div className="flex h-full w-full">
          <SessionListPanel />
          <SessionChat />
          {isDetailPanelOpen && <SessionDetailPanel />}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
