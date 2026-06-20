import { cn } from "@/lib/utils";
import type { AgentId } from "@/services/artifactClient";
import { resolveArtifactUrl } from "@/services/artifactClient";
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { HTMLAttributes } from "react";

export interface MarkdownViewerProps {
  content: string;
  agent?: AgentId;
  sessionId?: string | null;
  baseUrl?: string;
  className?: string;
}

function stripFrontmatter(content: string): string {
  if (!content.startsWith("---")) return content;
  const end = content.indexOf("---", 3);
  if (end === -1) return content;
  return content.slice(end + 3).trimStart();
}

function CodeBlock({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLElement> & { inline?: boolean }) {
  const match = /language-(\w+)/.exec(className ?? "");
  const language = match?.[1];

  if (!className) {
    return (
      <code
        className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.875em] text-foreground"
        {...props}
      >
        {children}
      </code>
    );
  }

  return (
    <div className="group relative my-4 overflow-hidden rounded-lg border bg-zinc-950 dark:bg-zinc-900">
      {language && (
        <div className="border-b border-zinc-800 px-4 py-1.5 text-xs font-medium uppercase tracking-wide text-zinc-400">
          {language}
        </div>
      )}
      <pre className="overflow-x-auto p-4 text-sm leading-relaxed">
        <code className={cn("font-mono text-zinc-100", className)} {...props}>
          {children}
        </code>
      </pre>
    </div>
  );
}

export function MarkdownViewer({
  content,
  agent,
  sessionId,
  baseUrl,
  className,
}: MarkdownViewerProps) {
  const body = stripFrontmatter(content);
  const assetRoot =
    baseUrl ??
    (sessionId && agent
      ? `/api/artifacts/runs/${sessionId}/${agent}/`
      : agent
        ? `/api/artifacts/${agent}/`
        : undefined);

  const components: Components = {
    h1: ({ children }) => (
      <h1 className="mb-4 mt-8 scroll-m-20 text-3xl font-bold tracking-tight first:mt-0">
        {children}
      </h1>
    ),
    h2: ({ children }) => (
      <h2 className="mb-3 mt-8 scroll-m-20 border-b pb-2 text-2xl font-semibold tracking-tight first:mt-0">
        {children}
      </h2>
    ),
    h3: ({ children }) => (
      <h3 className="mb-2 mt-6 scroll-m-20 text-xl font-semibold tracking-tight">
        {children}
      </h3>
    ),
    h4: ({ children }) => (
      <h4 className="mb-2 mt-4 scroll-m-20 text-lg font-semibold tracking-tight">
        {children}
      </h4>
    ),
    p: ({ children }) => (
      <p className="leading-7 [&:not(:first-child)]:mt-4">{children}</p>
    ),
    a: ({ href, children }) => (
      <a
        href={href}
        className="font-medium text-primary underline underline-offset-4 hover:text-primary/80"
        target={href?.startsWith("http") ? "_blank" : undefined}
        rel={href?.startsWith("http") ? "noreferrer noopener" : undefined}
      >
        {children}
      </a>
    ),
    ul: ({ children }) => (
      <ul className="my-4 ml-6 list-disc [&>li]:mt-2">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="my-4 ml-6 list-decimal [&>li]:mt-2">{children}</ol>
    ),
    li: ({ children }) => <li className="leading-7">{children}</li>,
    blockquote: ({ children }) => (
      <blockquote className="my-4 border-l-4 border-primary/40 bg-muted/40 py-1 pl-4 italic text-muted-foreground">
        {children}
      </blockquote>
    ),
    hr: () => <hr className="my-8 border-border" />,
    table: ({ children }) => (
      <div className="my-6 w-full overflow-x-auto rounded-lg border">
        <table className="w-full caption-bottom text-sm">{children}</table>
      </div>
    ),
    thead: ({ children }) => (
      <thead className="border-b bg-muted/50 [&_tr]:border-b">{children}</thead>
    ),
    tbody: ({ children }) => (
      <tbody className="[&_tr:last-child]:border-0">{children}</tbody>
    ),
    tr: ({ children }) => (
      <tr className="border-b transition-colors hover:bg-muted/30">{children}</tr>
    ),
    th: ({ children }) => (
      <th className="h-10 px-4 text-left align-middle text-xs font-medium text-muted-foreground">
        {children}
      </th>
    ),
    td: ({ children }) => (
      <td className="p-4 align-middle [&>code]:text-xs">{children}</td>
    ),
    code: ({ className, children, ...props }) => {
      const isInline =
        !className && typeof children === "string" && !children.includes("\n");

      if (isInline) {
        return (
          <code
            className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.875em]"
            {...props}
          >
            {children}
          </code>
        );
      }
      return (
        <CodeBlock className={className} {...props}>
          {children}
        </CodeBlock>
      );
    },
    pre: ({ children }) => <>{children}</>,
    img: ({ src, alt, title }) => {
      const resolved =
        assetRoot && src && agent
          ? resolveArtifactUrl(sessionId ?? null, agent, src)
          : src;

      if (!resolved) return null;

      return (
        <figure className="my-6">
          <img
            src={resolved}
            alt={alt ?? ""}
            title={title}
            className="max-w-full rounded-lg border bg-muted/20 object-contain"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.classList.add("opacity-40");
              e.currentTarget.alt = alt ? `${alt} (not found)` : "Image not found";
            }}
          />
          {(alt || title) && (
            <figcaption className="mt-2 text-center text-xs text-muted-foreground">
              {alt ?? title}
            </figcaption>
          )}
        </figure>
      );
    },
    strong: ({ children }) => (
      <strong className="font-semibold text-foreground">{children}</strong>
    ),
    em: ({ children }) => <em className="italic">{children}</em>,
  };

  return (
    <article
      className={cn(
        "markdown-viewer max-w-none text-sm text-foreground",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {body}
      </ReactMarkdown>
    </article>
  );
}
