import type { User, UserRole, TokenResponse } from '@/types';

const TOKEN_KEY = 'access_token';
const USER_KEY = 'user_data';

export function saveAuth(token: TokenResponse): void {
  localStorage.setItem(TOKEN_KEY, token.access_token);
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({
      member_id: token.member_id,
      member_name: token.member_name,
      role: token.role,
    })
  );
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed.member_id && parsed.role) {
      return {
        member_id: parsed.member_id,
        member_name: parsed.member_name || parsed.member_id,
        role: parsed.role as UserRole,
      };
    }
    return null;
  } catch {
    return null;
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export function isAdmin(): boolean {
  const user = getUser();
  return user?.role === 'admin';
}
