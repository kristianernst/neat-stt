from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from ..models import TranscriptionResponse, HealthResponse
from ..hf_tts import HuggingFaceSTT
import os
import tempfile
from typing import Optional
import logging


class TranscriptionController:
  def __init__(self):
    self.router = APIRouter()
    self.logger = logging.getLogger(self.__class__.__name__)
    self.transcriber = HuggingFaceSTT(model=os.getenv("MODEL_ID", "openai/whisper-large-v3"), device="infer", verbose=True)

    # Register routes
    self.router.post("/transcribe", response_model=TranscriptionResponse)(self.transcribe_audio)
    self.router.get("/health", response_model=HealthResponse)(self.health_check)

  async def transcribe_audio(
    self, file: UploadFile = File(...), language: Optional[str] = Form("english"), num_speakers: Optional[int] = Form(None)
  ):
    """
    Endpoint to transcribe an uploaded audio file.
    """
    try:
      # Create a temporary file to store the uploaded audio
      with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        # Write uploaded file content to temporary file
        content = await file.read()
        temp_file.write(content)
        temp_file.flush()

        # Update transcriber settings if provided
        if language:
          self.transcriber.language = language
        if num_speakers:
          self.transcriber.num_speakers = num_speakers

        # Perform transcription
        transcription = await self.transcriber.transcribe(temp_file.name)

      # Clean up the temporary file
      os.unlink(temp_file.name)

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
