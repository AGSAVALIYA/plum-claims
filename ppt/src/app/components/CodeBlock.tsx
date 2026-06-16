"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Check, ExternalLink } from "lucide-react";

interface CodeBlockProps {
  /** The code content to display */
  code: string;
  /** Language badge label, e.g. "python", "typescript", "json" */
  language?: string;
  /** Optional header text, e.g. "orchestrator/engine.py" */
  title?: string;
  /** Optional GitHub URL to the full file (renders an external link icon) */
  githubUrl?: string;
  /** Max height of the scrollable code area (default "300px") */
  maxHeight?: string;
  /** Line numbers to highlight visually (reserved for future use) */
  highlightedLines?: number[];
}

export default function CodeBlock({
  code,
  language,
  title,
  githubUrl,
  maxHeight = "300px",
  highlightedLines = [],
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
    } catch {
      // Fallback for older browsers or restricted contexts
      const textarea = document.createElement("textarea");
      textarea.value = code;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code.split("\n");

  const showTitleBar = !!(title || language || githubUrl);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="rounded-xl border border-border overflow-hidden bg-background"
    >
      {/* Title bar — only rendered when at least one of title/language/githubUrl is provided */}
      {showTitleBar && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-card border-b border-border">
          <div className="flex items-center gap-3 min-w-0">
            {language && (
              <span className="shrink-0 text-xs font-medium px-2 py-0.5 rounded-full bg-primary/20 text-primary leading-normal">
                {language}
              </span>
            )}
            {title && (
              <span className="text-sm text-foreground font-mono truncate">
                {title}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1 shrink-0">
            {/* Copy button */}
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-md text-muted hover:text-foreground hover:bg-secondary transition-colors"
              aria-label={copied ? "Copied" : "Copy code"}
              title="Copy code"
            >
              {copied ? (
                <Check className="w-4 h-4 text-primary" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>

            {/* GitHub / external link */}
            {githubUrl && (
              <a
                href={githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 rounded-md text-muted hover:text-foreground hover:bg-secondary transition-colors"
                aria-label="View on GitHub"
                title="View on GitHub"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>
      )}

      {/* Code area */}
      <div
        className="overflow-auto"
        style={{ maxHeight: showTitleBar ? maxHeight : undefined }}
      >
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((line, i) => {
              const lineNumber = i + 1;
              const isHighlighted = highlightedLines.includes(lineNumber);

              return (
                <tr
                  key={i}
                  className={
                    isHighlighted ? "bg-primary/[0.04]" : undefined
                  }
                >
                  {/* Line number gutter */}
                  <td className="text-right text-xs text-muted/50 select-none px-3 py-0 align-top whitespace-nowrap w-[1%] leading-relaxed">
                    {lineNumber}
                  </td>
                  {/* Code content */}
                  <td className="text-sm text-foreground font-mono px-3 py-0 whitespace-pre leading-relaxed">
                    {line || " "}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Thin scrollbar styling */}
      <style jsx>{`
        div.overflow-auto::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        div.overflow-auto::-webkit-scrollbar-track {
          background: transparent;
        }
        div.overflow-auto::-webkit-scrollbar-thumb {
          background: #1e3538;
          border-radius: 3px;
        }
        div.overflow-auto::-webkit-scrollbar-thumb:hover {
          background: #2a4a4d;
        }
        div.overflow-auto {
          scrollbar-width: thin;
          scrollbar-color: #1e3538 transparent;
        }
      `}</style>
    </motion.div>
  );
}
