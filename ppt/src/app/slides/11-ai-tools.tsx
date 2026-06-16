"use client";

import { motion } from "framer-motion";
import { Brain, Code, Lightbulb, Cpu, Sparkles } from "lucide-react";
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

const tools = [
  {
    icon: Code,
    title: "GitHub Copilot",
    tagline: "since 2021 beta",
    color: "#3EC1C5",
    features: [
      "DeepSeek V4 backend",
      "Boilerplate, tests, refactoring",
      "In-editor: from autocomplete to agent mode",
    ],
  },
  {
    icon: Brain,
    title: "Claude Code",
    tagline: "multi-model orchestration",
    color: "#F0A85A",
    features: [
      "DeepSeek V4 Pro → Thinking & Planning",
      "DeepSeek V4 Flash → Parallel sub-agents",
      "MiMo 2.5 Pro → Long-context tasks",
    ],
  },
  {
    icon: Lightbulb,
    title: "Claude Opus",
    tagline: "Antigravity",
    color: "#E56A76",
    features: [
      "Strategic architecture decisions",
      "Trade-off analysis",
      "Deciding what NOT to build",
    ],
  },
];

export default function Slide11AITools() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center w-full max-w-5xl gap-8"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-white tracking-tight text-center"
          variants={itemVariants}
        >
          AI-Assisted Development
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          className="text-lg text-[#3EC1C5] text-center max-w-2xl"
          variants={itemVariants}
        >
          Using AI tools is expected — knowing when NOT to use them is the skill
        </motion.p>

        {/* 3 Cards */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-3 gap-5 w-full"
          variants={itemVariants}
        >
          {tools.map((tool) => {
            const Icon = tool.icon;
            return (
              <div
                key={tool.title}
                className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-6 flex flex-col gap-4"
              >
                {/* Header */}
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                    style={{ backgroundColor: `${tool.color}20` }}
                  >
                    <Icon className="w-5 h-5" style={{ color: tool.color }} />
                  </div>
                  <div>
                    <div className="text-base font-semibold text-white">
                      {tool.title}
                    </div>
                    <div className="text-xs text-[#6B8A8C]">{tool.tagline}</div>
                  </div>
                </div>

                {/* Separator */}
                <div className="h-px bg-[#1E3538]" />

                {/* Features */}
                <ul className="flex flex-col gap-2">
                  {tool.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#E8EDE9]">
                      <div
                        className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                        style={{ backgroundColor: tool.color }}
                      />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </motion.div>

        {/* Bottom: Key insight */}
        <motion.div
          className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-5 w-full max-w-4xl flex flex-col gap-3"
          variants={itemVariants}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#F0A85A]" />
            <span className="text-sm font-semibold text-[#F0A85A] uppercase tracking-wider">
              Key Insight
            </span>
          </div>
          <p className="text-sm text-[#E8EDE9] leading-relaxed">
            AI accelerated implementation → 20+ issues found in 3 minutes by
            parallel sub-agents
          </p>
          <p className="text-sm text-[#6B8A8C] leading-relaxed">
            But architectural decisions (reject LangChain, parallelize pipeline,
            design traces) were human decisions
          </p>
        </motion.div>

        <AudioPlayer
          slideNumber={10}
          title="AI-Assisted Development"
          src="/audio/slide-11.wav"
          transcript="I want to talk about how I used AI tools to build this system. I've been using GitHub Copilot since the 2021 beta — it's evolved from simple autocomplete to full agent mode. For this project I configured it with DeepSeek V4 as the backing model for boilerplate generation, test scaffolding, and refactoring. For the heavy architectural work, I used Claude Code with a multi-model setup — DeepSeek V4 Pro for thinking and planning, DeepSeek V4 Flash for parallel sub-agents handling code review and test generation, and MiMo 2.5 Pro for long-context tasks. For strategic thinking — designing the architecture, deciding what not to build, and drafting documentation — I used Claude Opus. The key insight: AI accelerated implementation dramatically — parallel sub-agents found 20-plus issues in 3 minutes. But the architectural decisions — rejecting LangChain, parallelizing the pipeline, designing the trace system — were human decisions informed by AI analysis, not AI decisions."
        />
      </motion.div>
    </div>
  );
}
