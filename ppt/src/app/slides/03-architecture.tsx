"use client";

import { motion } from "framer-motion";
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

export default function Slide03Architecture() {
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
          className="text-4xl md:text-5xl font-bold text-white tracking-tight"
          variants={itemVariants}
        >
          System Architecture
        </motion.h2>

        <motion.p
          className="text-lg text-[#3EC1C5] mb-2"
          variants={itemVariants}
        >
          Modular Monolith with 4 Layers
        </motion.p>

        {/* SVG Diagram */}
        <motion.div
          className="w-full flex justify-center"
          variants={itemVariants}
        >
          <svg
            viewBox="0 0 800 500"
            className="w-full max-w-[760px]"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* ===== Layer 1: Frontend ===== */}
            <rect x={250} y={10} width={300} height={48} rx={10} fill="#0D1F21" stroke="#3EC1C5" strokeWidth={1.5} />
            <text x={400} y={40} textAnchor="middle" fill="#E8EDE9" fontSize={15} fontWeight={600}>
              🖥️ Next.js Frontend :3000
            </text>

            {/* Arrow down */}
            <line x1={400} y1={58} x2={400} y2={88} stroke="#1E3538" strokeWidth={2} />
            <polygon points="400,90 395,80 405,80" fill="#1E3538" />

            {/* ===== Layer 2: Backend API ===== */}
            <rect x={250} y={90} width={300} height={48} rx={10} fill="#0D1F21" stroke="#F0A85A" strokeWidth={1.5} />
            <text x={400} y={120} textAnchor="middle" fill="#E8EDE9" fontSize={15} fontWeight={600}>
              ⚡ FastAPI Backend :8000
            </text>

            {/* Arrow down */}
            <line x1={400} y1={138} x2={400} y2={168} stroke="#1E3538" strokeWidth={2} />
            <polygon points="400,170 395,160 405,160" fill="#1E3538" />

            {/* ===== Layer 3: Multi-Agent Pipeline ===== */}
            <rect x={50} y={170} width={700} height={145} rx={12} fill="#0D1F21" stroke="#3EC1C5" strokeWidth={1} strokeDasharray="4 3" />
            <text x={400} y={194} textAnchor="middle" fill="#3EC1C5" fontSize={13} fontWeight={600}>
              🤖 Multi-Agent Pipeline Engine
            </text>

            {/* Agent boxes */}
            {/* Verify */}
            <rect x={70} y={215} width={88} height={54} rx={8} fill="#0A1516" stroke="#3EC1C5" strokeWidth={1.2} />
            <text x={114} y={248} textAnchor="middle" fill="#3EC1C5" fontSize={13} fontWeight={600}>Verify</text>

            {/* Arrow: Verify → Extract */}
            <line x1={158} y1={242} x2={168} y2={242} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="170,242 164,238 164,246" fill="#1E3538" />

            {/* Extract */}
            <rect x={172} y={215} width={88} height={54} rx={8} fill="#0A1516" stroke="#F0A85A" strokeWidth={1.2} />
            <text x={216} y={248} textAnchor="middle" fill="#F0A85A" fontSize={13} fontWeight={600}>Extract</text>

            {/* Branch arrow from Extract to Policy & Fraud */}
            <line x1={260} y1={242} x2={280} y2={242} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={280} y1={242} x2={280} y2={226} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={280} y1={242} x2={280} y2={258} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={280} y1={226} x2={300} y2={226} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="302,226 296,222 296,230" fill="#3EC1C5" />
            <line x1={280} y1={258} x2={300} y2={258} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="302,258 296,254 296,262" fill="#E56A76" />

            {/* Parallel label */}
            <text x={286} y={250} textAnchor="middle" fill="#6B8A8C" fontSize={9}>‖</text>

            {/* Policy (top parallel) */}
            <rect x={304} y={202} width={90} height={52} rx={8} fill="#0A1516" stroke="#3EC1C5" strokeWidth={1.2} />
            <text x={349} y={226} textAnchor="middle" fill="#3EC1C5" fontSize={11} fontWeight={600}>Policy</text>
            <text x={349} y={242} textAnchor="middle" fill="#6B8A8C" fontSize={9}>14 rules</text>

            {/* Fraud (bottom parallel) */}
            <rect x={304} y={256} width={90} height={52} rx={8} fill="#0A1516" stroke="#E56A76" strokeWidth={1.2} />
            <text x={349} y={280} textAnchor="middle" fill="#E56A76" fontSize={11} fontWeight={600}>Fraud</text>
            <text x={349} y={296} textAnchor="middle" fill="#6B8A8C" fontSize={9}>5 signals</text>

            {/* Merge arrows from Policy & Fraud to Decision */}
            <line x1={394} y1={226} x2={414} y2={226} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={394} y1={280} x2={414} y2={280} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={414} y1={226} x2={414} y2={242} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={414} y1={280} x2={414} y2={242} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={414} y1={242} x2={433} y2={242} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="435,242 429,238 429,246" fill="#1E3538" />

            {/* Decision */}
            <rect x={437} y={215} width={88} height={54} rx={8} fill="#0A1516" stroke="#F0A85A" strokeWidth={1.2} />
            <text x={481} y={248} textAnchor="middle" fill="#F0A85A" fontSize={13} fontWeight={600}>Decision</text>

            {/* Arrow down from pipeline */}
            <line x1={400} y1={315} x2={400} y2={343} stroke="#1E3538" strokeWidth={2} />
            <polygon points="400,345 395,335 405,335" fill="#1E3538" />

            {/* ===== Layer 4: Domain Services ===== */}
            <rect x={170} y={347} width={460} height={48} rx={10} fill="#0D1F21" stroke="#6B8A8C" strokeWidth={1.5} />
            <text x={400} y={377} textAnchor="middle" fill="#E8EDE9" fontSize={15} fontWeight={600}>
              📊 Domain Services
            </text>

            {/* Arrow down */}
            <line x1={400} y1={395} x2={400} y2={423} stroke="#1E3538" strokeWidth={2} />
            <polygon points="400,425 395,415 405,415" fill="#1E3538" />

            {/* ===== Layer 5: Infrastructure ===== */}
            <rect x={50} y={427} width={700} height={52} rx={10} fill="#0D1F21" stroke="#6B8A8C" strokeWidth={1} strokeDasharray="4 3" />
            <text x={400} y={460} textAnchor="middle" fill="#6B8A8C" fontSize={14}>
              PostgreSQL  |  Redis  |  LLM Providers  |  OpenTelemetry
            </text>
          </svg>
        </motion.div>
      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={3}
          src="/audio/slide-03.wav"
          title="System Architecture"
          transcript="The system is a modular monolith with four layers. The HTTP API layer in FastAPI accepts claims and returns 202 Accepted immediately. The orchestrator runs the 5-agent pipeline — verify, extract, policy, fraud, and decision. Domain services house pure business logic. The providers layer abstracts external services — LLMs, storage, caching, and document processing. I chose a modular monolith because the team is small, bounded contexts are still evolving, and in-process calls have lower latency for the pipeline. The trade-off is that everything scales as one unit, but the clean separation means splitting into microservices later is straightforward. Infrastructure runs on Docker Compose with nine services — FastAPI backend, Celery worker, Next.js frontend, PostgreSQL 17, Redis 7, Jaeger for distributed tracing, Prometheus for metrics, and Grafana for dashboards. Every service has health checks and proper dependency ordering."
        />
      </div>
    </div>
  );
}
