'use client';

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import type { User, UserRole } from '@/types';
import { saveAuth, clearAuth, getUser, getToken } from '@/lib/auth';
import { login as apiLogin, register as apiRegister } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (memberId: string, password: string) => Promise<void>;
  register: (memberId: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const stored = getUser();
    if (stored && getToken()) {
      setUser(stored);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (memberId: string, password: string) => {
    const response = await apiLogin(memberId, password);
    saveAuth(response);
    setUser({
      member_id: response.member_id,
      member_name: response.member_name,
      role: response.role as UserRole,
    });
  }, []);

  const register = useCallback(async (memberId: string, password: string) => {
    const response = await apiRegister(memberId, password);
    saveAuth(response);
    setUser({
      member_id: response.member_id,
      member_name: response.member_name,
      role: response.role as UserRole,
    });
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    login,
    register,
    logout,
    isAdmin: user?.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
