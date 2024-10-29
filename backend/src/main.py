from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .controllers.transcription_controller import TranscriptionController

app = FastAPI()

# Configure CORS
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],  # In production, replace with specific origins
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Initialize and register the controller
transcription_controller = TranscriptionController()
app.include_router(transcription_controller.router, tags=["transcription"])
