import os
import time
from typing import Optional, Dict, List, Any, Generator


from tqdm import tqdm
from pydub import AudioSegment
import torch
import torch.nn.functional as F
import numpy as np
import wave

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
        batch_size: int = 16,
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

    def transcribe_live(self, chunk_duration_ms: int = 5000, save_debug: bool = True) -> Generator[Dict[str, Any], None, None]:
        """
        Perform live transcription with speaker diarization.
        
        Args:
            chunk_duration_ms: Duration of each audio chunk to process in milliseconds
            save_debug: If True, saves debug recordings
        
        Yields:
            Dict containing transcription results with speaker information
        """
        self.logger.info("Starting live transcription...")
        
        # Create debug directory if needed
        if save_debug:
            debug_dir = "debug_recordings"
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            raw_file = wave.open(f"{debug_dir}/raw_recording_{timestamp}.wav", 'wb')
            raw_file.setnchannels(1)
            raw_file.setsampwidth(2)  # For int16
            raw_file.setframerate(16000)
            
            processed_file = wave.open(f"{debug_dir}/processed_recording_{timestamp}.wav", 'wb')
            processed_file.setnchannels(1)
            processed_file.setsampwidth(2)
            processed_file.setframerate(16000)
        
        # Initialize audio recorder with matching sample rate
        recorder = AudioRecorder(sample_rate=16000)
        recorder.start_recording()
        
        try:
            buffer = []
            buffer_duration_ms = 0
            
            while True:
                # Get audio chunk
                chunk = recorder.get_audio_chunk(timeout=0.1)
                if chunk is None:
                    continue
                
                # Save raw audio if debugging (keep as int16)
                if save_debug:
                    raw_file.writeframes(chunk.tobytes())
                
                # Add to buffer (keep as int16)
                buffer.append(chunk)
                buffer_duration_ms += (len(chunk) * 1000) / recorder.sample_rate
                
                # Process buffer when it reaches desired duration
                if buffer_duration_ms >= chunk_duration_ms:
                    # Combine buffer chunks
                    audio_data = np.concatenate(buffer)
                    
                    # Save processed chunk if debugging
                    if save_debug:
                        processed_file.writeframes(audio_data.tobytes())
                    
                    # Convert to torch tensor with proper shape (channel, time)
                    waveform = torch.from_numpy(audio_data).float() / 32768.0
                    waveform = waveform.unsqueeze(0)  # Add channel dimension
                    
                    # Perform diarization
                    diarization = self.diarization_processor.perform_diarization(
                        waveform, recorder.sample_rate
                    )
                    segments = self.diarization_processor.process_diarization_segments(diarization)
                    
                    # Create AudioSegment for transcription
                    audio_segment = AudioSegment(
                        audio_data.tobytes(),
                        frame_rate=recorder.sample_rate,
                        sample_width=2,  # int16
                        channels=1
                    )
                    
                    # Process each diarization segment
                    for segment, _, speaker in segments:
                        start_ms = int(segment.start * 1000)
                        end_ms = int(segment.end * 1000)
                        
                        # Extract segment from audio
                        segment_audio = audio_segment[start_ms:end_ms]
                        
                        # Transcribe segment
                        result = self.transcription_processor.transcribe_chunk(
                            start_time=segment.start,
                            end_time=segment.end,
                            speaker=speaker,
                            waveform=segment_audio,
                            sample_rate=recorder.sample_rate
                        )
                        yield result
                    
                    # Keep a small overlap for context
                    overlap_ms = 500
                    if buffer_duration_ms > overlap_ms:
                        samples_to_keep = int((overlap_ms * recorder.sample_rate) / 1000)
                        buffer = [buffer[-1][-samples_to_keep:]]
                        buffer_duration_ms = overlap_ms
                    else:
                        buffer = []
                        buffer_duration_ms = 0
                    
        except KeyboardInterrupt:
            self.logger.info("Stopping live transcription...")
        finally:
            recorder.stop_recording()
            if save_debug:
                raw_file.close()
                processed_file.close()

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
        for result in stt.transcribe_live(chunk_duration_ms=5000, save_debug=True):
            speaker = f"Speaker {result['speaker']}"
            text = result['text'].strip()
            if text:
                print(f"\n[{speaker}]: {text}")
                
    except KeyboardInterrupt:
        print("\nStopping transcription...")
    except Exception as e:
        print(f"Error: {str(e)}")

    