from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np
import torch
from pydub import AudioSegment

from src.configuration.log import get_logger
from src.configuration.model_config import ModelConfig


class BaseTranscriptionProcessor(ABC):
  """Base class for transcription processors"""

  def __init__(self, model_config: ModelConfig | dict, device: str, language: Optional[str] = None):
    """
    Initialize the transcription processor

    Args:
        model_config (ModelConfig | dict): The model configuration
        device (str): The device to use for the model
        language (Optional[str]): The language to use for the model
    """
    self.device = device
    self.language = language
    self.logger = get_logger()

    # Convert dict to ModelConfig if necessary
    if isinstance(model_config, dict):
      model_config = ModelConfig.from_dict(model_config)

    self.model_config = model_config
    self.model_type = model_config.type

    try:
      self._init_model(model_config)
    except Exception as e:
      self.logger.error(f"Failed to initialize model: {str(e)}")
      raise

  @abstractmethod
  def _init_model(self, model_config: ModelConfig) -> None:
    """All Transcription Processors must implement this method to initialize the model and processor"""
    pass

  @abstractmethod
  def transcribe_chunk(self, chunk: AudioSegment, start_time: float, end_time: float, speaker: str, frame_rate: int) -> Dict[str, Any]:
    """All Transcription Processors must implement this method to transcribe a single audio chunk"""
    pass

  @abstractmethod
  def transcribe_chunks_batch(self, chunks: List[AudioSegment], metadata: List[Dict], frame_rate: int) -> List[Dict[str, Any]]:
    """All Transcription Processors must implement this method to transcribe a batch of audio chunks"""
    pass

  def _preprocess_audio(self, chunk: AudioSegment, frame_rate: int) -> torch.Tensor:
    """Standard method for common audio preprocessing logic"""
    samples = np.array(chunk.set_frame_rate(frame_rate).set_channels(1).get_array_of_samples())
    return torch.from_numpy(samples).float() / (2**15)
