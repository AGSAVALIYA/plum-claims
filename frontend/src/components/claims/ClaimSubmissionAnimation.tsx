'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import { Button } from '@/components/ui/button';

interface ClaimSubmissionAnimationProps {
  claimId: number;
  isOpen: boolean;
  onClose: () => void;
}

const CONFETTI_COLORS = [
  '#0D6B6E',
  '#D45161',
  '#2D8B6E',
  '#E8A838',
  '#7EC3C3',
  '#E56A76',
  '#3EC1C5',
  '#F9F7F4',
];

interface Particle {
  id: number;
  x: number;
  y: number;
  color: string;
  size: number;
  rotation: number;
  shape: 'circle' | 'square';
  xEnd: number;
  yEnd: number;
  rotationEnd: number;
}

function generateParticles(count: number): Particle[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: 50,
    y: 50,
    color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
    size: Math.random() * 10 + 6,
    rotation: Math.random() * 360,
    shape: Math.random() > 0.5 ? 'circle' : 'square' as 'circle' | 'square',
    xEnd: Math.random() * 100 - 20,
    yEnd: Math.random() * 100 - 30,
    rotationEnd: Math.random() * 720 - 360,
  }));
}

export default function ClaimSubmissionAnimation({
  claimId,
  isOpen,
  onClose,
}: ClaimSubmissionAnimationProps) {
  const router = useRouter();
  const [particles] = useState(() => generateParticles(24));
  const [showContent, setShowContent] = useState(false);
  const [showButtons, setShowButtons] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setShowContent(false);
      setShowButtons(false);
      const t1 = setTimeout(() => setShowContent(true), 600);
      const t2 = setTimeout(() => setShowButtons(true), 1800);
      const autoDismiss = setTimeout(() => onClose(), 8000);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
        clearTimeout(autoDismiss);
      };
    }
  }, [isOpen, onClose]);

  const handleViewClaim = useCallback(() => {
    onClose();
    router.push(`/claims/${claimId}`);
  }, [claimId, onClose, router]);

  const handleSubmitAnother = useCallback(() => {
    onClose();
    router.push('/claims/new');
  }, [onClose, router]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Content */}
          <motion.div
            className="relative flex flex-col items-center gap-6"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 200 }}
          >
            {/* Confetti Particles */}
            {particles.map((p) => (
              <motion.div
                key={p.id}
                className="absolute"
                style={{
                  width: p.size,
                  height: p.size,
                  backgroundColor: p.color,
                  borderRadius: p.shape === 'circle' ? '50%' : '2px',
                }}
                initial={{
                  x: '50vw',
                  y: '50vh',
                  rotate: p.rotation,
                  opacity: 1,
                }}
                animate={{
                  x: `calc(50vw + ${p.xEnd}vw)`,
                  y: `calc(50vh + ${p.yEnd}vh)`,
                  rotate: p.rotationEnd,
                  opacity: 0,
                }}
                transition={{
                  duration: 1.5,
                  delay: 0.3,
                  ease: [0.16, 1, 0.3, 1],
                  opacity: { duration: 1.2, delay: 0.6 },
                }}
              />
            ))}

            {/* Checkmark Circle */}
            <motion.div
              className="relative flex size-28 items-center justify-center"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                type: 'spring',
                damping: 14,
                stiffness: 180,
                delay: 0.15,
              }}
            >
              {/* Outer ring */}
              <svg
                className="absolute inset-0 size-28"
                viewBox="0 0 112 112"
                fill="none"
              >
                <motion.circle
                  cx="56"
                  cy="56"
                  r="50"
                  stroke="#2D8B6E"
                  strokeWidth="4"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{
                    duration: 0.6,
                    delay: 0.2,
                    ease: 'easeOut',
                  }}
                />
              </svg>

              {/* Inner fill */}
              <motion.div
                className="absolute inset-4 rounded-full bg-[#2D8B6E]"
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  type: 'spring',
                  damping: 16,
                  stiffness: 180,
                  delay: 0.35,
                }}
              />

              {/* Checkmark */}
              <svg
                className="relative z-10 size-12"
                viewBox="0 0 36 36"
                fill="none"
              >
                <motion.path
                  d="M8 18 L15 25 L28 11"
                  stroke="white"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{
                    duration: 0.5,
                    delay: 0.5,
                    ease: 'easeOut',
                  }}
                />
              </svg>
            </motion.div>

            {/* Success Text */}
            {showContent && (
              <motion.div
                className="flex flex-col items-center gap-1"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              >
                <h2
                  className="text-3xl font-bold text-white"
                  style={{ fontFamily: 'var(--font-display)' }}
                >
                  Claim Submitted!
                </h2>
                <p className="text-white/70 text-sm">
                  Claim #{claimId} has been received and is being processed.
                </p>
              </motion.div>
            )}

            {/* Buttons */}
            {showButtons && (
              <motion.div
                className="flex gap-3 mt-2"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
              >
                <Button
                  variant="default"
                  size="lg"
                  className="min-w-[140px] bg-[#2D8B6E] text-white hover:bg-[#2D8B6E]/80"
                  onClick={handleViewClaim}
                >
                  View Claim
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  className="min-w-[140px] border-white/30 text-white hover:bg-white/10"
                  onClick={handleSubmitAnother}
                >
                  Submit Another
                </Button>
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
