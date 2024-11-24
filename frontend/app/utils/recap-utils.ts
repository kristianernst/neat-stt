interface TranscriptionSegment {
  start?: number;
  end?: number;
  timestamp?: string;
  speaker: string;
  text: string;
}

export function serializeTranscript(segments: TranscriptionSegment[]): string {
  // Sort segments by start time
  const sortedSegments = [...segments].sort((a, b) => (a.start || 0) - (b.start || 0));
  
  // Convert to string format
  return sortedSegments.map(segment => {
    const timestamp = segment.start !== undefined && segment.end !== undefined
      ? `[${formatTime(segment.start)} -> ${formatTime(segment.end)}]`
      : segment.timestamp || '';
    return `${timestamp}\n${segment.speaker}: ${segment.text}`;
  }).join('\n\n');
}

function formatTime(seconds: number): string {
  return new Date(seconds * 1000).toISOString().substr(11, 8);
}

export async function generateRecap(transcript: string): Promise<string> {
  try {
    const encodedTranscript = btoa(encodeURIComponent(transcript));
    const response = await fetch('http://localhost:8000/generate-recap', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        transcript: encodedTranscript,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to generate recap');
    }

    const data = await response.json();
    return data.recap;
  } catch (error) {
    console.error('Error generating recap:', error);
    throw error;
  }
}