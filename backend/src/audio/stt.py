import os
import time
from typing import Optional, Dict, List, Any, Generator


from tqdm import tqdm
from pydub import AudioSegment
import torch
import torch.nn.functional as F
import numpy as np
import wave
import threading

from src.audio.preprocess import read_audio, load_audio_segment, read_audio_from_numpy
from src.audio.diarization import DiarizationProcessor
from src.audio.transcription import TranscriptionProcessor
from src.audio.utils import merge_segments, format_transcription_output
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
        self.progress_callback = None

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
        transcribed_segments = []
        current_batch = {
            "chunks": [],
            "metadata": [],
            "last_end": 0
        }
        
        for turn, _, speaker in tqdm(diarization_segments):
            start_ms = int(turn.start * 1000)
            end_ms = int(turn.end * 1000)
            
            # Skip if this segment overlaps significantly with previous
            if start_ms/1000 < current_batch["last_end"]:
                continue
            
            # Process current batch if speaker changes
            if current_batch["chunks"] and current_batch["metadata"][-1]["speaker"] != speaker:
                batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                    current_batch["chunks"], 
                    current_batch["metadata"], 
                    frame_rate
                )
                transcribed_segments.extend(batch_transcriptions)
                current_batch = {"chunks": [], "metadata": [], "last_end": current_batch["last_end"]}
            
            # Add segment to current batch
            chunk = audio[start_ms:end_ms]
            current_batch["chunks"].append(chunk)
            current_batch["metadata"].append({
                "start": start_ms / 1000,
                "end": end_ms / 1000,
                "speaker": speaker,
            })
            current_batch["last_end"] = end_ms/1000
            
            # Process batch if it's full
            if len(current_batch["chunks"]) >= self.batch_size:
                batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                    current_batch["chunks"], 
                    current_batch["metadata"], 
                    frame_rate
                )
                transcribed_segments.extend(batch_transcriptions)
                current_batch = {"chunks": [], "metadata": [], "last_end": current_batch["last_end"]}
        
        # Process any remaining chunks
        if current_batch["chunks"]:
            batch_transcriptions = self.transcription_processor.transcribe_chunks_batch(
                current_batch["chunks"], 
                current_batch["metadata"], 
                frame_rate
            )
            transcribed_segments.extend(batch_transcriptions)
        
        return transcribed_segments

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
                    transcribed_segments = self._process_diarization_segments(
                        segments,
                        audio_segment,
                        self.recorder.sample_rate,
                        max_chunk_length=5000,  # 5 seconds
                        min_chunk_length=500    # 0.5 seconds
                    )
                    
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

if __name__ == "__main__":
    try:
        # Initialize SpeechToText
        stt = SpeechToText(
            language="english",
            num_speakers=2
        )
        
        print("Starting live transcription... Press Ctrl+C to stop")
        print("=" * 50)
        
        # Process live audio with transcription and save debug recordings
        for result in stt.transcribe_live(chunk_duration_ms=2000, save_debug=True):
            speaker = f"Speaker {result['speaker']}"
            text = result['text'].strip()
            if text:
                print(f"\n[{speaker}]: {text}")
                
    except KeyboardInterrupt:
        print("\nStopping transcription...")
    except Exception as e:
        print(f"Error: {str(e)}")

    