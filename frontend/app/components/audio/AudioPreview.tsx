import { memo } from 'react';
import Card from '../shared/Card';
import IconButton from '../shared/IconButton';
import { FiX } from 'react-icons/fi';
import AudioPlayer from './AudioPlayer';

interface AudioPreviewProps {
  file: File | null;
  onClose: () => void;
}

export default memo(function AudioPreview({ file, onClose }: AudioPreviewProps) {
  if (!file) return null;

  const audioUrl = URL.createObjectURL(file);

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium gradient-text">{file.name}</h3>
        <IconButton
          icon={<FiX className="w-5 h-5" />}
          label="Close preview"
          onClick={onClose}
        />
      </div>
      <AudioPlayer 
        src={audioUrl} 
        onEnded={() => URL.revokeObjectURL(audioUrl)} 
      />
    </Card>
  );
}); 