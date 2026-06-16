"use client";

import { motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Server,
  Database,
  Container,
  HardDrive,
  GitBranch,
  Cpu,
  LayoutDashboard,
} from "lucide-react";
import AudioPlayer from "@/app/components/AudioPlayer";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

interface Service {
  name: string;
  tech: string;
  port?: string;
  icon: typeof Server;
}

const services: Service[] = [
  { name: "app", tech: "FastAPI", port: ":8000", icon: Server },
  { name: "worker", tech: "Celery", icon: Activity },
  { name: "frontend", tech: "Next.js", port: ":3000", icon: Container },
  { name: "db", tech: "PostgreSQL 17", icon: Database },
  { name: "redis", tech: "Redis 7", icon: Database },
  { name: "minio", tech: "S3-compatible", icon: HardDrive },
  { name: "jaeger", tech: "Tracing", port: ":16686", icon: GitBranch },
  { name: "prometheus", tech: "Metrics", port: ":9095", icon: Cpu },
  { name: "grafana", tech: "Dashboards", port: ":3001", icon: LayoutDashboard },
];

const features = [
  "Non-root user in Dockerfile",
  "Multi-stage build (builder + slim runner)",
  "Health checks on all critical services",
  "14-Panel Grafana dashboard: throughput, latency, fraud, cache, decisions",
];

export default function Slide09Grafana() {
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
          Production-Grade{" "}
          <span className="text-[#3EC1C5]">Infrastructure</span>
        </motion.h1>

        {/* Service cards grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl"
          variants={itemVariants}
        >
          {services.map((s) => {
            const Icon = s.icon;
            return (
              <div
                key={s.name}
                className="rounded-xl p-5 border border-[#1E3538] bg-[#0D1F21] flex flex-col gap-2 hover:border-[#3EC1C5]/40 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Icon size={18} className="text-[#3EC1C5]" />
                  <h3 className="text-lg font-semibold text-white">{s.name}</h3>
                </div>
                <div className="flex items-center gap-1 text-sm">
                  <span className="text-[#6B8A8C]">{s.tech}</span>
                  {s.port && (
                    <span className="text-[#3EC1C5] font-mono text-xs">
                      {s.port}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </motion.div>

        {/* Divider */}
        <motion.div
          className="w-full max-w-4xl border-t border-[#1E3538]"
          variants={itemVariants}
        />

        {/* Features */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-4xl"
          variants={itemVariants}
        >
          {features.map((f) => (
            <div
              key={f}
              className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#0D1F21] border border-[#1E3538]"
            >
              <span className="w-2 h-2 rounded-full bg-[#3EC1C5] shrink-0" />
              <span className="text-sm text-[#E8EDE9]">{f}</span>
            </div>
          ))}
        </motion.div>

        <AudioPlayer
          slideNumber={9}
          title="Production-Grade Infrastructure"
          src="/audio/slide-09.wav"
          transcript="The infrastructure runs on Docker Compose with nine services — FastAPI backend, a standalone Celery worker for async processing, Next.js frontend, PostgreSQL 17, Redis 7, MinIO for S3-compatible storage, Jaeger for distributed tracing, Prometheus for metrics, and Grafana for dashboards. The Dockerfile uses multi-stage builds with a builder and slim runner, runs as non-root, and every critical service has health checks with proper dependency ordering. The Grafana dashboard has 14 panels tracking claims throughput by category, agent execution duration histograms, fraud risk score distribution, LLM cache hit-miss ratios, pipeline error rates, and decision outcome breakdowns."
        />
      </motion.div>
    </div>
  );
}
