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

      for (const line of lines) {
        if (line.trim() === '') continue;
        
        if (line.startsWith('event: ')) {
          const eventType = line.slice(7).trim();
          const dataLine = lines[lines.indexOf(line) + 1];
          if (dataLine?.startsWith('data: ')) {
            try {
              const data = JSON.parse(dataLine.slice(6));
              
              // Handle segment concatenation for transcription events
              if (eventType === 'transcription' && lastSegment && lastSegment.speaker === data.speaker) {
                // Concatenate with previous segment
                lastSegment.text = `${lastSegment.text} ${data.text}`.trim();
                lastSegment.end = data.end;
                onEvent(eventType, lastSegment);
              } else {
                // New speaker or different event type
                lastSegment = eventType === 'transcription' ? { ...data } : null;
                onEvent(eventType, data);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}