"use client";

import { motion } from "framer-motion";
import { Github } from "lucide-react";
import { AudioPlayer } from "@/app/components";
import { CONFIG } from "@/app/config";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.2 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};

export default function Slide01Title() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center gap-8 max-w-3xl"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h1
          className="text-5xl md:text-6xl font-bold text-center text-white tracking-tight"
          variants={itemVariants}
        >
          Health Insurance Claims
          <br />
          Processing System
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          className="text-xl md:text-2xl text-[#3EC1C5] font-medium text-center"
          variants={itemVariants}
        >
          AI-Powered Multi-Agent Claims Adjudication
        </motion.p>

        {/* Context */}
        <motion.p
          className="text-base text-[#6B8A8C] text-center"
          variants={itemVariants}
        >
          System Architecture — Interactive Demo
        </motion.p>

        {/* Screenshot photo */}
        <motion.div variants={itemVariants}>
          <img
            src="/screenshots/dashboard.png"
            alt="E2E Dashboard"
            className="rounded-xl border border-[#1E3538] max-w-md shadow-lg"
          />
        </motion.div>

        {/* GitHub link */}
        <motion.a
          href={CONFIG.githubBaseUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-[#6B8A8C] hover:text-[#3EC1C5] transition-colors"
          variants={itemVariants}
        >
          <Github className="w-5 h-5" />
          <span className="text-sm">View on GitHub</span>
        </motion.a>

        {/* Pulsing navigation hint */}
        <motion.p
          className="text-sm text-[#3EC1C5] mt-4"
          variants={itemVariants}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          → Use arrow keys or space to navigate
        </motion.p>
      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={1}
          title="Claims Processing System"
          src="/audio/slide-01.wav"
          transcript="Hello, and welcome to the demonstration of the AI Claims Processing platform. Over this presentation, I'll walk you through the architecture, the multi-agent pipeline, the AI integration decisions, and a live demo. Let's dive in."
        />
      </div>
    </div>
  );
}
