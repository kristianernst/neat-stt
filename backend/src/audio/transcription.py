from functools import lru_cache
from typing import Dict, Any, List, Generator, Tuple
import traceback

import numpy as np
import torch
from pydub import AudioSegment
from transformers import WhisperForConditionalGeneration, WhisperProcessor




from src.configuration.log import get_logger

logger = get_logger()

class TranscriptionError(Exception):
    """Custom exception for transcription-related errors"""
    pass

class TranscriptionProcessor:
    def __init__(self, model_name: str, device: str, language: str = None):
        try:
            self.device = device
            self.language = language
            self.logger = logger
            self._init_model(model_name)
            self.model.eval()
            try:
                self.logger.info("Compiling model with aot_eager backend")
                self.model = torch.compile(self.model, backend="aot_eager")
            except Exception as e:
                self.logger.warning("Failed to compile model with aot_eager backend, falling back to aot")
        except Exception as e:
            self.logger.error(f"Failed to initialize TranscriptionProcessor: {str(e)}")
            raise TranscriptionError(f"Initialization failed: {str(e)}") from e

    def _init_model(self, model_name: str) -> None:
        try:
            self.logger.info(f"Initializing Whisper model '{model_name}' on device '{self.device}'")
            self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
            self.processor = WhisperProcessor.from_pretrained(model_name)
            self.logger.info("Model and processor successfully initialized")
        except Exception as e:
            self.logger.error(f"Model initialization failed: {str(e)}\n{traceback.format_exc()}")
            raise TranscriptionError(f"Model initialization failed: {str(e)}") from e

    def transcribe_chunk(self, chunk: AudioSegment, start_time: float, end_time: float, 
                        speaker: str, frame_rate: int) -> Dict[str, Any]:
        try:
            self.logger.debug(f"Processing chunk: start={start_time:.2f}s, end={end_time:.2f}s, speaker={speaker}")
            
            # Preprocess audio
            self.logger.debug(f"Converting audio chunk to samples (frame_rate={frame_rate})")
            samples = np.array(chunk.set_frame_rate(frame_rate).set_channels(1).get_array_of_samples())
            waveform_chunk = torch.from_numpy(samples).float() / (2 ** 15)
            
            # Extract features
            self.logger.debug("Extracting features from audio chunk")
            input_features = self.processor.feature_extractor(
                waveform_chunk.numpy(), sampling_rate=frame_rate, return_tensors="pt"
            ).input_features.to(self.device)
            
            # Generate transcription
            self.logger.debug("Generating transcription")
            with torch.inference_mode():
                generated_ids = self.model.generate(input_features, language=self.language, task="transcribe")
                transcription = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            self.logger.info(f"Successfully transcribed chunk: {start_time:.2f}s - {end_time:.2f}s")
            return {"start": start_time, "end": end_time, "text": transcription, "speaker": speaker}
            
        except Exception as e:
            self.logger.error(f"Failed to transcribe chunk: {str(e)}\n{traceback.format_exc()}")
            raise TranscriptionError(f"Chunk transcription failed: {str(e)}") from e

    def transcribe_chunks_batch(self, chunks: List[AudioSegment], metadata: List[Dict], 
                              frame_rate: int) -> List[Dict[str, Any]]:
        try:
            self.logger.info(f"Processing batch of {len(chunks)} chunks")
            if not chunks or not metadata:
                raise ValueError("Empty chunks or metadata provided")
            if len(chunks) != len(metadata):
                raise ValueError(f"Mismatch between chunks ({len(chunks)}) and metadata ({len(metadata)})")

            # Preprocess batch
            self.logger.debug("Converting audio chunks to samples")
            batch_samples = []
            for i, chunk in enumerate(chunks):
                try:
                    samples = np.array(chunk.set_frame_rate(frame_rate).set_channels(1).get_array_of_samples(), dtype=np.float32)
                    samples = samples / (2 ** 15)  # Normalize
                    batch_samples.append(samples)
                except Exception as e:
                    self.logger.error(f"Failed to process chunk {i}: {str(e)}")
                    raise

            # Extract features
            self.logger.debug("Extracting features from batch")
            inputs = self.processor.feature_extractor(
                batch_samples, sampling_rate=frame_rate, return_tensors="pt", padding=True
            )
            input_features = inputs.input_features.to(self.device)
            attention_mask = inputs.attention_mask.to(self.device) if 'attention_mask' in inputs else None

            # Generate transcriptions
            self.logger.debug("Generating batch transcriptions")
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

            self.logger.info(f"Successfully transcribed batch of {len(chunks)} chunks")
            return [
                {"start": meta["start"], "end": meta["end"], "text": text, "speaker": meta["speaker"]}
                for text, meta in zip(transcriptions, metadata)
            ]

        except Exception as e:
            self.logger.error(f"Failed to transcribe batch: {str(e)}\n{traceback.format_exc()}")
            raise TranscriptionError(f"Batch transcription failed: {str(e)}") from e

    def transcribe_chunk_streaming(self, chunk: AudioSegment, start_time: float, 
                                end_time: float, speaker: str, frame_rate: int) -> Generator[Dict[str, Any], None, None]:
        """
        Stream transcription results word by word.
        """
        try:
            # Use the existing transcribe_chunk method
            result = self.transcribe_chunk(chunk, start_time, end_time, speaker, frame_rate)
            
            # Split the transcription into words if needed
            words = result["text"].split()
            if not words:
                return
                
            # Calculate timing for each word
            word_duration = (end_time - start_time) / len(words)
            
            for i, word in enumerate(words):
                word_start = start_time + (i * word_duration)
                word_end = word_start + word_duration
                logger.info(f"\n\n\nWord: {word}, start={word_start:.2f}s, end={word_end:.2f}s\n\n\n")
                
                yield {
                    "start": word_start,
                    "end": word_end,
                    "text": word,
                    "speaker": speaker
                }

        except Exception as e:
            self.logger.error(f"Failed to transcribe streaming chunk: {str(e)}")
            raise TranscriptionError(f"Streaming chunk transcription failed: {str(e)}") from e