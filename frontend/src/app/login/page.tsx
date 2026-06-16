'use client';

import { useState, useEffect, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { User, LockKeyhole, Loader2, Info } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const router = useRouter();

  const [memberId, setMemberId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(memberId, password);
      router.replace('/dashboard');
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred. Please try again.';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillAdmin = () => {
    setMemberId('ADMIN001');
    setPassword('admin123');
  };

  const fillEmployee = (val: string | null) => {
    if (!val) return;
    setMemberId(val);
    const num = val.replace('EMP', '');
    setPassword(`pass${num}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-sm text-muted-foreground">Loading ClaimFlow...</p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) return null;

  const demoEmployees = ['EMP001', 'EMP002', 'EMP003', 'EMP004', 'EMP005'];

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md"
      >
        <Card>
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl font-[family-name:var(--font-display)]">
              Welcome back
            </CardTitle>
            <CardDescription>
              Sign in to your ClaimFlow account
            </CardDescription>
          </CardHeader>

          <CardContent>
            {/* Quick Demo Login Section */}
            <div className="mb-6 p-4 rounded-lg bg-primary/5 border border-primary/20 space-y-3">
              <div className="flex items-center gap-2 text-sm font-medium text-primary mb-2">
                <Info className="size-4" /> Demo Quick Login
              </div>
              <div className="flex flex-col gap-3">
                <Select onValueChange={fillEmployee}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select Employee" />
                  </SelectTrigger>
                  <SelectContent>
                    {demoEmployees.map(emp => (
                      <SelectItem key={emp} value={emp}>{emp}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="secondary" onClick={fillAdmin} className="w-full" type="button">
                  Fill Admin Credentials
                </Button>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="member-id">Member ID</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                  <Input
                    id="member-id"
                    className="pl-9"
                    placeholder="Enter your member ID"
                    value={memberId}
                    onChange={(e) => setMemberId(e.target.value)}
                    required
                    autoComplete="username"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Password</Label>
                </div>
                <div className="relative">
                  <LockKeyhole className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                  <Input
                    id="password"
                    type="password"
                    className="pl-9"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={6}
                    autoComplete="current-password"
                  />
                </div>
              </div>

              {error && (
                <div
                  role="alert"
                  className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive"
                >
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full h-10"
                disabled={isSubmitting}
              >
                {isSubmitting && <Loader2 className="size-4 animate-spin" />}
                {isSubmitting ? 'Please wait...' : 'Sign In'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
