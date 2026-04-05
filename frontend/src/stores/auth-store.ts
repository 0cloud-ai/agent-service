import { create } from "zustand";
import { userApi } from "@/lib/api";
import type { UserWithMemberships } from "@/lib/types";

type AuthState = {
  user: UserWithMemberships | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  validateToken: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  isLoading: true,

  login: async (email, password) => {
    const res = await userApi.login(email, password);
    localStorage.setItem("token", res.token);
    set({ token: res.token });
    try {
      const me = await userApi.getMe();
      set({ user: me, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ token: null, isLoading: false });
      throw new Error("Login succeeded but failed to fetch user profile");
    }
  },

  register: async (email, name, password) => {
    const res = await userApi.register(email, name, password);
    localStorage.setItem("token", res.token);
    set({ token: res.token });
    try {
      const me = await userApi.getMe();
      set({ user: me, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ token: null, isLoading: false });
      throw new Error("Registration succeeded but failed to fetch user profile");
    }
  },

  logout: () => {
    userApi.logout().catch(() => {});
    localStorage.removeItem("token");
    set({ user: null, token: null });
  },

  validateToken: async () => {
    const stored = localStorage.getItem("token");
    if (!stored) {
      set({ isLoading: false });
      return;
    }
    set({ token: stored });
    try {
      const me = await userApi.getMe();
      set({ user: me, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ user: null, token: null, isLoading: false });
    }
  },
}));
