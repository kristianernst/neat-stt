import { ReactNode } from 'react';
import { FiX } from 'react-icons/fi';
import Card from './Card';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  maxWidth?: string;
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = 'max-w-2xl'
}: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="min-h-screen px-4 text-center">
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        />

        <div className={`inline-block w-full ${maxWidth} my-8 text-left align-middle transition-all transform`}>
          <Card className="relative bg-[var(--bg-primary)]">
            {title && (
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold gradient-text">{title}</h2>
                <button 
                  onClick={onClose}
                  className="p-2 hover:bg-[var(--card-hover)] rounded-lg transition-colors"
                >
                  <FiX className="w-6 h-6 text-[var(--text-secondary)]" />
                </button>
              </div>
            )}
            {children}
          </Card>
        </div>
      </div>
    </div>
  );
} 