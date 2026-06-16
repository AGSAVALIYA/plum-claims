'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import * as auth from '@/lib/auth';

interface AuthState {
  token: string | null;
  memberId: string | null;
  memberName: string | null;
  role: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

interface AuthContextType extends AuthState {
  login: (token: string, memberId: string, memberName: string, role?: string) => void;
  logout: () => void;
  refresh: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    memberId: null,
    memberName: null,
    role: null,
    isAuthenticated: false,
    isAdmin: false,
  });

  const refresh = useCallback(() => {
    const token = auth.getToken();
    const memberId = auth.getMemberId();
    const memberName = auth.getMemberName();
    const role = auth.getRole();
    setState({
      token,
      memberId,
      memberName,
      role,
      isAuthenticated: !!token,
      isAdmin: role === 'admin',
    });
  }, []);

  useEffect(() => {
    refresh();
    // Listen for storage changes (e.g., login in another tab)
    const handleStorage = () => refresh();
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [refresh]);

  const login = useCallback((token: string, memberId: string, memberName: string, role: string = 'member') => {
    auth.setAuth(token, memberId, memberName, role);
    refresh();
  }, [refresh]);

  const logout = useCallback(() => {
    auth.logout();
    refresh();
  }, [refresh]);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
