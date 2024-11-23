from fastapi import APIRouter, HTTPException
from base64 import b64decode
from urllib.parse import unquote

from src.configuration.log import get_logger
from src.lm.recap import RecapGenerator
from src.pydantic_classes import RecapRequest, RecapResponse

class LLMController:
    """
    FastAPI controller for LLM-based operations like generating meeting/lecture recaps
    """
    def __init__(self):
        self.router = APIRouter()
        self.logger = get_logger()
        self.recap_generator = RecapGenerator(
            max_tokens=10_000,
            max_chunk_length=1800,
            chunk_strategy="semantic"
        )
        
        # Register routes
        self.router.post("/generate-recap", response_model=RecapResponse)(self.generate_recap)
        
    async def generate_recap(self, request: RecapRequest) -> RecapResponse:
        """
        Generate a structured recap from a transcript using the RecapGenerator
        """
        try:
            self.logger.info("Starting recap generation")
            
            # Deserialize the transcript
            decoded_bytes = b64decode(request.transcript)
            decoded_str = decoded_bytes.decode('utf-8')
            transcript = unquote(decoded_str)
            
            recap = self.recap_generator.generate_recap(transcript)
            
            return RecapResponse(
                recap=recap,
                status="success"
            )
            
        except Exception as e:
            self.logger.error(f"Recap generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate recap: {str(e)}"
            )
