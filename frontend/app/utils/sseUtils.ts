export async function processSSEStream(
  stream: ReadableStream,
  onEvent: (eventType: string, data: any) => void
) {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

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
          const dataLine = lines[i + 1];
          if (dataLine?.startsWith('data: ')) {
            try {
              const data = JSON.parse(dataLine.slice(6));
              onEvent(eventType, data);
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