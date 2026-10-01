import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy, ExternalLink } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";
import type { ExtraProps } from "react-markdown";
import { LessonFigure } from "./figures/Figure";

export function CodeBlock({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);
  const copy = () => {
    const text = (ref.current?.textContent ?? "").replace(/\n$/, "");
    navigator.clipboard
      .writeText(text)
      .then(() => {
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1600);
      })
      .catch(() => setCopied(false));
  };
  return (
    <div className="code-block">
      <pre ref={ref} tabIndex={0}>
        {children}
      </pre>
      <button
        type="button"
        className={`copy-code ${copied ? "copied" : ""}`}
        aria-label={copied ? "Copied" : "Copy code"}
        title={copied ? "Copied" : "Copy code"}
        onClick={copy}
      >
        {copied ? <Check size={15} /> : <Copy size={15} />}
      </button>
    </div>
  );
}

export function referenceTitle(source: string) {
  const url = new URL(source);
  const topic = decodeURIComponent(
    url.pathname.split("/").filter(Boolean).at(-1) || "Documentation",
  )
    .replace(/\.(html|md|pdf)$/, "")
    .replace(/[-_]/g, " ");
  const title = topic.charAt(0).toUpperCase() + topic.slice(1);
  const publisher = url.hostname.replace(/^(www\.|docs\.|doc\.)/, "");
  return `${title} · ${publisher}`;
}

/** A fenced block written as ```figure with one figure ID embeds that figure. */
function figureId(node: ExtraProps["node"]): string | null {
  const code = node?.children[0];
  if (code?.type !== "element" || code.tagName !== "code") return null;
  const classes = code.properties.className;
  if (!Array.isArray(classes) || !classes.includes("language-figure"))
    return null;
  const text = code.children[0];
  return text?.type === "text" ? text.value.trim() : "";
}

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h2>{children}</h2>,
          h2: ({ children }) => <h3>{children}</h3>,
          h3: ({ children }) => <h4>{children}</h4>,
          h4: ({ children }) => <h5>{children}</h5>,
          h5: ({ children }) => <h6>{children}</h6>,
          pre: ({ node, children }) => {
            const figure = figureId(node);
            return figure === null ? (
              <CodeBlock>{children}</CodeBlock>
            ) : (
              <LessonFigure id={figure} />
            );
          },
          a: ({ children, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer">
              {children}
              <ExternalLink size={12} />
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
