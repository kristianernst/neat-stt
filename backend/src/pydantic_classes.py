from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
  status: str = Field(..., description="Health status of the service")
