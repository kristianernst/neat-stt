export async function processSSEStream(
  stream: ReadableStream,
  onEvent: (eventType: string, data: any) => void
) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let lastSegment: any = null;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.trim() === '') continue;

        if (line.startsWith('event: ')) {
          const eventType = line.slice(7).trim();
          const dataLine = lines[i + 1]; // Access the next line directly
          if (dataLine?.startsWith('data: ')) {
            try {
              const data = JSON.parse(dataLine.slice(6));
              
              // Handle segment concatenation for transcription events
              if (eventType === 'transcription') {
                if (lastSegment && lastSegment.speaker === data.speaker && 
                    Math.abs(lastSegment.end - data.start) < 0.5) { // Add time threshold check
                  // Concatenate with previous segment only if they're close in time
                  lastSegment.text = `${lastSegment.text} ${data.text}`.trim();
                  lastSegment.end = data.end;
                  onEvent(eventType, lastSegment);
                } else {
                  // New speaker or time gap too large
                  lastSegment = { ...data };
                  onEvent(eventType, data);
                }
              } else {
                lastSegment = null;
                onEvent(eventType, data);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
            i++; // Skip the data line since it's already processed
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}