"use client";

import { motion } from "framer-motion";
import {
  Cpu,
  GitBranch,
  FileWarning,
  Lightbulb,
  RefreshCw,
  FileText,
  Bug,
  TestTube,
} from "lucide-react";
import AudioPlayer from "@/app/components/AudioPlayer";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

const challenges = [
  {
    icon: Cpu,
    title: "Embedded vs Standalone Celery",
    color: "#F0A85A",
    points: [
      "Dev: embedded daemon thread",
      "Production: standalone worker in docker-compose",
      "Learned: embedded worker dies silently under real LLM load",
    ],
  },
  {
    icon: GitBranch,
    title: "Sync Verification vs Async Processing",
    color: "#F0A85A",
    points: [
      "Step 1: Synchronous gate (stops before LLM calls)",
      "Steps 2-5: Async pipeline (extraction, policy, fraud, decision)",
      "Trade-off: early gate saves cost, async pipeline maximizes throughput",
    ],
  },
  {
    icon: FileWarning,
    title: "HybridDocumentProcessor Stub",
    color: "#F0A85A",
    points: [
      "Docling OCR integration is a placeholder",
      "Due to time constraints, documented the limitation and focused on core pipeline",
      "Real Indian medical docs need proper OCR + vision LLM",
    ],
  },
];

const improvements = [
  { icon: RefreshCw, text: "Fix Redis rate limiter (dead code → sorted-set sliding window)" },
  { icon: FileText, text: "Complete Docling OCR pipeline for real document processing" },
  { icon: Bug, text: "Add evaluator-optimizer pattern (Decision reviews Policy reasoning)" },
  { icon: TestTube, text: "Add frontend tests (zero right now)" },
];

export default function Slide12Challenges() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center w-full max-w-5xl gap-6"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-white tracking-tight text-center"
          variants={itemVariants}
        >
          Challenges{" "}
          <span className="text-[#3EC1C5">&</span> Key Decisions
        </motion.h2>

        {/* 3 challenge cards */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-3 gap-5 w-full"
          variants={itemVariants}
        >
          {challenges.map((challenge) => {
            const Icon = challenge.icon;
            return (
              <div
                key={challenge.title}
                className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-5 flex flex-col gap-3"
              >
                {/* Header */}
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                    style={{ backgroundColor: `${challenge.color}20` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: challenge.color }} />
                  </div>
                  <span className="text-sm font-semibold text-white leading-tight">
                    {challenge.title}
                  </span>
                </div>

                {/* Points */}
                <ul className="flex flex-col gap-2 mt-1">
                  {challenge.points.map((point, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#6B8A8C] leading-relaxed">
                      <span className="text-[#F0A85A] mt-0.5 shrink-0">
                        {i === challenge.points.length - 1 ? "→" : "•"}
                      </span>
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </motion.div>

        {/* Bottom: What I'd Change */}
        <motion.div
          className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-5 w-full max-w-4xl"
          variants={itemVariants}
        >
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-[#E56A76]" />
            <span className="text-sm font-semibold text-[#E56A76] uppercase tracking-wider">
              What I'd Change Given More Time
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-2 gap-3">
            {improvements.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.text} className="flex items-start gap-3">
                  <Icon className="w-4 h-4 mt-0.5 shrink-0 text-[#3EC1C5]" />
                  <span className="text-sm text-[#E8EDE9] leading-relaxed">{item.text}</span>
                </div>
              );
            })}
          </div>
        </motion.div>

        <AudioPlayer
          slideNumber={11}
          title="Challenges & Key Decisions"
          src="/audio/slide-12.wav"
          transcript="Let me talk about the hardest decisions. First, embedded versus standalone Celery — the dev mode uses a daemon thread, but I discovered it silently dies under real LLM load, so production uses a standalone worker. Second, the synchronous verification gate before async extraction — Step 1 must be synchronous to stop the pipeline before expensive LLM calls, while Steps 2 through 5 can be async. This clean separation was the right architectural call. Third, the HybridDocumentProcessor stub — real Indian medical documents with handwritten prescriptions and phone photos need proper OCR with visual LLM fallback, but for the initial MVP, I documented the limitation and focused on the core pipeline. Given more time, I'd fix the Redis rate limiter, complete the Docling OCR pipeline, add an evaluator-optimizer pattern where the Decision agent reviews the Policy agent's reasoning, and add frontend tests. One decision I'm proud of: the LLM abstraction layer — switching providers means changing one environment variable."
        />
      </motion.div>
    </div>
  );
}
