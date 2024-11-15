from typing import Optional

from src.audio.transcription.base_transcription import BaseTranscriptionProcessor
from src.audio.transcription.whisper_transcription import WhisperTranscriptionProcessor
from src.audio.transcription.mms_transcription import MmsTranscriptionProcessor
from src.configuration.model_config import ModelConfig


def create_transcription_processor(
  model_config: ModelConfig | dict, device: str, language: Optional[str] = None
) -> BaseTranscriptionProcessor:
  """Factory function to create the appropriate transcription processor"""

  if isinstance(model_config, dict):
    model_config = ModelConfig.from_dict(model_config)

  if model_config.type == "whisper":
    return WhisperTranscriptionProcessor(model_config, device, language)
  elif model_config.type == "mms":
    return MmsTranscriptionProcessor(model_config, device, language)
  else:
    raise ValueError(f"Unsupported model type: {model_config.type}")
