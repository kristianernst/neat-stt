from typing import Any, Dict, List, Optional

import torch
from transformers import Wav2Vec2ForCTC, AutoProcessor
from pydub import AudioSegment

from src.configuration.model_config import ModelConfig
from src.audio.transcription.base_transcription import BaseTranscriptionProcessor


def convert_language(language: str) -> str:
  """takes language and returns the language code used by MMS"""
  if language == "english":
    return "eng"
  elif language == "danish":
    return "dan"
  elif language == "german":
    return "deu"


class MmsTranscriptionProcessor(BaseTranscriptionProcessor):
  def _init_model(self, model_config: ModelConfig) -> None:
    try:
      self.logger.info(f"Initializing MMS model '{model_config.name}' on device '{self.device}'")
      self.model = Wav2Vec2ForCTC.from_pretrained(
        model_config.name,
        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
      ).to(self.device)
      self.processor = AutoProcessor.from_pretrained(model_config.name)

      # Set initial language
      if self.language:
        language_code = convert_language(self.language)
        self.logger.info(f"Setting language to {language_code}")
        self.processor.tokenizer.set_target_lang(language_code)
        self.model.load_adapter(language_code)

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

    inputs = self.processor(waveform_chunk.numpy(), sampling_rate=frame_rate, return_tensors="pt").to(self.device)

    with torch.inference_mode():
      outputs = self.model(**inputs).logits
      ids = torch.argmax(outputs, dim=-1)[0]
      transcription = self.processor.decode(ids)

    return {"start": start_time, "end": end_time, "text": transcription, "speaker": speaker}

  def transcribe_chunks_batch(self, chunks: List[AudioSegment], metadata: List[Dict], frame_rate: int) -> List[Dict[str, Any]]:
    batch_samples = []
    for chunk in chunks:
      waveform = self._preprocess_audio(chunk, frame_rate)
      batch_samples.append(waveform.numpy())

    inputs = self.processor(batch_samples, sampling_rate=frame_rate, return_tensors="pt", padding=True).to(self.device)

    with torch.inference_mode():
      outputs = self.model(**inputs).logits
      ids = torch.argmax(outputs, dim=-1)
      transcriptions = [self.processor.decode(sequence_ids) for sequence_ids in ids]

    return [
      {"start": meta["start"], "end": meta["end"], "text": text, "speaker": meta["speaker"]} for text, meta in zip(transcriptions, metadata)
    ]
