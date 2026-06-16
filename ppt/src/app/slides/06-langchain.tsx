"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { AudioPlayer, CodeBlock } from "@/app/components";
import { githubFile } from "@/app/config";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

const rows: { concern: string; langchain: string; custom: string }[] = [
  {
    concern: "Abstraction",
    langchain: "500KB+ dependency",
    custom: "~200 lines per adapter",
  },
  {
    concern: "Debugging",
    langchain: "Opaque chain internals",
    custom: "Direct ProcessingTrace per step",
  },
  {
    concern: "Schema Validation",
    langchain: "Optional, inconsistent",
    custom: "Built-in with automatic retry",
  },
  {
    concern: "Cost Tracking",
    langchain: "No native support",
    custom: "Per-call, per-agent, per-claim",
  },
  {
    concern: "Vendor Lock-in",
    langchain: "OpenAI-first ecosystem",
    custom: "Equal support: OpenAI, Anthropic, Gemini, DeepSeek",
  },
  {
    concern: "Graceful Degradation",
    langchain: "Hard to implement",
    custom: "Native try/except with confidence reduction",
  },
  {
    concern: "Explainability",
    langchain: "Lost in chain abstraction",
    custom: "Every check, every decision, fully traceable",
  },
];

export default function Slide06LangChain() {
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
          AI Integration{" "}
          <span className="text-[#3EC1C5]">— Why NOT LangChain</span>
        </motion.h1>

        {/* Table */}
        <motion.div
          className="w-full overflow-hidden rounded-xl border border-[#1E3538]"
          variants={itemVariants}
        >
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-[#0D1F21] border-b border-[#1E3538]">
                <th className="px-5 py-3 font-semibold text-[#E8EDE9] w-1/5">
                  Concern
                </th>
                <th className="px-5 py-3 font-semibold text-[#E56A76] w-2/5">
                  <div className="flex items-center gap-2">
                    <XCircle size={16} />
                    LangChain
                  </div>
                </th>
                <th className="px-5 py-3 font-semibold text-[#3EC1C5] w-2/5">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} />
                    Our Custom Solution
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr
                  key={row.concern}
                  className={`border-b border-[#1E3538] ${
                    i % 2 === 0 ? "bg-[#0A1516]" : "bg-[#0D1F21]"
                  }`}
                >
                  <td className="px-5 py-3 font-medium text-[#E8EDE9]">
                    {row.concern}
                  </td>
                  <td className="px-5 py-3 text-[#6B8A8C]">{row.langchain}</td>
                  <td className="px-5 py-3 text-[#3EC1C5]">{row.custom}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>

        {/* Code snippet: LLM interface */}
        <motion.div className="w-full max-w-3xl" variants={itemVariants}>
          <CodeBlock
            code={`class ILLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def chat(
        self, messages: list[ChatMessage], **kwargs
    ) -> ChatResponse: ...

    @abstractmethod
    async def extract_structured(
        self, messages: list[ChatMessage], schema: type[T], **kwargs
    ) -> T: ...

    @abstractmethod
    async def health_check(self) -> bool: ...`}
            language="python"
            title="providers/llm/interface.py"
            githubUrl={githubFile("backend/providers/llm/interface.py")}
            maxHeight="200px"
          />
        </motion.div>

        {/* Quote */}
        <motion.div
          className="flex items-start gap-3 max-w-3xl mt-2"
          variants={itemVariants}
        >
          <AlertTriangle size={20} className="text-[#F0A85A] mt-0.5 shrink-0" />
          <p className="text-base italic text-[#6B8A8C] leading-relaxed">
            Anthropic's guidance:{" "}
            <span className="text-[#E8EDE9] not-italic">
              "Start simple, add complexity only when needed."
            </span>{" "}
            Our 5-step pipeline is simple. It works. It's explainable. It didn't
            need a framework.
          </p>
        </motion.div>
      </motion.div>

      {/* Audio player */}
      <div className="w-full flex justify-center z-[100] mt-12">
        <AudioPlayer
          slideNumber={6}
          src="/audio/slide-06.wav"
          title="AI Integration - Why NOT LangChain"
          transcript="Let me explain why I deliberately chose NOT to use LangChain or LangGraph. LangChain adds a 500-kilobyte-plus dependency for what is essentially five async function calls with try-except around each. Debugging LangChain is notoriously difficult — you get opaque error traces. Our custom orchestrator gives us a complete ProcessingTrace with per-step input, output, confidence, and timing. Schema validation is another issue — our adapters have built-in validation with automatic retry on malformed LLM output. Cost tracking is per-call, per-agent, per-claim — at scale, this matters. And we avoid vendor lock-in — one interface supports OpenAI, Anthropic, Gemini, and DeepSeek equally. As Anthropic's guidance says: start simple, add complexity only when needed. Our five-step pipeline is simple, it works, and it's fully explainable."
        />
      </div>
    </div>
  );
}
