import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../api/client';

export interface AuthUser {
  id: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const res = await apiClient.post<{ token: string; user: AuthUser }>('/auth/login', {
          email,
          password,
        });
        set({ token: res.data.token, user: res.data.user, isAuthenticated: true });
      },

      register: async (email, password) => {
        const res = await apiClient.post<{ token: string; user: AuthUser }>('/auth/register', {
          email,
          password,
        });
        set({ token: res.data.token, user: res.data.user, isAuthenticated: true });
      },

      logout: () => {
        set({ token: null, user: null, isAuthenticated: false });
      },

      refreshUser: async () => {
        const token = get().token;
        if (!token) return;
        try {
          const res = await apiClient.get<{ user: AuthUser }>('/auth/me');
          set({ user: res.data.user, isAuthenticated: true });
        } catch {
          set({ token: null, user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'makyol-auth',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
