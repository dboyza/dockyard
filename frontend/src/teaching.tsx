import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExternalLink } from "lucide-react";

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

export function Topology({ compact = false }: { compact?: boolean }) {
  return (
    <svg
      className="topology"
      viewBox={compact ? "0 0 670 160" : "0 0 670 220"}
      role="img"
      aria-label="Dispatch evolves from an API into a system with a queue, worker, and database"
    >
      <path className="wire" d="M150 80H245 M385 80H490 M560 110V175H320V110" />
      <g>
        <rect className="node" x="10" y="45" width="140" height="70" rx="9" />
        <text x="80" y="73" textAnchor="middle">
          Your browser
        </text>
        <text className="subtext" x="80" y="96" textAnchor="middle">
          HTTP request
        </text>
      </g>
      <g>
        <rect
          className="node focusnode"
          x="245"
          y="35"
          width="140"
          height="90"
          rx="9"
        />
        <text x="315" y="71" textAnchor="middle">
          Dispatch API
        </text>
        <text className="subtext" x="315" y="96" textAnchor="middle">
          Your first container
        </text>
      </g>
      <g>
        <rect
          className="node future"
          x="490"
          y="45"
          width="165"
          height="70"
          rx="9"
        />
        <text x="572" y="73" textAnchor="middle">
          Queue + worker
        </text>
        <text className="subtext" x="572" y="96" textAnchor="middle">
          Introduced as you learn
        </text>
      </g>
      {!compact && (
        <g>
          <rect
            className="node"
            x="245"
            y="148"
            width="140"
            height="60"
            rx="9"
          />
          <text x="315" y="183" textAnchor="middle">
            PostgreSQL
          </text>
        </g>
      )}
      {compact && (
        <rect x="240" y="145" width="430" height="15" fill="var(--surface)" />
      )}
    </svg>
  );
}
