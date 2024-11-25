import ReactMarkdown from 'react-markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      className={`prose prose-invert max-w-none space-y-6 ${className}`}
      components={{
        h1: ({children}) => (
          <h1 className="text-[var(--main-accent)] font-sans font-normal mb-8">{children}</h1>
        ),
        h2: ({children}) => (
          <h2 className="text-[var(--main-accent)] font-sans font-normal mb-6">{children}</h2>
        ),
        h3: ({children}) => (
          <h3 className="text-[var(--main-accent)] font-sans font-normal mb-4">{children}</h3>
        ),
        h4: ({children}) => (
          <h4 className="text-[var(--main-accent)] font-sans font-normal mb-4">{children}</h4>
        ),
        p: ({children}) => (
          <p className="text-[var(--text-primary)] leading-relaxed font-serif mb-4">{children}</p>
        ),
        ul: ({children}) => (
          <ul className="text-[var(--text-primary)] font-serif space-y-2 mb-4">{children}</ul>
        ),
        li: ({children}) => (
          <li className="text-[var(--text-primary)] font-serif ml-4">{children}</li>
        ),
        strong: ({children}) => (
          <strong className="text-[var(--main-accent)] font-sans font-normal mb-4">{children}</strong>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
} 