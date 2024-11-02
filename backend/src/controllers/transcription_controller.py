import os
import tempfile
from typing import Optional, Dict, Any, AsyncGenerator
import asyncio
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from sse_starlette.sse import EventSourceResponse

from src.pydantic_classes import TranscriptionResponse, HealthResponse
from src.audio.stt import SpeechToText
from src.configuration.log import get_logger


class TranscriptionController:
  def __init__(self):
    self.router = APIRouter()
    self.logger = get_logger()
    self.stt = SpeechToText()
    # Register routes
    self.router.post("/transcribe", response_model=TranscriptionResponse)(self.transcribe_audio)
    self.router.get("/health", response_model=HealthResponse)(self.health_check)
    self.router.get("/live-transcribe")(self.live_transcribe)
    self.router.post("/stop-live-transcribe")(self.stop_live_transcribe)

  async def transcribe_audio(
    self, file: UploadFile = File(...), language: Optional[str] = Form("english"), num_speakers: Optional[int] = Form(None)
  ):
    """
    Endpoint to transcribe an uploaded audio file.
    """
    try:
      self.stt._update_settings(language, num_speakers)
      # Create a temporary file to store the uploaded audio
      with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        # Write uploaded file content to temporary file
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()

        # Perform transcription in a separate thread
        loop = asyncio.get_event_loop()
        transcription = await loop.run_in_executor(None, self.stt.transcribe, temp_file.name)
        
      # Clean up the temporary file
      os.unlink(temp_file.name)
      
      self.logger.info(f"Transcription: {transcription}")

      return TranscriptionResponse(transcription=transcription)

    except Exception as e:
      self.logger.error(f"Transcription error: {str(e)}")
      raise HTTPException(status_code=500, detail=str(e))

  async def health_check(self):
    """
    Endpoint to check the health status of the service.
    """
    try:
      return HealthResponse(status="healthy")
    except Exception as e:
      self.logger.error(f"Health check failed: {str(e)}")
      return HealthResponse(status="unhealthy")

  async def live_transcribe(
    self,
    language: Optional[str] = "english",
    num_speakers: Optional[int] = 2,
    chunk_duration_ms: Optional[int] = 5000,
    save_debug: Optional[bool] = False
  ) -> EventSourceResponse:
    """
    Endpoint for live audio transcription using Server-Sent Events (SSE).
    """
    try:
        self.logger.info("Starting live transcription stream...")
        self.stt._update_settings(language, num_speakers)
        
        async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
            try:
                # Initialize transcription before sending ready event
                transcription_gen = self.stt.transcribe_live(
                    chunk_duration_ms=chunk_duration_ms,
                    save_debug=save_debug
                )
                
                # Send ready event after initialization
                yield {
                    "event": "ready",
                    "data": json.dumps({"status": "ready"})
                }
                
                # Process transcription results
                for result in transcription_gen:
                    if result and result.get("text", "").strip():
                        self.logger.info(f"\n\n\nTranscription result: {result}\n\n\n")
                        yield {
                            "event": "transcription",
                            "data": json.dumps(result)
                        }
                    await asyncio.sleep(0.02)
            except Exception as e:
                self.logger.error(f"Live transcription error: {str(e)}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
            finally:
                yield {
                    "event": "close",
                    "data": json.dumps({"message": "Stream closed"})
                }

        return EventSourceResponse(event_generator())

    except Exception as e:
        self.logger.error(f"Failed to start live transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

  async def stop_live_transcribe(self) -> Dict[str, str]:
    """
    Stop the live transcription and cleanup resources.
    """
    try:
        self.logger.info("Stopping live transcription...")
        # Set a timeout for the stop operation
        stop_timeout = 3  # seconds
        
        def stop_with_timeout():
            self.stt.stop_live_transcription()
            
        # Run stop operation with timeout
        try:
            await asyncio.wait_for(
                asyncio.to_thread(stop_with_timeout), 
                timeout=stop_timeout
            )
            return {"status": "stopped"}
        except asyncio.TimeoutError:
            self.logger.error("Stop operation timed out, forcing stop...")
            # Force stop if timeout occurs
            if hasattr(self.stt, 'recorder'):
                self.stt.recorder = None
            self.stt.is_running = False
            return {"status": "force_stopped"}
            
    except Exception as e:
        self.logger.error(f"Failed to stop live transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
