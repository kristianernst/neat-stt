from functools import lru_cache
from typing import Dict, Any, List

import numpy as np
import torch
from pydub import AudioSegment
from transformers import WhisperForConditionalGeneration, WhisperProcessor




from src.configuration.log import get_logger

logger = get_logger()

class TranscriptionProcessor:
    def __init__(self, model_name: str, device: str, language: str = None):
        self.device = device
        self.language = language
        self.logger = logger
        self._init_model(model_name)

    def _init_model(self, model_name: str) -> None:
        """
        Initialize the Whisper model and processor.
        """
        self.logger.info("Initializing model and processor ...")
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.processor = WhisperProcessor.from_pretrained(model_name)

    def transcribe_chunk(
        self,
        chunk: AudioSegment,
        start_time: float,
        end_time: float,
        speaker: str,
        frame_rate: int,
    ) -> Dict[str, Any]:
        """
        Transcribe a chunk of audio.
        """
        samples = np.array(chunk.set_frame_rate(frame_rate).set_channels(1).get_array_of_samples())
        waveform_chunk = torch.from_numpy(samples).float() / (2 ** 15)
        input_features = self.processor.feature_extractor(
            waveform_chunk.numpy(), sampling_rate=frame_rate, return_tensors="pt"
        ).input_features.to(self.device)
        with torch.inference_mode():
            generated_ids = self.model.generate(input_features, language=self.language, task="transcribe")
            transcription = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            return {"start": start_time, "end": end_time, "text": transcription, "speaker": speaker}

    def transcribe_chunks_batch(self, chunks: List[AudioSegment], metadata: List[Dict], frame_rate: int) -> List[Dict[str, Any]]:
      """
      Transcribe multiple chunks in a batch.
      """
      batch_samples = []
      for chunk in chunks:
          samples = np.array(chunk.set_frame_rate(frame_rate).set_channels(1).get_array_of_samples())
          waveform_chunk = torch.from_numpy(samples).float() / (2 ** 15)
          batch_samples.append(waveform_chunk.numpy())
      
      # Use the processor's feature extractor to handle variable-length inputs
      inputs = self.processor.feature_extractor(
          batch_samples, sampling_rate=frame_rate, return_tensors="pt", padding=True
      )
      input_features = inputs.input_features.to(self.device)
      attention_mask = inputs.attention_mask.to(self.device) if 'attention_mask' in inputs else None

      with torch.inference_mode():
          generated_ids = self.model.generate(
              input_features,
              attention_mask=attention_mask,
              language=self.language,
              task="transcribe"
          )
          transcriptions = [
              self.processor.decode(ids, skip_special_tokens=True) 
              for ids in generated_ids
          ]

      return [
          {"start": meta["start"], "end": meta["end"], "text": text, "speaker": meta["speaker"]}
          for text, meta in zip(transcriptions, metadata)
      ]
