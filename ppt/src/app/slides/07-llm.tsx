"use client";

import { motion } from "framer-motion";
import { Cpu, DollarSign, Database, RefreshCw } from "lucide-react";
import { AudioPlayer } from "@/app/components";

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

const providers = [
  { name: "OpenAI" },
  { name: "Anthropic" },
  { name: "Google" },
];

const features = [
  {
    icon: RefreshCw,
    text: "Schema validation with automatic retry on malformed output",
  },
  {
    icon: DollarSign,
    text: "Cost tracking per model (input + output tokens x per-1K rates)",
  },
  {
    icon: Database,
    text: "Content-addressable LLM response caching (SHA-256, Redis TTL)",
  },
  {
    icon: Cpu,
    text: "Tenacity retry with exponential backoff (transient network errors)",
  },
];

export default function Slide07LLM() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center gap-8 max-w-5xl w-full"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h1
          className="text-4xl md:text-5xl font-bold text-center text-white tracking-tight"
          variants={itemVariants}
        >
          Multi-Provider{" "}
          <span className="text-[#3EC1C5]">LLM Abstraction</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="text-lg text-[#6B8A8C] text-center"
          variants={itemVariants}
        >
          Switch providers by changing{" "}
          <span className="text-[#3EC1C5] font-mono">ONE</span> environment
          variable
        </motion.p>

        {/* Provider cards grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl"
          variants={itemVariants}
        >
          {providers.map((p) => (
            <div
              key={p.name}
              className="rounded-xl p-6 border border-[#1E3538] bg-[#0D1F21] flex items-center justify-center min-h-[80px]"
            >
              <h3 className="text-xl font-semibold text-white">{p.name}</h3>
            </div>
          ))}
        </motion.div>

        {/* Divider */}
        <motion.div
          className="w-full max-w-4xl border-t border-[#1E3538]"
          variants={itemVariants}
        />

        {/* Features */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-4xl"
          variants={itemVariants}
        >
          {features.map((f) => {
            const Icon = f.icon;
            return (
              <div key={f.text} className="flex items-start gap-3">
                <Icon size={20} className="text-[#3EC1C5] mt-0.5 shrink-0" />
                <span className="text-sm text-[#E8EDE9] leading-relaxed">
                  {f.text}
                </span>
              </div>
            );
          })}
        </motion.div>
      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={7}
          src="/audio/slide-07.wav"
          title="Multi-Provider LLM Abstraction"
          transcript="The LLM abstraction layer is something I'm genuinely proud of. Switching providers requires changing one environment variable. We support multiple providers through the same interface — OpenAI, Anthropic, and Google. Key features include schema validation with automatic retry on malformed output, per-model cost tracking based on input and output token counts, content-addressable response caching using SHA-256 with Redis TTL, and tenacity-based retry with exponential backoff for transient network errors. This is the difference between a prompt engineer and an AI engineer — thinking about cost, reliability, and production readiness from day one."
        />
      </div>
    </div>
  );
}
