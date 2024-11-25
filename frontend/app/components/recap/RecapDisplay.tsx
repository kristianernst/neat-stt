import { FiCopy, FiDownload } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import IconButton from '../shared/IconButton';
import Card from '../shared/Card';
import LoadingSpinner from '../shared/LoadingSpinner';
import ScrollableCard from '../shared/ScrollableCard';
import MarkdownRenderer from '../shared/MarkdownRenderer';

interface RecapDisplayProps {
  recap: string;
  isLoading: boolean;
}

export default function RecapDisplay({ recap, isLoading }: RecapDisplayProps) {
  const handleCopy = () => {
    navigator.clipboard.writeText(recap);
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
  };

  const CheckIcon = () => (
    <svg 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round"
      className="w-5 h-5"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );

  if (isLoading) {
    return (
      <Card className="mt-4 text-center">
        <LoadingSpinner className="mx-auto mb-4" />
        <p className="text-[var(--text-secondary)]">Generating recap...</p>
      </Card>
    );
  }

  if (!recap) return null;

  return (
    <div className="mt-4">
      <div className="flex justify-end mb-2 space-x-4">
        <IconButton
          icon={<FiCopy className="w-5 h-5" />}
          successIcon={<CheckIcon />}
          label="Copy"
          successLabel="Copied!"
          onClick={handleCopy}
        />
        <IconButton
          icon={<FiDownload className="w-5 h-5" />}
          successIcon={<CheckIcon />}
          label="Download"
          successLabel="Downloaded!"
          onClick={handleDownload}
        />
      </div>
      <ScrollableCard maxHeight="500px">
        <div className="p-6">
          <MarkdownRenderer content={recap} />
        </div>
      </ScrollableCard>
    </div>
  );
}