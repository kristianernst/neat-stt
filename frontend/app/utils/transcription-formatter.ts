interface TranscriptionSegment {
  speaker: string;
  text: string;
  start?: number;
  end?: number;
  timestamp?: string; // Added to accommodate recorded transcriptions
}

export type { TranscriptionSegment };

export function formatTranscription(segments: TranscriptionSegment[], format: 'txt' | 'md'): string {
  return segments.map(segment => {
    const timestamp = segment.start !== undefined && segment.end !== undefined
      ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
      : segment.timestamp || '';

    if (format === 'md') {
      return `#### ${timestamp}\n**${segment.speaker}:** ${segment.text}\n`;
    } else {
      return `${timestamp}\n${segment.speaker}: ${segment.text}\n`;
    }
  }).join('\n');
}

function formatTime(seconds: number): string {
  return new Date(seconds * 1000).toISOString().substr(11, 8);
}
