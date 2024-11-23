from pydantic import BaseModel, Field, field_validator
import base64


class HealthResponse(BaseModel):
  status: str = Field(..., description="Health status of the service")

class RecapRequest(BaseModel):
    transcript: str
    
    @field_validator('transcript')
    def validate_transcript(cls, v):
        try:
            # Verify it's valid base64
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError('Invalid base64 encoded transcript')

class RecapResponse(BaseModel):
    recap: str
    status: str