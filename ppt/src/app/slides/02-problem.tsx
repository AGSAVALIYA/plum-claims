"use client";

import { motion } from "framer-motion";
import { AlertCircle, ShieldCheck, Brain, Target } from "lucide-react";
import { AudioPlayer } from "@/app/components";

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

const painPoints = [
  { icon: AlertCircle, text: "Manual claims review is slow, inconsistent, doesn't scale" },
  { icon: ShieldCheck, text: "Decisions must be explainable — black-box AI is not acceptable" },
  { icon: AlertCircle, text: "System must handle failures gracefully — no crashes" },
  { icon: ShieldCheck, text: "Document problems must be caught early with specific, actionable messages" },
  { icon: AlertCircle, text: "Must work with messy real-world medical documents" },
];



export default function Slide02Problem() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center w-full max-w-5xl gap-10"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-white tracking-tight"
          variants={itemVariants}
        >
          The Problem
        </motion.h2>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-2 gap-10 w-full">
          {/* Left: The Challenge */}
          <motion.div variants={itemVariants}>
            <div className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-6 flex flex-col items-start gap-4 h-full">
              <div className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0 bg-[#3EC1C5]20">
                <Target className="w-6 h-6 text-[#3EC1C5]" />
              </div>
              <h3 className="text-lg font-semibold text-white">The Challenge</h3>
              <p className="text-base text-[#E8EDE9] leading-relaxed">
                Health insurance claims processing is manual, slow, and inconsistent. At scale — tens of thousands of claims per year — this becomes a bottleneck that directly impacts patient care and operational costs.
              </p>
            </div>
          </motion.div>

          {/* Right: Pain points */}
          <motion.div
            className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-6 flex flex-col gap-5"
            variants={itemVariants}
          >
            <h3 className="text-lg font-semibold text-[#E56A76] mb-1">Key Challenges</h3>
            {painPoints.map((point, i) => {
              const Icon = point.icon;
              return (
                <div key={i} className="flex items-start gap-3">
                  <Icon className="w-5 h-5 mt-0.5 shrink-0 text-[#3EC1C5]" />
                  <span className="text-base text-[#E8EDE9] leading-relaxed">{point.text}</span>
                </div>
              );
            })}
          </motion.div>
        </div>

        
      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={2}
          title="The Problem"
          src="/audio/slide-02.wav"
          transcript="The core problem: processing health insurance claims manually doesn't scale. Our goal was to design a working system that accepts claims, verifies documents, extracts data, evaluates against policy rules, detects fraud, and produces explainable decisions."
        />
      </div>
    </div>
  );
}
