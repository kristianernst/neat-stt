from typing import Optional

import torch
from pyannote.audio import Pipeline  # type: ignore

from src.configuration.environment import DIARIZATION_MODEL, HF_TOKEN
from src.configuration.log import get_logger


class DiarizationProcessor:
  def __init__(self, device: str, num_speakers: Optional[int] = None):
    self.device = device
    self.num_speakers = num_speakers
    self.logger = get_logger()
    self._init_diarization_model()

  def _init_diarization_model(self) -> None:
    """
    Initialize the speaker diarization model.
    """
    self.logger.info("Initializing diarization model ...")
    self.diarization_model = Pipeline.from_pretrained(
      DIARIZATION_MODEL,
      use_auth_token=HF_TOKEN,
    ).to(torch.device(self.device))

  def perform_diarization(self, waveform: torch.Tensor, sample_rate: int):
    """
    Perform speaker diarization on the audio.
    """
    self.logger.info("Performing speaker diarization ...")
    diarization = self.diarization_model(
      {"waveform": waveform, "sample_rate": sample_rate},
      num_speakers=self.num_speakers,
    )
    return diarization

  def process_diarization_segments(self, diarization):
    """
    Process diarization results into a usable format.
    """
    diarization_segments = list(diarization.itertracks(yield_label=True))
    self.logger.info(f"Detected {len(set(label for _, _, label in diarization_segments))} speakers.")
    return diarization_segments
