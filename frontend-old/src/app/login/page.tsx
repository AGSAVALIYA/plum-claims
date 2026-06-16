'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

const API_BASE = '/api/v1';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [memberId, setMemberId] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ member_id: memberId, password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const msg = body?.detail?.error?.message || body?.detail || 'Authentication failed';
        throw new Error(msg);
      }

      const data = await res.json();
      login(data.access_token, data.member_id, data.member_name, data.role || 'member');
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-xl shadow-sm border p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {mode === 'login' ? 'Sign In' : 'Register'}
          </h1>
          <p className="text-sm text-gray-500 mb-6">
            {mode === 'login'
              ? 'Sign in with your member ID and password.'
              : 'Create an account (member must exist in policy roster).'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Member ID</label>
              <input
                type="text"
                value={memberId}
                onChange={(e) => setMemberId(e.target.value)}
                placeholder="e.g., EMP001"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                required
                minLength={4}
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-white font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
            >
              {loading ? 'Processing...' : mode === 'login' ? 'Sign In' : 'Register'}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              {mode === 'login'
                ? "Don't have an account? Register"
                : 'Already have an account? Sign In'}
            </button>
          </div>

          <div className="mt-6 border-t pt-4 space-y-3">
            {/* Member credentials */}
            <div>
              <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">👤 Member Accounts</p>
              <div className="grid grid-cols-2 gap-1 text-xs text-[var(--color-text-secondary)]">
                <span>EMP001 / pass001</span>
                <span>EMP002 / pass002</span>
                <span>EMP003 / pass003</span>
                <span>EMP010 / pass010</span>
              </div>
            </div>
            {/* Admin credentials */}
            <div>
              <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-1.5">🛡️ Admin Account</p>
              <div className="text-xs text-[var(--color-text-secondary)]">
                <span>ADMIN001 / admin123</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
