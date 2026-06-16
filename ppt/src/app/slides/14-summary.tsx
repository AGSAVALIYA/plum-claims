"use client";

import { motion } from "framer-motion";
import { CheckCircle, Github, Mail, Linkedin } from "lucide-react";
import AudioPlayer from "@/app/components/AudioPlayer";
import { CONFIG, githubFile } from "@/app/config";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

const achievements = [
  "Multi-agent pipeline — 5 agents, parallel Policy + Fraud execution",
  "Production observability — OpenTelemetry, Jaeger, Prometheus, Grafana",
  "Explainable decisions — full ProcessingTrace, every check visible",
  "77 tests, 12/12 eval pass, 10/10 system_must pass",
  "Multi-provider LLM — DeepSeek, with cost tracking + schema validation",
  "AI-assisted development — Copilot, Claude Code, Opus",
];

export default function Slide14Summary() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center w-full max-w-3xl gap-8"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h1
          className="text-5xl md:text-6xl font-bold text-center text-white tracking-tight"
          variants={itemVariants}
        >
          Thank You
        </motion.h1>

        {/* System name */}
        <motion.div
          className="text-2xl md:text-3xl font-bold text-[#3EC1C5] text-center"
          variants={itemVariants}
        >
          Health Insurance Claims Processing System
        </motion.div>

        {/* Key takeaways */}
        <motion.div
          className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-6 w-full"
          variants={itemVariants}
        >
          <h3 className="text-lg font-semibold text-[#E56A76] mb-4">
            Key Takeaways
          </h3>
          <div className="flex flex-col gap-3">
            {achievements.map((item) => (
              <div key={item} className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 mt-0.5 shrink-0 text-[#3EC1C5]" />
                <span className="text-base text-[#E8EDE9] leading-relaxed">
                  {item}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div
          className="flex flex-col items-center gap-3 text-center"
          variants={itemVariants}
        >
          <a
            href={CONFIG.githubBaseUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-[#3EC1C5] hover:underline transition-colors"
          >
            <Github className="w-4 h-4" />
            View on GitHub
          </a>
          <p className="text-sm text-[#6B8A8C]">
            Prepared for technical review — ready to extend live
          </p>
          <p className="text-sm text-[#E8EDE9]">
            {CONFIG.presenter.name} · {CONFIG.presenter.email} · {CONFIG.presenter.linkedin}
          </p>
        </motion.div>

        <AudioPlayer
          slideNumber={13}
          title="Summary"
          src="/audio/slide-14.wav"
          transcript="To summarize: I built a production-ready claims processing system with a multi-agent pipeline, 77 tests, full observability, explainable decisions, and a clean UI. The system processes claims end-to-end — document verification, structured extraction, policy evaluation, fraud detection, and decision aggregation — in about two seconds with a real LLM. I used AI tools extensively — Copilot since 2021, Claude Code for multi-agent orchestration, Opus for strategic thinking. But the architectural decisions, the trade-offs, the judgment about what not to build — those were human decisions. I'm prepared to extend the system live — add a new policy rule, implement a new fraud signal, or integrate a new LLM provider. Thank you for watching this demonstration."
        />
      </motion.div>
    </div>
  );
}
