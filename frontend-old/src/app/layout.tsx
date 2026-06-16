'use client';

import './globals.css';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';

function Navigation() {
  const { isAuthenticated, isAdmin, memberName, logout } = useAuth();

  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-surface-raised)] shadow-sm">
      <div className="mx-auto max-w-7xl px-4 py-3.5 sm:px-6 lg:px-8 flex items-center justify-between">
        <a
          href="/"
          className="text-xl font-bold text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] transition-colors duration-150 flex items-center gap-2"
        >
          <span aria-hidden="true">🏥</span>
          Plum Claims
        </a>
        <nav className="flex items-center gap-1 sm:gap-5 text-sm font-medium">
          <a
            href="/"
            className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary-600)] transition-colors duration-150 px-2 py-1.5 rounded-lg hover:bg-[var(--color-primary-50)] min-h-touch flex items-center"
          >
            Submit Claim
          </a>
          <a
            href="/claims"
            className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary-600)] transition-colors duration-150 px-2 py-1.5 rounded-lg hover:bg-[var(--color-primary-50)] min-h-touch flex items-center"
          >
            My Claims
          </a>
          {isAdmin && (
            <a
              href="/admin"
              className="text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] font-semibold transition-colors duration-150 px-2 py-1.5 rounded-lg hover:bg-[var(--color-primary-50)] min-h-touch flex items-center"
            >
              Admin
            </a>
          )}
          {isAuthenticated ? (
            <button
              onClick={() => {
                logout();
                window.location.href = '/login';
              }}
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-danger-600)] transition-colors duration-150 px-2 py-1.5 rounded-lg hover:bg-[var(--color-danger-50)] min-h-touch flex items-center"
            >
              Logout <span className="hidden sm:inline ml-1">({memberName || ''})</span>
            </button>
          ) : (
            <a
              href="/login"
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-primary-600)] transition-colors duration-150 px-2 py-1.5 rounded-lg hover:bg-[var(--color-primary-50)] min-h-touch flex items-center"
            >
              Login
            </a>
          )}
        </nav>
      </div>
    </header>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>Plum Claims — Health Insurance Claims</title>
        <meta
          name="description"
          content="Submit and track your health insurance claims quickly and easily."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen antialiased">
        <AuthProvider>
          <Navigation />
          <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
