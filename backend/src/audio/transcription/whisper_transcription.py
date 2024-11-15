from typing import Any, Dict, List, Optional

import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from pydub import AudioSegment

from src.configuration.model_config import ModelConfig
from src.audio.transcription.base_transcription import BaseTranscriptionProcessor


class WhisperTranscriptionProcessor(BaseTranscriptionProcessor):
  def _init_model(self, model_config: ModelConfig) -> None:
    try:
      self.logger.info(f"Initializing Whisper model '{model_config.name}' on device '{self.device}'")
      self.model = WhisperForConditionalGeneration.from_pretrained(model_config.name).to(self.device)
      self.processor = WhisperProcessor.from_pretrained(model_config.name)

      try:
        self.model = torch.compile(self.model, backend="aot_eager")
      except Exception:
        self.logger.warning("Failed to compile model with aot_eager backend")

      self.logger.info("Model and processor successfully initialized")
    except Exception as e:
      self.logger.error(f"Model initialization failed: {str(e)}")
      raise

  def transcribe_chunk(self, chunk: AudioSegment, start_time: float, end_time: float, speaker: str, frame_rate: int) -> Dict[str, Any]:
    waveform_chunk = self._preprocess_audio(chunk, frame_rate)

    input_features = self.processor.feature_extractor(
      waveform_chunk.numpy(), sampling_rate=frame_rate, return_tensors="pt"
    ).input_features.to(self.device)

    with torch.inference_mode():
      generated_ids = self.model.generate(input_features, language=self.language, task="transcribe")
      transcription = self.processor.decode(generated_ids[0], skip_special_tokens=True)

    return {"start": start_time, "end": end_time, "text": transcription, "speaker": speaker}

  def transcribe_chunks_batch(self, chunks: List[AudioSegment], metadata: List[Dict], frame_rate: int) -> List[Dict[str, Any]]:
    batch_samples = []
    for chunk in chunks:
      waveform = self._preprocess_audio(chunk, frame_rate)
      batch_samples.append(waveform.numpy())

    inputs = self.processor.feature_extractor(batch_samples, sampling_rate=frame_rate, return_tensors="pt", padding=True)
    input_features = inputs.input_features.to(self.device)
    attention_mask = inputs.attention_mask.to(self.device) if "attention_mask" in inputs else None

    with torch.inference_mode():
      generated_ids = self.model.generate(input_features, attention_mask=attention_mask, language=self.language, task="transcribe")
      transcriptions = [self.processor.decode(ids, skip_special_tokens=True) for ids in generated_ids]

    return [
      {"start": meta["start"], "end": meta["end"], "text": text, "speaker": meta["speaker"]} for text, meta in zip(transcriptions, metadata)
    ]
