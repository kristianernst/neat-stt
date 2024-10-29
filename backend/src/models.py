from pydantic import BaseModel, Field
from typing import Optional


class TranscriptionResponse(BaseModel):
  transcription: str = Field(..., description="The transcribed text")


class HealthResponse(BaseModel):
  status: str = Field(..., description="Health status of the service")
