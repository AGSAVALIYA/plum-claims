"use client";

import { motion } from "framer-motion";
import { BarChart3, Eye, GitBranch, ShieldAlert } from "lucide-react";
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

const traceSteps = [
  {
    icon: "✅",
    label: "SUBMISSION_DEADLINE",
    status: "PASSED",
    detail: "within 30 days",
  },
  {
    icon: "✅",
    label: "CATEGORY_COVERED",
    status: "PASSED",
    detail: "CONSULTATION is covered",
  },
  {
    icon: "✅",
    label: "WAITING_PERIOD",
    status: "PASSED",
    detail: "enrolled 547 days ago",
  },
  {
    icon: "ℹ️",
    label: "CO-PAY",
    status: "10% applied",
    detail: "Rs 150 deducted",
  },
  {
    icon: "ℹ️",
    label: "NETWORK_DISCOUNT",
    status: "20% at Apollo Hospitals",
    detail: null,
  },
];

const metricItems = [
  { icon: BarChart3, text: "240 Business Metrics", sub: "Prometheus" },
  { icon: Eye, text: "14-Panel Grafana Dashboard", sub: null },
  { icon: GitBranch, text: "Jaeger Distributed Tracing", sub: null },
  { icon: ShieldAlert, text: "PHI/PII Log Scrubbing", sub: null },
];

export default function Slide08Observability() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center gap-6 max-w-6xl w-full"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h1
          className="text-4xl md:text-5xl font-bold text-center text-white tracking-tight"
          variants={itemVariants}
        >
          <span className="text-[#3EC1C5]">Observability</span> &{" "}
          <span className="text-[#E56A76]">Explainability</span>
        </motion.h1>

        

        {/* Two columns */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full mt-2"
          variants={itemVariants}
        >
          {/* Left: ProcessingTrace */}
          <div className="rounded-xl p-6 border border-[#1E3538] bg-[#0D1F21]">
            <h3 className="text-lg font-semibold text-[#3EC1C5] mb-4 font-mono">
              ProcessingTrace
            </h3>
            <div className="flex flex-col gap-2">
              {traceSteps.map((step) => (
                <div
                  key={step.label}
                  className="flex items-start gap-3 text-sm py-1.5 px-3 rounded-lg bg-[#0A1516] border border-[#1E3538]"
                >
                  <span className="text-base shrink-0">{step.icon}</span>
                  <div className="flex flex-col">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[#E8EDE9] text-xs font-semibold">
                        {step.label}
                      </span>
                      <span
                        className={`text-xs font-semibold ${
                          step.icon === "✅"
                            ? "text-[#3EC1C5]"
                            : "text-[#F0A85A]"
                        }`}
                      >
                        {step.status}
                      </span>
                    </div>
                    {step.detail && (
                      <span className="text-[#6B8A8C] text-xs">
                        {step.detail}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right: Metrics */}
          <div className="rounded-xl p-6 border border-[#1E3538] bg-[#0D1F21] flex flex-col justify-center gap-4">
            {metricItems.map((m) => {
              const Icon = m.icon;
              return (
                <div
                  key={m.text}
                  className="flex items-center gap-4 px-4 py-3 rounded-lg bg-[#0A1516] border border-[#1E3538]"
                >
                  <Icon size={24} className="text-[#3EC1C5] shrink-0" />
                  <div>
                    <span className="text-white font-medium">{m.text}</span>
                    {m.sub && (
                      <span className="text-[#6B8A8C] text-sm ml-2">
                        → {m.sub}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Bottom quote */}
        <motion.div
          className="max-w-4xl text-center px-6 py-3 rounded-lg border border-[#1E3538] bg-[#0D1F21]"
          variants={itemVariants}
        >
          <p className="text-sm text-[#6B8A8C] italic">
            "someone on the operations team must be able to look at the system's
            output and understand exactly what happened"
          </p>
        </motion.div>

          


        <AudioPlayer
          slideNumber={8}
          title="Observability & Explainability"
          src="/audio/slide-08.wav"
          transcript="A key requirement is that someone on the operations team must be able to look at the system's output and understand exactly what happened. This is exactly what our ProcessingTrace delivers. Every claim has a trace with five steps — each showing agent name, status, confidence score, timing, and detailed checks performed. Expand any step and you see exactly what happened. For Policy Evaluation you see: submission deadline passed, category covered, waiting period passed, co-pay applied, network discount applied. Each check has a full human-readable reason. We also have full OpenTelemetry integration — every claim gets a distributed trace through Jaeger, 240 business metrics flow through Prometheus to a 14-panel Grafana dashboard. And we scrub PHI and PII from logs — patient names, amounts, doctor details are redacted before hitting log output. The combination of per-claim ProcessingTraces, distributed tracing, and business metrics means we can reconstruct exactly why any claim got any decision just from the trace. As you can see in the screenshot, the UI seamlessly integrates this trace data, allowing reviewers to drill down into the exact rationale for every decision."
        />
      </motion.div>
    </div>
  );
}
