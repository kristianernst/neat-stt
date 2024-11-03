import time
from typing import Optional, Dict, List, Any, Generator

from tqdm import tqdm
from pydub import AudioSegment
import torch
import torch.nn.functional as F
import numpy as np
import threading

from src.audio.preprocess import read_audio, load_audio_segment
from src.audio.diarization import DiarizationProcessor
from src.audio.transcription import TranscriptionProcessor
from src.audio.utils import merge_segments
from src.configuration.environment import (
    MODEL_ID,
    MAX_CHUNK_LENGTH_MS,
    MIN_CHUNK_LENGTH_MS,
)
from src.configuration.log import get_logger
from src.audio.recorder import AudioRecorder

class SpeechToText:
    """
    HuggingFace Speech to Text Class with Speaker Diarization.
    """

    def __init__(
        self,
        model: Optional[str] = MODEL_ID,
        language: Optional[str] = None,
        device: Optional[str] = "infer",
        input_file: Optional[str] = None,
        batch_size: int = 32,
        num_speakers: Optional[int] = None,
        verbose: bool = False,
    ):
        self.logger = get_logger()
        self.device = self._infer_device() if device == "infer" else device
        self.logger.info(f"Using device: {self.device}")
        self.verbose = verbose
        self.input_file = input_file
        self.language = language
        self.batch_size = batch_size
        self.num_speakers = None if num_speakers == 1 else num_speakers
        self.model = model

        # Initialize processors
        self.diarization_processor = DiarizationProcessor(self.device, self.num_speakers)
        self.transcription_processor = TranscriptionProcessor(self.model, self.device, self.language)

        # Add a flag to control the transcription loop
        self.is_running = False

    def _infer_device(self) -> str:
        """
        Infer the device to use based on availability.
        """
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _update_settings(self, language: str, num_speakers: int):
        self.language = language
        self.num_speakers = num_speakers
        self.diarization_processor = DiarizationProcessor(self.device, self.num_speakers)
        self.transcription_processor = TranscriptionProcessor(self.model, self.device, self.language)

    def transcribe(self, input_file: Optional[str] = None, frame_rate: int = 16000) -> Generator[Dict[str, Any], None, None]:
        """
        Transcribe an audio file and perform speaker diarization,
        yielding transcription results as they are processed.
        """
        self.logger.info("Transcribing audio file ...")
        start_time = time.time()
        if input_file is None:
            input_file = self.input_file

        # Constants for chunk size control
        max_chunk_length = int(MAX_CHUNK_LENGTH_MS)
        min_chunk_length = int(MIN_CHUNK_LENGTH_MS)

        try:
            # Read audio for both transcription and diarization
            waveform, sample_rate = read_audio(input_file, self.device)
            audio = load_audio_segment(input_file)
            total_duration = len(audio) / 1000.0  # Duration in seconds

            # Yield initial progress
            yield {"type": "progress", "progress": 10}

            # Perform speaker diarization
            diarization = self.diarization_processor.perform_diarization(waveform, sample_rate)
            diarization_segments = self.diarization_processor.process_diarization_segments(diarization)
            
            # Yield diarization progress
            yield {"type": "progress", "progress": 30}

            # Process segments and yield results
            yield from self._process_segments(
                diarization_segments,
                audio,
                frame_rate,
                max_chunk_length,
                min_chunk_length,
                total_duration
            )

            # Final progress update
            yield {"type": "progress", "progress": 100}

            end_time = time.time()
            self.logger.info(f"Transcription completed in {end_time - start_time:.2f} seconds")

        except Exception as e:
            self.logger.error(f"Transcription error: {str(e)}")
            yield {"type": "error", "error": str(e)}

    # Existing live transcription methods remain unchanged
    def transcribe_live(self, chunk_duration_ms: int = 2000, save_debug: bool = False):
        """Live transcription with efficient batch processing"""
        self.logger.info("Starting live transcription...")
        self.recorder = AudioRecorder(sample_rate=16000, chunk_size=chunk_duration_ms, channels=1)
        self.recorder.start_recording()
        self.is_running = True
        
        try:
            buffer = []
            buffer_duration_ms = 0
            total_processed_duration = 0
            
            while self.is_running:
                chunk = self.recorder.get_audio_chunk(timeout=0.1)
                if chunk is None:
                    continue
                
                buffer.append(chunk)
                buffer_duration_ms += (len(chunk) * 1000) / self.recorder.sample_rate
                
                if buffer_duration_ms >= chunk_duration_ms:
                    # Process the buffer
                    audio_data = np.concatenate(buffer)
                    waveform = torch.from_numpy(audio_data).float() / 32768.0
                    waveform = waveform.unsqueeze(0)
                    
                    # Get speaker segments
                    diarization = self.diarization_processor.perform_diarization(
                        waveform, self.recorder.sample_rate
                    )
                    segments = self.diarization_processor.process_diarization_segments(diarization)
                    
                    # Create AudioSegment
                    audio_segment = AudioSegment(
                        audio_data.tobytes(),
                        frame_rate=self.recorder.sample_rate,
                        sample_width=2,
                        channels=1
                    )
                    
                    # Process segments efficiently using batching
                    transcribed_segments = self._process_live_transcription(segments, audio_segment, self.recorder.sample_rate)
                    
                    # Stream results
                    for segment in transcribed_segments:
                        yield {
                            "start": total_processed_duration + segment["start"],
                            "end": total_processed_duration + segment["end"],
                            "text": segment["text"],
                            "speaker": segment["speaker"]
                        }
                    
                    total_processed_duration += buffer_duration_ms / 1000
                    buffer = []
                    buffer_duration_ms = 0
                    
        finally:
            if hasattr(self, 'recorder'):
                self.recorder.stop_recording()
                self.recorder = None

    def _process_live_transcription(self, segments, audio_segment, frame_rate):
        """
        Process segments during live transcription.
        """
        # Since this is synchronous, we can't await; process segments directly
        transcribed_segments = []
        current_batch = {
            "chunks": [],
            "metadata": [],
        }

        for turn, _, speaker in segments:
            start_ms = int(turn.start * 1000)
            end_ms = int(turn.end * 1000)
            
            chunk = audio_segment[start_ms:end_ms]
            current_batch["chunks"].append(chunk)
            current_batch["metadata"].append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker,
            })

        if current_batch["chunks"]:
            batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                current_batch["chunks"],
                current_batch["metadata"],
                frame_rate
            )
            transcribed_segments.extend(batch_transcriptions)

        return transcribed_segments

    def stop_live_transcription(self):
        """
        Stop the live transcription by setting the flag and stopping the recorder.
        """
        self.logger.info("Stopping live transcription...")
        self.is_running = False
        
        # Stop the recorder immediately in a separate thread to prevent blocking
        def stop_recorder():
            if hasattr(self, 'recorder') and self.recorder:
                self.recorder.stop_recording()
                self.recorder = None
        
        threading.Thread(target=stop_recorder).start()

    def _process_segments(
        self,
        diarization_segments: List[Any],
        audio: AudioSegment,
        frame_rate: int,
        max_chunk_length: int,
        min_chunk_length: int,
        total_duration: float
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process diarization segments and transcribe the audio accordingly using batching.
        Yields progress and transcription results.
        """
        current_batch = []
        last_speaker = None
        last_end = 0
        progress = 30

        for turn, _, speaker in tqdm(diarization_segments, desc="Processing segments"):
            start_ms = int(turn.start * 1000)
            end_ms = int(turn.end * 1000)
            duration = end_ms - start_ms

            # Skip if segment overlaps significantly with previous
            if turn.start < last_end:
                continue

            # Handle segments based on duration
            if duration < min_chunk_length:
                # Try to merge with previous segment if same speaker
                if current_batch and last_speaker == speaker:
                    prev = current_batch[-1]
                    prev["end_ms"] = end_ms
                    continue

            if duration > max_chunk_length:
                # Split long segments
                for chunk_start in range(start_ms, end_ms, max_chunk_length):
                    chunk_end = min(chunk_start + max_chunk_length, end_ms)
                    current_batch.append({
                        "start_ms": chunk_start,
                        "end_ms": chunk_end,
                        "speaker": speaker
                    })
            else:
                current_batch.append({
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "speaker": speaker
                })

            # Process batch if full
            if len(current_batch) >= self.batch_size:
                chunks = [audio[seg["start_ms"]:seg["end_ms"]] for seg in current_batch]
                metadata = [{
                    "start": seg["start_ms"] / 1000,
                    "end": seg["end_ms"] / 1000,
                    "speaker": seg["speaker"]
                } for seg in current_batch]
                
                transcribed_segments = self.transcription_processor.transcribe_chunks_batch(
                    chunks, metadata, frame_rate
                )
                merged_segments = merge_segments(transcribed_segments)
                
                for segment in merged_segments:
                    yield {"type": "transcription", "data": segment}
                
                # Update progress
                progress = min(30 + (last_end / total_duration * 70), 100)
                yield {"type": "progress", "progress": progress}
                
                current_batch = []

            last_speaker = speaker
            last_end = turn.end

        # Process remaining segments
        if current_batch:
            chunks = [audio[seg["start_ms"]:seg["end_ms"]] for seg in current_batch]
            metadata = [{
                "start": seg["start_ms"] / 1000,
                "end": seg["end_ms"] / 1000,
                "speaker": seg["speaker"]
            } for seg in current_batch]
            
            transcribed_segments = self.transcription_processor.transcribe_chunks_batch(
                chunks, metadata, frame_rate
            )
            merged_segments = merge_segments(transcribed_segments)
            
            for segment in merged_segments:
                yield {"type": "transcription", "data": segment}
