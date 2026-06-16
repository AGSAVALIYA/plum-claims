// Auth helpers for Plum Claims frontend

const TOKEN_KEY = 'plum_token';
const MEMBER_ID_KEY = 'plum_member_id';
const MEMBER_NAME_KEY = 'plum_member_name';
const ROLE_KEY = 'plum_role';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getMemberId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(MEMBER_ID_KEY);
}

export function getMemberName(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(MEMBER_NAME_KEY);
}

export function getRole(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ROLE_KEY);
}

export function isAdmin(): boolean {
  return getRole() === 'admin';
}

export function setAuth(token: string, memberId: string, memberName: string, role: string = 'member'): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(MEMBER_ID_KEY, memberId);
  localStorage.setItem(MEMBER_NAME_KEY, memberName);
  localStorage.setItem(ROLE_KEY, role);
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(MEMBER_ID_KEY);
  localStorage.removeItem(MEMBER_NAME_KEY);
  localStorage.removeItem(ROLE_KEY);
}
