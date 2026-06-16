"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Github,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  Play,
  Settings,
  MousePointerClick
} from "lucide-react";
import { CONFIG } from "@/app/config";
import { PlaybackMode, PresentationContext } from "./context/PresentationContext";
import {
  Slide01Title,
  Slide02Problem,
  Slide03Architecture,
  Slide04CodeStructure,
  Slide05Pipeline,
  Slide06LangChain,
  Slide07LLM,
  Slide08Observability,
  Slide09Grafana,
  Slide11AITools,
  Slide12Challenges,
  Slide13Metrics,
  Slide14Summary,
} from "./slides";

const SLIDES = [
  Slide01Title,
  Slide02Problem,
  Slide03Architecture,
  Slide04CodeStructure,
  Slide05Pipeline,
  Slide06LangChain,
  Slide07LLM,
  Slide08Observability,
  Slide09Grafana,
  Slide11AITools,
  Slide12Challenges,
  Slide13Metrics,
  Slide14Summary,
];

const TOTAL = SLIDES.length;

export default function Home() {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [hasStarted, setHasStarted] = useState(false);
  const [playbackMode, setPlaybackMode] = useState<PlaybackMode>("manual");
  const [muted, setMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Track fullscreen changes from browser UI (Esc key, etc.)
  useEffect(() => {
    const handler = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const go = useCallback(
    (delta: number) => {
      setDirection(delta);
      setIndex((prev) => Math.max(0, Math.min(TOTAL - 1, prev + delta)));
    },
    []
  );

  const nextSlide = useCallback(() => {
    if (index < TOTAL - 1) {
      go(1);
    }
  }, [index, go]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }, []);

  const toggleMuted = useCallback(() => {
    setMuted((prev) => !prev);
  }, []);

  useEffect(() => {
    if (!hasStarted) return; // Disable keyboard nav until started

    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " ") {
        e.preventDefault();
        go(1);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "Home") {
        e.preventDefault();
        setIndex(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setIndex(TOTAL - 1);
      } else if (e.key === "f" || e.key === "F") {
        e.preventDefault();
        toggleFullscreen();
      } else if (e.key === "m" || e.key === "M") {
        e.preventDefault();
        toggleMuted();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [hasStarted, go, toggleFullscreen, toggleMuted]);

  // Touch support
  useEffect(() => {
    if (!hasStarted) return;
    let startY = 0;
    const touchStart = (e: TouchEvent) => {
      startY = e.touches[0].clientY;
    };
    const touchEnd = (e: TouchEvent) => {
      const dy = startY - e.changedTouches[0].clientY;
      if (Math.abs(dy) > 50) go(dy > 0 ? 1 : -1);
    };
    window.addEventListener("touchstart", touchStart);
    window.addEventListener("touchend", touchEnd);
    return () => {
      window.removeEventListener("touchstart", touchStart);
      window.removeEventListener("touchend", touchEnd);
    };
  }, [hasStarted, go]);

  const startPresentation = (mode: PlaybackMode) => {
    setPlaybackMode(mode);
    setHasStarted(true);
  };

  const Slide = SLIDES[index];
  const progress = ((index + 1) / TOTAL) * 100;

  if (!hasStarted) {
    return (
      <div className="w-full min-h-screen flex flex-col items-center justify-center p-6 bg-[#0A1516] text-[#E8EDE9]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#0D1F21] border border-[#1E3538] rounded-2xl p-8 max-w-2xl w-full flex flex-col gap-8 shadow-2xl"
        >
          <div className="flex flex-col gap-2 text-center">
            <h1 className="text-3xl font-bold text-white tracking-tight">AI Claims Processing</h1>
            <p className="text-[#8BA4A6]">Choose how you'd like to view this presentation.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => startPresentation("autoplay")}
              className="flex flex-col items-center gap-4 bg-[#1a2f31] border border-[#264144] hover:border-[#3EC1C5] rounded-xl p-6 transition-all group"
            >
              <div className="w-12 h-12 rounded-full bg-[#3EC1C5]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Play className="w-6 h-6 text-[#3EC1C5]" fill="currentColor" />
              </div>
              <div className="text-center">
                <h3 className="font-semibold text-white mb-1">Full Autoplay</h3>
                <p className="text-xs text-[#8BA4A6] leading-relaxed">
                  Audio plays automatically. Slides advance automatically when audio ends.
                </p>
              </div>
            </button>

            <button
              onClick={() => startPresentation("manual-auto-audio")}
              className="flex flex-col items-center gap-4 bg-[#1a2f31] border border-[#264144] hover:border-[#F0A85A] rounded-xl p-6 transition-all group"
            >
              <div className="w-12 h-12 rounded-full bg-[#F0A85A]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Settings className="w-6 h-6 text-[#F0A85A]" />
              </div>
              <div className="text-center">
                <h3 className="font-semibold text-white mb-1">Manual + Auto Audio</h3>
                <p className="text-xs text-[#8BA4A6] leading-relaxed">
                  You advance slides manually. Audio plays automatically for each slide.
                </p>
              </div>
            </button>

            <button
              onClick={() => startPresentation("manual")}
              className="flex flex-col items-center gap-4 bg-[#1a2f31] border border-[#264144] hover:border-[#E56A76] rounded-xl p-6 transition-all group"
            >
              <div className="w-12 h-12 rounded-full bg-[#E56A76]/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                <MousePointerClick className="w-6 h-6 text-[#E56A76]" />
              </div>
              <div className="text-center">
                <h3 className="font-semibold text-white mb-1">Full Manual</h3>
                <p className="text-xs text-[#8BA4A6] leading-relaxed">
                  You advance slides. You click play to hear audio narration.
                </p>
              </div>
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <PresentationContext.Provider value={{ playbackMode, nextSlide, muted }}>
      <div className="slide-wrapper">
        <div className="progress-bar" style={{ width: `${progress}%` }} />

        {/* Top bar with controls */}
        <div
          style={{
            position: "fixed",
            top: "1rem",
            left: "0",
            right: "0",
            display: "flex",
            justifyContent: "space-between",
            padding: "0 1rem",
            zIndex: 250,
            pointerEvents: "none",
          }}
        >
          {/* Left: GitHub link */}
          <a
            href={CONFIG.githubBaseUrl.replace("/blob/main", "")}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-[#6B8A8C] hover:text-[#3EC1C5] transition-colors"
            style={{ pointerEvents: "auto" }}
          >
            <Github size={14} />
            <span className="hidden sm:inline">Repo</span>
          </a>

          {/* Right: Controls */}
          <div className="flex items-center gap-2 bg-[#0D1F21]/80 backdrop-blur-md border border-[#1E3538] px-3 py-1.5 rounded-full shadow-lg" style={{ pointerEvents: "auto" }}>
            <div className="text-[10px] text-[#3EC1C5] font-semibold px-2 uppercase tracking-wider hidden sm:block">
              {playbackMode.replace(/-/g, ' ')}
            </div>
            
            {/* Mute toggle */}
            <button
              onClick={toggleMuted}
              className="p-1.5 rounded-md hover:bg-[#1E3538] transition-colors"
              title={muted ? "Unmute" : "Mute"}
            >
              {muted ? (
                <VolumeX size={16} className="text-[#FF6B6B]" />
              ) : (
                <Volume2 size={16} className="text-[#6B8A8C]" />
              )}
            </button>

            {/* Fullscreen toggle */}
            <button
              onClick={toggleFullscreen}
              className="p-1.5 rounded-md hover:bg-[#1E3538] transition-colors"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 size={16} className="text-[#6B8A8C]" />
              ) : (
                <Maximize2 size={16} className="text-[#6B8A8C]" />
              )}
            </button>

            {/* Slide counter */}
            <span className="text-xs text-[#6B8A8C] font-mono ml-1">
              {index + 1}/{TOTAL}
            </span>
          </div>
        </div>

        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={index}
            custom={direction}
            initial={{ opacity: 0, x: direction * 60 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -60 }}
            transition={{ duration: 0.4, ease: "easeInOut" }}
            style={{ width: "100%", height: "100%" }}
          >
            <Slide />
          </motion.div>
        </AnimatePresence>

        {/* Navigation dots */}
        <div
          style={{
            position: "fixed",
            bottom: "1.5rem",
            left: "50%",
            transform: "translateX(-50%)",
            display: "flex",
            gap: "0.6rem",
            zIndex: 300,
          }}
        >
          {SLIDES.map((_, i) => (
            <button
              key={i}
              className={`nav-dot ${i === index ? "active" : ""}`}
              onClick={() => setIndex(i)}
              aria-label={`Go to slide ${i + 1}`}
            />
          ))}
        </div>

        <div className="keyboard-hint">
          &larr; &rarr; or Space to navigate &middot; F fullscreen &middot; M mute &middot; {index + 1}/{TOTAL}
        </div>
      </div>
    </PresentationContext.Provider>
  );
}
