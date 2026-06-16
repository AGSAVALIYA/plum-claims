"use client";

import { motion } from "framer-motion";
import { CheckCircle, FileText, Database, ShieldCheck, BarChart3, TestTube } from "lucide-react";
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

const metrics = [
  { icon: CheckCircle, text: "77 tests → 100% pass" },
  { icon: CheckCircle, text: "12/12 eval → 100% pass" },
  { icon: CheckCircle, text: "10/10 system_must → 100% pass" },
  { icon: FileText, text: "8 test files covering API, domain, orchestrator" },
  { icon: TestTube, text: "FastAPI TestClient for endpoint tests" },
  { icon: Database, text: "In-memory SQLite for isolated integration tests" },
];

export default function Slide13Metrics() {
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
          Engineering Quality
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          className="text-lg text-[#3EC1C5] text-center"
          variants={itemVariants}
        >
          77 Tests · 8 Test Files · 2,301 Lines of Test Code
        </motion.p>

        {/* Two columns */}
        <div className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-2 gap-8 w-full mt-2">
          {/* Left: Test Pyramid */}
          <motion.div
            className="flex flex-col items-center justify-center gap-3"
            variants={itemVariants}
          >
            <div className="flex flex-col items-center w-full max-w-xs">
              {/* Smoke tests — top */}
              <div className="w-24 h-10 bg-[#E56A76] rounded-t-md flex items-center justify-center text-xs font-semibold text-white">
                6 Smoke
              </div>
              {/* Unit tests — middle */}
              <div className="w-40 h-14 bg-[#F0A85A] flex items-center justify-center text-xs font-semibold text-white">
                28 Unit
              </div>
              {/* Integration tests — bottom */}
              <div className="w-full h-16 bg-[#3EC1C5] rounded-b-md flex items-center justify-center text-xs font-semibold text-white">
                12 Integration
              </div>
            </div>
            <p className="text-xs text-[#6B8A8C] mt-1">
              policy · fraud · decision · documents · API
            </p>
          </motion.div>

          {/* Right: Metrics Grid */}
          <motion.div
            className="flex flex-col gap-3"
            variants={itemVariants}
          >
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div
                  key={metric.text}
                  className="bg-[#0D1F21] border border-[#1E3538] rounded-lg px-4 py-3 flex items-center gap-3"
                >
                  <Icon className="w-4 h-4 shrink-0 text-[#3EC1C5]" />
                  <span className="text-sm text-[#E8EDE9]">{metric.text}</span>
                </div>
              );
            })}
          </motion.div>
        </div>

        {/* Bottom: system_must explanation */}
        <motion.div
          className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-4 w-full max-w-4xl flex items-start gap-3"
          variants={itemVariants}
        >
          <ShieldCheck className="w-5 h-5 mt-0.5 shrink-0 text-[#F0A85A]" />
          <p className="text-sm text-[#6B8A8C] leading-relaxed">
            <span className="text-[#F0A85A] font-semibold">system_must</span>{" "}
            verification checks natural-language requirements (e.g.,{" "}
            <span className="text-[#E8EDE9] italic">
              "Tell the member specifically what document type was uploaded
              and what is needed instead"
            </span>
            )
          </p>
        </motion.div>

        <AudioPlayer
          slideNumber={12}
          title="Engineering Quality"
          src="/audio/slide-13.wav"
          transcript="Engineering quality is measured by what happens when things go wrong, not just when they go right. The system has 77 tests across 8 test files — 6 smoke tests, 28 unit tests, and 12 integration tests using FastAPI's TestClient with in-memory SQLite for isolated test runs. All 12 core test cases pass at 100%, and all 10 strict system requirements pass — these verify natural language requirements like telling the member specifically what document was uploaded and what is needed instead. The test pyramid is well-structured: fast smoke tests at the top, thorough unit tests in the middle, and integration tests verifying full pipeline flows at the base."
        />
      </motion.div>
    </div>
  );
}
