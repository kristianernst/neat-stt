from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.controllers import TranscriptionController, LLMController

app = FastAPI()

# Configure CORS
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # In production, replace with specific origins
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Initialize and register the controllers
transcription_controller = TranscriptionController()
llm_controller = LLMController()

app.include_router(transcription_controller.router, tags=["transcription"])
app.include_router(llm_controller.router, tags=["llm"])
