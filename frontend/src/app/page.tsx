'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Upload, ShieldCheck, Zap, MonitorPlay, BookOpen } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

/* ------------------------------------------------------------------ */
/*  Feature data                                                      */
/* ------------------------------------------------------------------ */

interface Feature {
  icon: typeof Upload;
  title: string;
  description: string;
}

const features: Feature[] = [
  {
    icon: Upload,
    title: 'Upload & Submit',
    description: 'Drag-and-drop your medical documents for instant claim submission.',
  },
  {
    icon: ShieldCheck,
    title: 'Smart Verification',
    description: 'AI-powered document validation ensures accuracy before processing.',
  },
  {
    icon: Zap,
    title: 'Fast Processing',
    description: 'Get decisions in minutes, not weeks, with intelligent automation.',
  },
];

/* ------------------------------------------------------------------ */
/*  Animation variants                                                */
/* ------------------------------------------------------------------ */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.6 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
  },
};

/* ------------------------------------------------------------------ */
/*  Page                                                              */
/* ------------------------------------------------------------------ */

export default function SplashPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/dashboard');
    }
  }, [isLoading, isAuthenticated, router]);

  /* ── Loading ─────────────────────────────────────────────────── */

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-sm text-muted-foreground">Loading ClaimFlow...</p>
        </div>
      </div>
    );
  }

  /* ── Already authenticated ───────────────────────────────────── */

  if (isAuthenticated) return null;

  /* ── Splash ──────────────────────────────────────────────────── */

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden relative select-none">
      {/* ── Animated gradient orbs ─────────────────────────────── */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <motion.div
          className="absolute -top-1/3 -left-1/4 w-1/2 h-1/2 rounded-full"
          style={{ background: 'radial-gradient(circle, color-mix(in oklch, var(--primary) 10%, transparent) 0%, transparent 70%)' }}
          animate={{ x: [0, 40, 0], y: [0, -30, 0] }}
          transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute -bottom-1/3 -right-1/4 w-1/2 h-1/2 rounded-full"
          style={{ background: 'radial-gradient(circle, color-mix(in oklch, var(--accent) 10%, transparent) 0%, transparent 70%)' }}
          animate={{ x: [0, -40, 0], y: [0, 30, 0] }}
          transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      {/* ── Hero section ───────────────────────────────────────── */}
      <section className="flex-1 flex flex-col items-center justify-center relative z-10 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="text-center max-w-3xl"
        >
          {/* Decorative accent */}
          <div className="w-16 h-[3px] bg-primary rounded-full mx-auto mb-8" />

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.08] tracking-tight font-[family-name:var(--font-display)] text-foreground">
            Your Health Claims,{' '}
            <span className="text-primary">Simplified</span>
          </h1>
        </motion.div>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="mt-6 text-lg sm:text-xl text-muted-foreground max-w-xl text-center leading-relaxed"
        >
          Intelligent document processing that turns your health insurance claims
          from hassle to hassle-free.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button
            size="lg"
            className="h-12 px-8 text-base rounded-xl shadow-lg hover:shadow-xl active:shadow-md transition-all"
            onClick={() => router.push('/login')}
          >
            Get Started
          </Button>
          
          <Button
            size="lg"
            variant="secondary"
            className="h-12 px-6 text-base rounded-xl bg-primary/10 text-primary hover:bg-primary/20 border border-primary/30 shadow-sm transition-all gap-2"
            onClick={() => window.open('https://plum-claims-interactive.akshitgs.me', '_blank')}
          >
            <Presentation className="mr-2 size-5" />
            Interactive PPT
          </Button>

          <Button
            size="lg"
            variant="secondary"
            className="h-12 px-6 text-base rounded-xl bg-primary/10 text-primary hover:bg-primary/20 border border-primary/30 shadow-sm transition-all gap-2"
            onClick={() => window.open('https://plum-claims-doc.akshitgs.me', '_blank')}
          >
            <BookOpen className="size-5" />
            Read Docs
          </Button>
        </motion.div>
      </section>

      {/* ── Feature cards ──────────────────────────────────────── */}
      <section className="shrink-0 pb-6 sm:pb-8 relative z-10">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <motion.div key={feature.title} variants={itemVariants}>
                  <Card size="sm" className="text-center h-full">
                    <CardContent className="flex flex-col items-center gap-3 pt-6 pb-5">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Icon className="size-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm text-foreground">
                          {feature.title}
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                          {feature.description}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>
    </div>
  );
}
