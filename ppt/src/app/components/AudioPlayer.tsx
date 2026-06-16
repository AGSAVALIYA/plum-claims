"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Pause,
  FileText,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { usePresentation } from "../context/PresentationContext";

interface AudioPlayerProps {
  src?: string;
  transcript?: string;
  slideNumber: number;
  title: string;
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function AudioPlayer({
  src,
  transcript = "",
  slideNumber,
  title,
}: AudioPlayerProps) {
  const { playbackMode, nextSlide, muted } = usePresentation();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const progressRef = useRef<HTMLInputElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [showTranscript, setShowTranscript] = useState(false);
  const [audioError, setAudioError] = useState(false);

  const hasAudio = Boolean(src && src.trim().length > 0) && !audioError;
  const isAutoAudio = playbackMode === "autoplay" || playbackMode === "manual-auto-audio";
  const isAutoAdvance = playbackMode === "autoplay";

  // Reset state when src changes
  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setShowTranscript(false);
    setAudioError(false);
  }, [src]);

  // Audio event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoadedMetadata = () => setDuration(audio.duration);
    const onEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      if (isAutoAdvance) {
        nextSlide();
      }
    };
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);

    // In case the metadata loaded before the event listener was attached
    if (audio.readyState >= 1) {
      setDuration(audio.duration);
    }

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
    };
  }, [isAutoAdvance, nextSlide]);

  // Handle Mute from global context
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.muted = muted;
    }
  }, [muted]);

  // Autoplay audio on slide mount if setting is enabled
  useEffect(() => {
    if (isAutoAudio && hasAudio && audioRef.current) {
      audioRef.current.play().catch((e) => {
        console.log("Autoplay prevented by browser: ", e);
      });
    }
  }, [isAutoAudio, hasAudio, src]);

  const togglePlay = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => {});
    } else {
      audio.pause();
    }
  }, []);

  const handleSeek = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const time = Number(e.target.value);
      setCurrentTime(time);
      if (audioRef.current) {
        audioRef.current.currentTime = time;
      }
    },
    []
  );

  const hasTranscript = transcript.trim().length > 0;

  return (
    <>
      {/* Hidden audio element */}
      {hasAudio && (
        <audio
          ref={audioRef}
          src={src}
          preload="auto"
          onError={() => setAudioError(true)}
        />
      )}

      <div className="audio-player-bar">
        <div
          className="
            rounded-xl border backdrop-blur-lg
            bg-[#0D1F21]/95 border-[#1E3538]
            shadow-xl shadow-black/40
            overflow-hidden
            transition-all duration-200
            flex flex-col
          "
        >
          {/* Main bar - always visible */}
          <div className="flex items-center gap-3 px-3 h-[52px]">
            {/* Title / Badge section (fixed max width to prevent crushing others) */}
            <div className="flex items-center gap-2 flex-shrink-0 w-32 sm:w-40 overflow-hidden pr-2 border-r border-[#1E3538]">
              <span
                className="
                  flex-shrink-0 text-[10px] font-semibold tracking-wider
                  text-[#3EC1C5] bg-[#3EC1C5]/10
                  px-1.5 py-0.5 rounded
                "
              >
                {String(slideNumber).padStart(2, "0")}
              </span>
              <span className="text-xs font-medium text-[#E8EDE9] truncate">
                {title}
              </span>
            </div>

            {hasAudio ? (
              <>
                {/* Play/Pause */}
                <button
                  onClick={togglePlay}
                  className="
                    flex-shrink-0 w-9 h-9 rounded-full
                    flex items-center justify-center
                    bg-[#3EC1C5] text-[#0A1516]
                    hover:brightness-110 active:scale-95
                    transition-all duration-150 shadow-sm
                  "
                  aria-label={isPlaying ? "Pause" : "Play"}
                >
                  {isPlaying ? (
                    <Pause className="w-4 h-4" fill="currentColor" />
                  ) : (
                    <Play className="w-4 h-4 ml-0.5" fill="currentColor" />
                  )}
                </button>

                {/* Progress bar (flex-1 to take remaining space safely) */}
                <div className="flex items-center gap-2 flex-1 min-w-[100px]">
                  <span className="text-[10px] text-[#6B8A8C] tabular-nums w-8 text-right flex-shrink-0">
                    {formatTime(currentTime)}
                  </span>
                  <input
                    ref={progressRef}
                    type="range"
                    min={0}
                    max={duration || 0}
                    value={currentTime}
                    onChange={handleSeek}
                    className="flex-1 w-full cursor-pointer h-1.5"
                    aria-label="Seek"
                  />
                  <span className="text-[10px] text-[#6B8A8C] tabular-nums w-8 flex-shrink-0">
                    {formatTime(duration)}
                  </span>
                </div>

                {/* Transcript toggle */}
                {hasTranscript && (
                  <motion.button
                    animate={slideNumber === 1 ? { 
                      boxShadow: ["0px 0px 0px rgba(62,193,197,0)", "0px 0px 15px rgba(62,193,197,0.8)", "0px 0px 0px rgba(62,193,197,0)"] 
                    } : {}}
                    transition={slideNumber === 1 ? { duration: 1.5, repeat: 1, ease: "easeInOut", delay: 1 } : {}}
                    onClick={() => setShowTranscript((v) => !v)}
                    className="
                      flex-shrink-0 flex items-center gap-1.5
                      text-[11px] font-medium text-[#6B8A8C]
                      hover:text-[#3EC1C5] hover:bg-[#3EC1C5]/10
                      transition-colors
                      px-2.5 py-1.5 rounded-md border border-transparent
                      hover:border-[#3EC1C5]/30
                    "
                    aria-label={
                      showTranscript ? "Hide transcript" : "Show transcript"
                    }
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">
                      {showTranscript ? "Hide" : "Script"}
                    </span>
                  </motion.button>
                )}
              </>
            ) : (
              /* No audio: show transcript toggle */
              <>
                <div className="flex-1" />
                {hasTranscript ? (
                  <button
                    onClick={() => setShowTranscript((v) => !v)}
                    className="
                      flex items-center gap-1.5
                      text-xs text-[#6B8A8C]
                      hover:text-[#3EC1C5] hover:bg-[#3EC1C5]/10 
                      transition-colors px-3 py-1.5 rounded-md
                    "
                  >
                    <FileText className="w-4 h-4" />
                    <span>Show Transcript</span>
                    {showTranscript ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </button>
                ) : (
                  <span className="text-[10px] text-[#6B8A8C] italic">
                    No audio or transcript available
                  </span>
                )}
              </>
            )}
          </div>

          {/* Expandable transcript panel */}
          <AnimatePresence initial={false}>
            {showTranscript && hasTranscript && (
              <motion.div
                key="transcript"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="overflow-hidden border-t border-[#1E3538] bg-[#0A1516]/50"
              >
                <div className="transcript-text p-4 text-[13px] text-[#8BA4A6] leading-relaxed">
                  {transcript}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}
