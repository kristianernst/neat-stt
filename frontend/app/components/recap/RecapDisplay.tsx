import { useState } from 'react';
import { FiCopy, FiDownload } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';

interface RecapDisplayProps {
  recap: string;
  isLoading: boolean;
}

export default function RecapDisplay({ recap, isLoading }: RecapDisplayProps) {
  const [copySuccess, setCopySuccess] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(recap);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([recap], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'recap.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setDownloadSuccess(true);
    setTimeout(() => setDownloadSuccess(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="mt-4 card p-6 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-[var(--gradient-start)] border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-[var(--text-secondary)]">Generating recap...</p>
      </div>
    );
  }

  if (!recap) return null;

  return (
    <div className="mt-4">
      <div className="flex justify-end mb-2 space-x-4">
        <button
          onClick={handleCopy}
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                   focus:outline-none flex items-center space-x-1 group relative"
          disabled={copySuccess}
        >
          <div className="relative w-5 h-5">
            <FiCopy 
              className={`w-5 h-5 absolute transition-all duration-300 ${
                copySuccess ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
              }`}
            />
            <svg 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className={`w-5 h-5 absolute transition-all duration-300 ${
                copySuccess 
                  ? 'opacity-100 scale-100 text-[var(--success-text)]' 
                  : 'opacity-0 scale-75'
              }`}
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={`text-sm transition-colors duration-300 ${
            copySuccess ? 'text-[var(--success-text)]' : ''
          }`}>
            {copySuccess ? 'Copied!' : 'Copy'}
          </span>
        </button>
        <button
          onClick={handleDownload}
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                   focus:outline-none flex items-center space-x-1 group relative"
          disabled={downloadSuccess}
        >
          <div className="relative w-5 h-5">
            <FiDownload 
              className={`w-5 h-5 absolute transition-all duration-300 ${
                downloadSuccess ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
              }`}
            />
            <svg 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              className={`w-5 h-5 absolute transition-all duration-300 ${
                downloadSuccess 
                  ? 'opacity-100 scale-100 text-[var(--success-text)]' 
                  : 'opacity-0 scale-75'
              }`}
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={`text-sm transition-colors duration-300 ${
            downloadSuccess ? 'text-[var(--success-text)]' : ''
          }`}>
            {downloadSuccess ? 'Downloaded!' : 'Download'}
          </span>
        </button>
      </div>
      <div className="card p-6 prose prose-invert max-w-none">
        <ReactMarkdown
          components={{
            h1: ({children}) => <h1 className="text-[var(--main-accent)] font-serif">{children}</h1>,
            h2: ({children}) => <h2 className="text-[var(--main-accent)] font-serif">{children}</h2>,
            h3: ({children}) => <h3 className="text-[var(--text-primary)] font-serif">{children}</h3>,
            p: ({children}) => <p className="text-[var(--text-primary)] leading-relaxed font-serif">{children}</p>,
            ul: ({children}) => <ul className="text-[var(--text-primary)] font-serif">{children}</ul>,
            li: ({children}) => <li className="text-[var(--text-primary)] font-serif">{children}</li>,
          }}
        >
          {recap}
        </ReactMarkdown>
      </div>
    </div>
  );
}