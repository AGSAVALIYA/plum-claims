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

const outcomes = [
  { label: "APPROVED", color: "#3EC1C5" },
  { label: "PARTIAL", color: "#F0A85A" },
  { label: "REJECTED", color: "#E56A76" },
  { label: "MANUAL_REVIEW", color: "#6B8A8C" },
];

const keyPoints = [
  "✅ Early gate stops invalid claims before LLM calls (saves cost)",
  "⚡ Policy + Fraud run in parallel via asyncio.gather (40% faster)",
  "🛡️ Graceful degradation — any agent can fail, pipeline continues",
  "📋 Full ProcessingTrace — every check, every decision, fully explainable",
];

export default function Slide05Pipeline() {
  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-20 px-4 md:p-12 pb-32 relative bg-[#0A1516]">
      

      <motion.div
        className="flex flex-col items-center w-full max-w-5xl gap-5"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Title */}
        <motion.h2
          className="text-4xl md:text-5xl font-bold text-white tracking-tight"
          variants={itemVariants}
        >
          Multi-Agent Pipeline
        </motion.h2>

        <motion.p
          className="text-lg text-[#3EC1C5] mb-1"
          variants={itemVariants}
        >
          5-Step Orchestrated Processing with Parallel Execution
        </motion.p>

        {/* SVG Flow Diagram */}
        <motion.div variants={itemVariants} className="w-full flex justify-center">
          <svg
            viewBox="0 0 800 270"
            className="w-full max-w-[780px]"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Step 1: Document Verification */}
            <rect x={10} y={10} width={150} height={56} rx={10} fill="#0D1F21" stroke="#3EC1C5" strokeWidth={1.5} />
            <text x={85} y={32} textAnchor="middle" fill="#3EC1C5" fontSize={11} fontWeight={600}>Step 1</text>
            <text x={85} y={50} textAnchor="middle" fill="#E8EDE9" fontSize={11}>Document</text>
            <text x={85} y={62} textAnchor="middle" fill="#E8EDE9" fontSize={11}>Verification</text>

            {/* Red STOP gate */}
            <rect x={175} y={16} width={46} height={44} rx={8} fill="#E56A7620" stroke="#E56A76" strokeWidth={1.5} />
            <text x={198} y={44} textAnchor="middle" fill="#E56A76" fontSize={13} fontWeight={700}>STOP</text>

            {/* Arrow to Step 2 */}
            <line x1={221} y1={38} x2={244} y2={38} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="246,38 240,34 240,42" fill="#1E3538" />

            {/* Step 2: Document Extraction */}
            <rect x={248} y={10} width={150} height={56} rx={10} fill="#0D1F21" stroke="#F0A85A" strokeWidth={1.5} />
            <text x={323} y={32} textAnchor="middle" fill="#F0A85A" fontSize={11} fontWeight={600}>Step 2</text>
            <text x={323} y={50} textAnchor="middle" fill="#E8EDE9" fontSize={11}>Document</text>
            <text x={323} y={62} textAnchor="middle" fill="#E8EDE9" fontSize={11}>Extraction (LLM)</text>

            {/* Arrow down splitting into two branches */}
            <line x1={323} y1={66} x2={323} y2={90} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={220} y1={90} x2={426} y2={90} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={220} y1={90} x2={220} y2={115} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="220,117 216,109 224,109" fill="#3EC1C5" />
            <line x1={426} y1={90} x2={426} y2={115} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="426,117 422,109 430,109" fill="#E56A76" />

            {/* Parallel label */}
            <text x={323} y={88} textAnchor="middle" fill="#6B8A8C" fontSize={10}>parallel</text>

            {/* Step 3 & 4 side by side */}
            <rect x={145} y={117} width={150} height={56} rx={10} fill="#0D1F21" stroke="#3EC1C5" strokeWidth={1.5} />
            <text x={220} y={139} textAnchor="middle" fill="#3EC1C5" fontSize={11} fontWeight={600}>Step 3</text>
            <text x={220} y={157} textAnchor="middle" fill="#E8EDE9" fontSize={11}>Policy Evaluation</text>
            <text x={220} y={169} textAnchor="middle" fill="#6B8A8C" fontSize={9}>14 rules</text>

            <rect x={305} y={117} width={150} height={56} rx={10} fill="#0D1F21" stroke="#E56A76" strokeWidth={1.5} />
            <text x={380} y={139} textAnchor="middle" fill="#E56A76" fontSize={11} fontWeight={600}>Step 4</text>
            <text x={380} y={157} textAnchor="middle" fill="#E8EDE9" fontSize={11}>Fraud Detection</text>
            <text x={380} y={169} textAnchor="middle" fill="#6B8A8C" fontSize={9}>5 signals</text>

            {/* Brace / merge arrows */}
            <line x1={220} y1={173} x2={220} y2={195} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={380} y1={173} x2={380} y2={195} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={220} y1={195} x2={380} y2={195} stroke="#1E3538" strokeWidth={1.5} />
            <line x1={300} y1={195} x2={300} y2={215} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="300,217 296,209 304,209" fill="#1E3538" />

            {/* Step 5: Decision Aggregation */}
            <rect x={225} y={220} width={150} height={44} rx={10} fill="#0D1F21" stroke="#F0A85A" strokeWidth={1.5} />
            <text x={300} y={240} textAnchor="middle" fill="#F0A85A" fontSize={11} fontWeight={600}>Step 5</text>
            <text x={300} y={254} textAnchor="middle" fill="#E8EDE9" fontSize={10}>Decision Aggregation</text>

            {/* Outcomes row */}
            {outcomes.map((outcome, i) => (
              <g key={outcome.label}>
                <rect x={400 + i * 100} y={228} width={92} height={28} rx={6} fill={`${outcome.color}15`} stroke={outcome.color} strokeWidth={1} />
                <text x={446 + i * 100} y={246} textAnchor="middle" fill={outcome.color} fontSize={9} fontWeight={600}>
                  {outcome.label}
                </text>
              </g>
            ))}

            {/* Arrow from Step 5 to outcomes */}
            <line x1={375} y1={242} x2={395} y2={242} stroke="#1E3538" strokeWidth={1.5} />
            <polygon points="397,242 391,238 391,246" fill="#1E3538" />
          </svg>
        </motion.div>

        {/* Key points */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-1 md:grid-cols-2 gap-3 w-full mt-2"
          variants={itemVariants}
        >
          {keyPoints.map((point, i) => (
            <div
              key={i}
              className="bg-[#0D1F21] border border-[#1E3538] rounded-xl p-3.5 text-sm text-[#E8EDE9] leading-relaxed"
            >
              {point}
            </div>
          ))}
        </motion.div>
        {/* Screenshot */}
        <motion.div
          className="w-full flex justify-center mt-6"
          variants={itemVariants}
        >
          <img 
            src="/screenshots/document-error.png" 
            alt="Document Error Example" 
            className="rounded-xl border border-[#1E3538] max-w-full shadow-lg object-contain max-h-[250px]"
          />
        </motion.div>

      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={5}
          src="/audio/slide-05.wav"
          title="Multi-Agent Pipeline"
          transcript="The multi-agent pipeline is the core of the system. When a claim is submitted, the API returns 202 Accepted immediately, and processing happens asynchronously. Step 1 is Document Verification — the early gate. If documents are wrong, the pipeline stops immediately before any LLM calls, saving money. As you can see in the screenshot below, the system explicitly meets the system requirements by telling the member exactly what document type was uploaded and what is needed instead. Step 2 is Document Extraction using LLMs to pull structured data from messy medical documents — patient names, diagnoses, amounts. Steps 3 and 4 run in parallel using asyncio.gather — Policy Evaluation checks against 14 rules, while Fraud Detection computes a weighted score from 5 signals. This parallelization reduces pipeline latency by about 40%. Step 5 is Decision Aggregation — it combines all results into one of four decisions: Approved, Partial, Rejected, or Manual Review. Most importantly, if any agent fails, the pipeline doesn't crash. The error is caught, confidence is reduced, and remaining agents continue with whatever data they have."
        />
      </div>
    </div>
  );
}
