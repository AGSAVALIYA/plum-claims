"use client";

import { motion } from "framer-motion";
import { Beaker, Cpu, Server, LayoutDashboard, Github } from "lucide-react";
import { AudioPlayer } from "@/app/components";
import { githubFile } from "@/app/config";

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
  { icon: Beaker, value: "77", label: "Tests", color: "#3EC1C5" },
  { icon: Cpu, value: "6", label: "LLM Providers", color: "#F0A85A" },
  { icon: Server, value: "8", label: "Docker Services", color: "#E56A76" },
  { icon: LayoutDashboard, value: "14", label: "Grafana Panels", color: "#3EC1C5" },
];

const treeLines: { text: string; bold?: boolean; color?: string; githubUrl?: string }[] = [
  { text: "plum-claims/", bold: true, color: "#3EC1C5" },
  { text: "├── backend/           (Python 3.13 + FastAPI)", color: "#E8EDE9" },
  { text: "│   ├── api/           HTTP endpoints, middleware, auth", color: "#6B8A8C", githubUrl: githubFile("backend/api/") },
  { text: "│   ├── domain/        Business logic (claims, policy, fraud)", color: "#6B8A8C", githubUrl: githubFile("backend/domain/") },
  { text: "│   ├── orchestrator/  5-agent pipeline engine", color: "#6B8A8C", githubUrl: githubFile("backend/orchestrator/engine.py") },
  { text: "│   ├── providers/     LLM, Storage, Cache, Doc Processing", color: "#6B8A8C", githubUrl: githubFile("backend/providers/") },
  { text: "│   └── tests/         77 tests across 8 files", color: "#6B8A8C" },
  { text: "├── frontend/          (Next.js + TypeScript)", color: "#E8EDE9" },
  { text: "│   ├── src/app/       Pages (dashboard, claims, admin)", color: "#6B8A8C" },
  { text: "│   ├── components/    UI components + shadcn/ui", color: "#6B8A8C" },
  { text: "│   └── lib/           API client, auth, utilities", color: "#6B8A8C" },
  { text: "├── docs/              26 documentation files", color: "#6B8A8C" },
  { text: "├── infra/             Prometheus, Grafana configs", color: "#6B8A8C" },
  { text: "└── scripts/           Seed, eval, document generator", color: "#6B8A8C" },
];

export default function Slide04CodeStructure() {
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
          className="text-4xl md:text-5xl font-bold text-white tracking-tight"
          variants={itemVariants}
        >
          Code Organization
        </motion.h2>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-2 gap-10 w-full">
          {/* Left: Tree */}
          <motion.div
            className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-5 overflow-x-auto"
            variants={itemVariants}
          >
            <pre className="text-xs md:text-sm leading-relaxed font-mono text-[#E8EDE9]">
              {treeLines.map((line, i) => (
                <div
                  key={i}
                  style={{ color: line.color, fontWeight: line.bold ? 700 : 400 }}
                  className="flex items-center gap-1"
                >
                  <span>{line.text}</span>
                  {line.githubUrl && (
                    <a
                      href={line.githubUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center hover:opacity-80 transition-opacity shrink-0"
                      title="View on GitHub"
                    >
                      <Github size={12} className="text-[#6B8A8C] hover:text-[#3EC1C5]" />
                    </a>
                  )}
                </div>
              ))}
            </pre>
          </motion.div>

          {/* Right: Metrics */}
          <motion.div
            className="flex flex-col gap-5 justify-center"
            variants={itemVariants}
          >
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div
                  key={metric.label}
                  className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-5 flex items-center gap-5"
                >
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
                    style={{ backgroundColor: `${metric.color}20` }}
                  >
                    <Icon className="w-6 h-6" style={{ color: metric.color }} />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{metric.value}</div>
                    <div className="text-sm text-[#6B8A8C]">{metric.label}</div>
                  </div>
                </div>
              );
            })}
          </motion.div>
        </div>


      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={4}
          src="/audio/slide-04.wav"
          title="Code Organization"
          transcript="The code is organized into a clean layered structure. The backend has four main packages — API for HTTP endpoints and middleware, domain for pure business logic, orchestrator for the 5-agent pipeline engine, and providers for external service abstractions. The frontend uses Next.js with TypeScript and Tailwind, organized into pages, components, and library utilities. Key metrics: 77 tests across 8 files, 6 LLM providers supported through a single interface, 9 Docker services with health checks, and a 14-panel Grafana dashboard. Here is a code snippet from the repository showing how cleanly the abstractions separate infrastructure from domain logic. This ensures testability and clean architecture."
        />
      </div>
    </div>
  );
}
