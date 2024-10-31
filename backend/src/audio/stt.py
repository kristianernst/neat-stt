import os
import time
from typing import Optional, Dict, List, Any


from tqdm import tqdm
from pydub import AudioSegment
import torch

from src.audio.preprocess import read_audio, load_audio_segment
from src.audio.diarization import DiarizationProcessor
from src.audio.transcription import TranscriptionProcessor
from src.audio.utils import merge_segments, format_transcription_output
from src.configuration.environment import (
    MODEL_ID,
    MAX_CHUNK_LENGTH_MS,
    MIN_CHUNK_LENGTH_MS,
)
from src.configuration.log import get_logger

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
        self.progress_callback = None

        # Initialize processors
        self.diarization_processor = DiarizationProcessor(self.device, self.num_speakers)
        self.transcription_processor = TranscriptionProcessor(self.model, self.device, self.language)

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

    def transcribe(self, input_file: Optional[str] = None, frame_rate: int = 16000) -> str:
        """
        Transcribe an audio file and perform speaker diarization.
        """
        self.logger.info("Transcribing audio file ...")
        start_time = time.time()
        if input_file is None:
            input_file = self.input_file

        # Constants for chunk size control
        max_chunk_length = int(MAX_CHUNK_LENGTH_MS)  # in milliseconds
        min_chunk_length = int(MIN_CHUNK_LENGTH_MS)  # in milliseconds

        # Read audio for both transcription and diarization
        waveform, sample_rate = read_audio(input_file, self.device)
        audio = load_audio_segment(input_file)

        # Perform speaker diarization first
        diarization = self.diarization_processor.perform_diarization(waveform, sample_rate)
        diarization_segments = self.diarization_processor.process_diarization_segments(diarization)

        # Process audio based on speaker turns
        transcribed_segments = self._process_diarization_segments(
            diarization_segments, audio, frame_rate, max_chunk_length, min_chunk_length
        )

        # Sort segments by start time
        transcribed_segments.sort(key=lambda x: x["start"])

        # Merge nearby segments from same speaker
        merged_segments = merge_segments(transcribed_segments)

        # Format the transcription output
        text_output = format_transcription_output(merged_segments)

        end_time = time.time()
        self.logger.info("Finished transcribing audio file.")
        self.logger.info(
            f"Elapsed time: {end_time - start_time:.2f} seconds, in minutes: {(end_time - start_time) / 60:.2f}"
        )

        return text_output

    def _process_diarization_segments(
        self,
        diarization_segments: List[Any],
        audio: AudioSegment,
        frame_rate: int,
        max_chunk_length: int,
        min_chunk_length: int,
    ) -> List[Dict[str, Any]]:
        """
        Process diarization segments and transcribe the audio accordingly using batching.
        """
        transcribed_segments = []
        current_segment = None
        batch_chunks = []
        batch_metadata = []

        for turn, _, speaker in tqdm(diarization_segments):
            start_ms = int(turn.start * 1000)
            end_ms = int(turn.end * 1000)
            duration = end_ms - start_ms

            # Handle segments shorter than MIN_CHUNK_LENGTH
            if duration < min_chunk_length:
                if current_segment and current_segment["speaker"] == speaker:
                    # Merge with previous segment
                    current_segment["end_ms"] = end_ms
                    current_segment["duration"] += duration
                elif current_segment:
                    # Process previous segment if it exists
                    if current_segment["duration"] >= min_chunk_length:
                        chunk = audio[current_segment["start_ms"]:current_segment["end_ms"]]
                        batch_chunks.append(chunk)
                        batch_metadata.append({
                            "start": current_segment["start_ms"] / 1000,
                            "end": current_segment["end_ms"] / 1000,
                            "speaker": current_segment["speaker"],
                        })
                        # Check if batch is full
                        if len(batch_chunks) >= self.batch_size:
                            # Process batch
                            batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                                batch_chunks, batch_metadata, frame_rate
                            )
                            transcribed_segments.extend(batch_transcriptions)
                            # Reset batch lists
                            batch_chunks = []
                            batch_metadata = []
                    # Start new segment
                    current_segment = {
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "duration": duration,
                        "speaker": speaker,
                    }
                else:
                    # Start first segment
                    current_segment = {
                        "start_ms": start_ms,
                        "end_ms": end_ms,
                        "duration": duration,
                        "speaker": speaker,
                    }
                continue

            # Handle segments longer than MAX_CHUNK_LENGTH
            if duration > max_chunk_length:
                # Process any pending current_segment
                if current_segment:
                    chunk = audio[current_segment["start_ms"]:current_segment["end_ms"]]
                    batch_chunks.append(chunk)
                    batch_metadata.append({
                        "start": current_segment["start_ms"] / 1000,
                        "end": current_segment["end_ms"] / 1000,
                        "speaker": current_segment["speaker"],
                    })
                    # Check if batch is full
                    if len(batch_chunks) >= self.batch_size:
                        # Process batch
                        batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                            batch_chunks, batch_metadata, frame_rate
                        )
                        transcribed_segments.extend(batch_transcriptions)
                        # Reset batch lists
                        batch_chunks = []
                        batch_metadata = []
                    current_segment = None

                # Split long segment into chunks
                for chunk_start in range(start_ms, end_ms, max_chunk_length):
                    chunk_end = min(chunk_start + max_chunk_length, end_ms)
                    chunk = audio[chunk_start:chunk_end]
                    batch_chunks.append(chunk)
                    batch_metadata.append({
                        "start": chunk_start / 1000,
                        "end": chunk_end / 1000,
                        "speaker": speaker,
                    })
                    # Check if batch is full
                    if len(batch_chunks) >= self.batch_size:
                        # Process batch
                        batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                            batch_chunks, batch_metadata, frame_rate
                        )
                        transcribed_segments.extend(batch_transcriptions)
                        # Reset batch lists
                        batch_chunks = []
                        batch_metadata = []
            else:
                # Normal length segment
                if current_segment:
                    # Process previous segment
                    chunk = audio[current_segment["start_ms"]:current_segment["end_ms"]]
                    batch_chunks.append(chunk)
                    batch_metadata.append({
                        "start": current_segment["start_ms"] / 1000,
                        "end": current_segment["end_ms"] / 1000,
                        "speaker": current_segment["speaker"],
                    })
                    # Check if batch is full
                    if len(batch_chunks) >= self.batch_size:
                        # Process batch
                        batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                            batch_chunks, batch_metadata, frame_rate
                        )
                        transcribed_segments.extend(batch_transcriptions)
                        # Reset batch lists
                        batch_chunks = []
                        batch_metadata = []

                # Process current segment
                chunk = audio[start_ms:end_ms]
                batch_chunks.append(chunk)
                batch_metadata.append({
                    "start": start_ms / 1000,
                    "end": end_ms / 1000,
                    "speaker": speaker,
                })
                # Check if batch is full
                if len(batch_chunks) >= self.batch_size:
                    # Process batch
                    batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                        batch_chunks, batch_metadata, frame_rate
                    )
                    transcribed_segments.extend(batch_transcriptions)
                    # Reset batch lists
                    batch_chunks = []
                    batch_metadata = []
                current_segment = None

        # Process any remaining current_segment
        if current_segment and current_segment["duration"] >= min_chunk_length:
            chunk = audio[current_segment["start_ms"]:current_segment["end_ms"]]
            batch_chunks.append(chunk)
            batch_metadata.append({
                "start": current_segment["start_ms"] / 1000,
                "end": current_segment["end_ms"] / 1000,
                "speaker": current_segment["speaker"],
            })

        # Process any remaining chunks in the batch
        if batch_chunks:
            batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                batch_chunks, batch_metadata, frame_rate
            )
            transcribed_segments.extend(batch_transcriptions)

        return transcribed_segments
    
    # def _process_diarization_segments(
    #     self,
    #     diarization_segments: List[Any],
    #     audio: AudioSegment,
    #     frame_rate: int,
    #     max_chunk_length: int,
    #     min_chunk_length: int,
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Process diarization segments and transcribe the audio accordingly.
    #     """
    #     transcribed_segments = []
    #     current_segment = None

    #     for turn, _, speaker in tqdm(diarization_segments):
    #         start_ms = int(turn.start * 1000)
    #         end_ms = int(turn.end * 1000)
    #         duration = end_ms - start_ms

    #         # Handle segments shorter than MIN_CHUNK_LENGTH
    #         if duration < min_chunk_length:
    #             if current_segment and current_segment["speaker"] == speaker:
    #                 # Merge with previous segment
    #                 current_segment["end_ms"] = end_ms
    #                 current_segment["duration"] += duration
    #             elif current_segment:
    #                 # Process previous segment if it exists
    #                 if current_segment["duration"] >= min_chunk_length:
    #                     chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
    #                     segment = self.transcription_processor.transcribe_chunk(
    #                         chunk,
    #                         current_segment["start_ms"] / 1000,
    #                         current_segment["end_ms"] / 1000,
    #                         current_segment["speaker"],
    #                         frame_rate,
    #                     )
    #                     transcribed_segments.append(segment)
    #                 # Start new segment
    #                 current_segment = {
    #                     "start_ms": start_ms,
    #                     "end_ms": end_ms,
    #                     "duration": duration,
    #                     "speaker": speaker,
    #                 }
    #             else:
    #                 # Start first segment
    #                 current_segment = {
    #                     "start_ms": start_ms,
    #                     "end_ms": end_ms,
    #                     "duration": duration,
    #                     "speaker": speaker,
    #                 }
    #             continue

    #         # Handle segments longer than MAX_CHUNK_LENGTH
    #         if duration > max_chunk_length:
    #             # Process any pending current_segment
    #             if current_segment:
    #                 chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
    #                 segment = self.transcription_processor.transcribe_chunk(
    #                     chunk,
    #                     current_segment["start_ms"] / 1000,
    #                     current_segment["end_ms"] / 1000,
    #                     current_segment["speaker"],
    #                     frame_rate,
    #                 )
    #                 transcribed_segments.append(segment)
    #                 current_segment = None

    #             # Split long segment into chunks
    #             for chunk_start in range(start_ms, end_ms, max_chunk_length):
    #                 chunk_end = min(chunk_start + max_chunk_length, end_ms)
    #                 chunk = audio[chunk_start:chunk_end]
    #                 segment = self.transcription_processor.transcribe_chunk(
    #                     chunk, chunk_start / 1000, chunk_end / 1000, speaker, frame_rate
    #                 )
    #                 transcribed_segments.append(segment)
    #         else:
    #             # Normal length segment
    #             if current_segment:
    #                 # Process previous segment
    #                 chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
    #                 segment = self.transcription_processor.transcribe_chunk(
    #                     chunk,
    #                     current_segment["start_ms"] / 1000,
    #                     current_segment["end_ms"] / 1000,
    #                     current_segment["speaker"],
    #                     frame_rate,
    #                 )
    #                 transcribed_segments.append(segment)

    #             # Process current segment
    #             chunk = audio[start_ms:end_ms]
    #             segment = self.transcription_processor.transcribe_chunk(
    #                 chunk, start_ms / 1000, end_ms / 1000, speaker, frame_rate
    #             )
    #             transcribed_segments.append(segment)
    #             current_segment = None

    #     # Process any remaining segment
    #     if current_segment and current_segment["duration"] >= min_chunk_length:
    #         chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
    #         segment = self.transcription_processor.transcribe_chunk(
    #             chunk,
    #             current_segment["start_ms"] / 1000,
    #             current_segment["end_ms"] / 1000,
    #             current_segment["speaker"],
    #             frame_rate,
    #         )
    #         transcribed_segments.append(segment)

    #     return transcribed_segments

    # # The rest of your methods (e.g., transcribe_folder) can be updated similarly.
