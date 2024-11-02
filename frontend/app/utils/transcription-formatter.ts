interface TranscriptionSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
}

export type { TranscriptionSegment };

export function formatTranscription(segments: TranscriptionSegment[], format: 'txt' | 'md'): string {
  if (format === 'md') {
    return segments.map(segment => {
      const timestamp = `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`;
      return `#### ${timestamp}\n**${segment.speaker}:** ${segment.text}\n`;
    }).join('\n');
  } else {
    return segments.map(segment => {
      const timestamp = `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`;
      return `${timestamp}\n${segment.speaker}: ${segment.text}\n`;
    }).join('\n');
  }
}

function formatTime(seconds: number): string {
  return new Date(seconds * 1000).toISOString().substr(11, 8);
} 