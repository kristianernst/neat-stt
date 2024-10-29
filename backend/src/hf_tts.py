import os
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from pydub import AudioSegment
from tqdm import tqdm
import time
import logging
from typing import Optional, Dict, List, Tuple
from pyannote.audio import Pipeline
import torchaudio
from dotenv import load_dotenv
import numpy as np
import asyncio

load_dotenv()

logging.basicConfig(level=logging.INFO)


class HuggingFaceSTT:
  """
  HuggingFace Speech to Text Class with Speaker Diarization

  This class provides functionality for transcribing audio files using the Whisper model
  and performing speaker diarization using the pyannote/speaker-diarization model.

  Attributes:
      logger (logging.Logger): Logger for the class.
      device (str): The device to run the models on (cuda, mps, or cpu).
      verbose (bool): Whether to print verbose output.
      model (WhisperForConditionalGeneration): The Whisper model for transcription.
      processor (WhisperProcessor): The Whisper processor for feature extraction and decoding.
      diarization_model (Pipeline): The pyannote speaker diarization model.
      input_file (str): Path to the input audio file.
      language (str): The language of the audio for transcription.
      batch_size (int): Batch size for processing.
      num_speakers (Optional[int]): Number of speakers in the audio (if known).
      progress_callback (Optional[Callable]): Callback function for progress reporting.
  """

  def __init__(
    self,
    model: Optional[str] = "openai/whisper-large-v3",
    language: str = "english",
    device: Optional[str] = "infer",
    input_file: Optional[str] = None,
    batch_size: int = 1,
    num_speakers: Optional[int] = None,
    verbose: bool = False,
  ):
    """
    Initialize the HuggingFaceSTT class.

    Args:
        model (Optional[str]): The Whisper model to use for transcription.
        language (str): The language of the audio for transcription.
        device (Optional[str]): The device to run the models on (cuda, mps, cpu, or infer).
        input_file (Optional[str]): Path to the input audio file.
        batch_size (int): Batch size for processing.
        num_speakers (Optional[int]): Number of speakers in the audio (if known).
        verbose (bool): Whether to print verbose output.
    """
    super().__init__()
    self.logger = logging.getLogger(self.__class__.__name__)
    self.device = (
      ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu") if device == "infer" else device
    )
    self.logger.info(f"Using device: {self.device}")
    self.verbose = verbose
    self._init_model(model)
    self._init_diarization_model()
    self.input_file = input_file
    self.language = language
    self.batch_size = batch_size
    if num_speakers == 1:
      num_speakers = None
    self.num_speakers = num_speakers
    self.progress_callback = None

  def _init_model(self, model: str) -> None:
    """
    Initialize the Whisper model and processor.

    Args:
        model (str): The name or path of the Whisper model to use.
    """
    self.logger.info("Initializing model and processor ...")
    self.model = WhisperForConditionalGeneration.from_pretrained(model).to(self.device)

    # self.model.generation_config.cache_implementation = "static"
    # self.model.generation_config.max_new_tokens = 256
    # self.model.forward = torch.compile(self.model.forward, mode="reduce-overhead", fullgraph=True)

    self.processor = WhisperProcessor.from_pretrained(model)

  def _init_diarization_model(self) -> None:
    """
    Initialize the speaker diarization model.
    """
    self.logger.info("Initializing diarization model ...")
    self.diarization_model = Pipeline.from_pretrained(
      os.getenv("DIARIZATION_MODEL"),
      use_auth_token=os.getenv("HF_TOKEN"),
    ).to(torch.device(self.device))

  def read_audio(self, input_file: str) -> Tuple[torch.Tensor, int]:
    """
    Read an audio file and return the waveform and sample rate.

    Args:
        input_file (str): Path to the input audio file.

    Returns:
        Tuple[torch.Tensor, int]: A tuple containing the waveform and sample rate.
    """
    self.logger.info("Reading audio file ...")
    try:
      # First, try using torchaudio
      waveform, sample_rate = torchaudio.load(input_file)
    except:
      # If torchaudio fails, use pydub
      audio = AudioSegment.from_file(input_file)
      sample_rate = audio.frame_rate
      waveform = torch.tensor(audio.get_array_of_samples()).float()

      # Convert to mono if stereo
      if audio.channels == 2:
        waveform = waveform.mean(dim=0, keepdim=True)
      else:
        waveform = waveform.unsqueeze(0)

      # Normalize
      waveform /= torch.abs(waveform).max()

    return waveform, sample_rate

  def perform_diarization(self, waveform: torch.Tensor, sample_rate: int) -> Pipeline:
    """
    Perform speaker diarization on the audio.

    Args:
        waveform (torch.Tensor): The audio waveform.
        sample_rate (int): The sample rate of the audio.

    Returns:
        Pipeline: The diarization result.
    """
    self.logger.info("Performing speaker diarization ...")
    diarization = self.diarization_model(
      {"waveform": waveform, "sample_rate": sample_rate},
      num_speakers=self.num_speakers,
    )
    return diarization

  def merge_transcription_and_diarization(self, segments: List[Dict[str, float]], diarization: Pipeline) -> List[Dict[str, str]]:
    """
    Merge transcription segments with diarization annotations and group them.

    Args:
        segments (List[Dict[str, float]]): List of transcription segments.
        diarization (Pipeline): The diarization result.

    Returns:
        List[Dict[str, str]]: A list of merged and grouped segments with speaker information.
    """
    self.logger.info("Merging transcription with diarization ...")
    diarization_list = list(diarization.itertracks(yield_label=True))
    unique_speakers = {label for _, _, label in diarization_list}
    n_speakers = len(unique_speakers)
    self.logger.info(f"Detected {n_speakers} speakers.")

    # Align transcription segments with diarization turns
    aligned_segments = []
    for segment in segments:
      segment_start = segment["start"]
      segment_end = segment["end"]
      segment_text = segment["text"]
      segment_speaker = "Unknown"

      # Find the speaker who was speaking during this segment
      for turn, _, speaker in diarization_list:
        turn_start = turn.start
        turn_end = turn.end
        # Check if there's an overlap
        if segment_end > turn_start and segment_start < turn_end:
          segment_speaker = speaker
          break  # Assuming one speaker per segment

      aligned_segments.append({"start": segment_start, "end": segment_end, "speaker": segment_speaker, "text": segment_text})

    # Group consecutive segments with the same speaker
    if not aligned_segments:
      return []

    grouped_segments = [aligned_segments[0]]
    for segment in aligned_segments[1:]:
      last_segment = grouped_segments[-1]
      # If the speaker is the same and the time gap is small, merge the segments
      time_gap = segment["start"] - last_segment["end"]
      if segment["speaker"] == last_segment["speaker"] and time_gap <= 2.0:  # 2 seconds gap
        last_segment["end"] = segment["end"]
        last_segment["text"] += " " + segment["text"]
      else:
        grouped_segments.append(segment)

    return grouped_segments

  async def report_progress(self, stage: str, progress: float, message: str):
    if self.progress_callback:
      await self.progress_callback(stage, progress, message)

  async def transcribe(self, input_file: Optional[str] = None, frame_rate: int = 16000) -> str:
    """
    Transcribe an audio file and perform speaker diarization.
    """

    def merge_segments(segments, max_gap: float = 2.0) -> List[Dict]:
      """
      Merge segments from the same speaker that are close together.

      Args:
          segments: List of transcribed segments
          max_gap: Maximum gap in seconds between segments to merge
      """
      if not segments:
        return []

      merged = []
      current = segments[0].copy()

      for next_segment in segments[1:]:
        # If same speaker and gap is small enough
        if next_segment["speaker"] == current["speaker"] and next_segment["start"] - current["end"] <= max_gap:
          # Merge segments
          current["end"] = next_segment["end"]
          current["text"] = current["text"].strip() + " " + next_segment["text"].strip()
        else:
          # Add current segment to merged list and start new segment
          merged.append(current)
          current = next_segment.copy()

      # Add final segment
      merged.append(current)
      return merged

    def transcribe_chunk(chunk, start_time, end_time, speaker):
      samples = chunk.set_frame_rate(frame_rate).set_channels(1).get_array_of_samples()
      waveform_chunk = torch.tensor(samples).float() / 2**15
      input_features = self.processor.feature_extractor(
        waveform_chunk.numpy(), sampling_rate=frame_rate, return_tensors="pt"
      ).input_features.to(self.device)

      with torch.no_grad():
        generated_ids = self.model.generate(input_features, language=self.language, task="transcribe")
        transcription = self.processor.decode(generated_ids[0], skip_special_tokens=True)
        return {"start": start_time, "end": end_time, "text": transcription, "speaker": speaker}

    self.logger.info("Transcribing audio file ...")
    start_time = time.time()
    if input_file is None:
      input_file = self.input_file

    # Constants for chunk size control
    MAX_CHUNK_LENGTH = int(os.getenv("MAX_CHUNK_LENGTH", 15000))  # 15 seconds in ms
    MIN_CHUNK_LENGTH = int(os.getenv("MIN_CHUNK_LENGTH", 1000))  # 1 second in ms

    # Read audio for both transcription and diarization
    waveform, sample_rate = self.read_audio(input_file)
    audio = AudioSegment.from_file(input_file)

    # Perform speaker diarization first
    diarization = self.perform_diarization(waveform, sample_rate)
    diarization_segments = list(diarization.itertracks(yield_label=True))

    # Process audio based on speaker turns
    transcribed_segments = []
    current_segment = None

    for turn, _, speaker in tqdm(diarization_segments):
      start_ms = int(turn.start * 1000)
      end_ms = int(turn.end * 1000)
      duration = end_ms - start_ms

      # Handle segments shorter than MIN_CHUNK_LENGTH
      if duration < MIN_CHUNK_LENGTH:
        if current_segment and current_segment["speaker"] == speaker:
          # Merge with previous segment
          current_segment["end_ms"] = end_ms
          current_segment["duration"] += duration
        elif current_segment:
          # Process previous segment if it exists
          if current_segment["duration"] >= MIN_CHUNK_LENGTH:
            chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
            segment = transcribe_chunk(
              chunk, current_segment["start_ms"] / 1000, current_segment["end_ms"] / 1000, current_segment["speaker"]
            )
            transcribed_segments.append(segment)
          # Start new segment
          current_segment = {"start_ms": start_ms, "end_ms": end_ms, "duration": duration, "speaker": speaker}
        else:
          # Start first segment
          current_segment = {"start_ms": start_ms, "end_ms": end_ms, "duration": duration, "speaker": speaker}
        continue

      # Handle segments longer than MAX_CHUNK_LENGTH
      if duration > MAX_CHUNK_LENGTH:
        # Process any pending current_segment
        if current_segment:
          chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
          segment = transcribe_chunk(
            chunk, current_segment["start_ms"] / 1000, current_segment["end_ms"] / 1000, current_segment["speaker"]
          )
          transcribed_segments.append(segment)
          current_segment = None

        # Split long segment into chunks
        for chunk_start in range(start_ms, end_ms, MAX_CHUNK_LENGTH):
          chunk_end = min(chunk_start + MAX_CHUNK_LENGTH, end_ms)
          chunk = audio[chunk_start:chunk_end]
          segment = transcribe_chunk(chunk, chunk_start / 1000, chunk_end / 1000, speaker)
          transcribed_segments.append(segment)
      else:
        # Normal length segment
        if current_segment:
          # Process previous segment
          chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
          segment = transcribe_chunk(
            chunk, current_segment["start_ms"] / 1000, current_segment["end_ms"] / 1000, current_segment["speaker"]
          )
          transcribed_segments.append(segment)

        # Process current segment
        chunk = audio[start_ms:end_ms]
        segment = transcribe_chunk(chunk, start_ms / 1000, end_ms / 1000, speaker)
        transcribed_segments.append(segment)
        current_segment = None

    # Process any remaining segment
    if current_segment and current_segment["duration"] >= MIN_CHUNK_LENGTH:
      chunk = audio[current_segment["start_ms"] : current_segment["end_ms"]]
      segment = transcribe_chunk(chunk, current_segment["start_ms"] / 1000, current_segment["end_ms"] / 1000, current_segment["speaker"])
      transcribed_segments.append(segment)

    # Sort segments by start time
    transcribed_segments.sort(key=lambda x: x["start"])

    # Merge nearby segments from same speaker
    merged_segments = merge_segments(transcribed_segments)

    # Clean up speaker labels and format output
    speaker_map = {}
    current_speaker_num = 1

    text_output = ""
    for segment in merged_segments:
      # Map speaker labels to simple numbers if not already mapped
      speaker_label = segment["speaker"]
      if speaker_label not in speaker_map:
        speaker_map[speaker_label] = f"Speaker {current_speaker_num}"
        current_speaker_num += 1

      speaker = speaker_map[speaker_label]
      start_time_str = time.strftime("%H:%M:%S", time.gmtime(segment["start"]))
      end_time_str = time.strftime("%H:%M:%S", time.gmtime(segment["end"]))

      # Clean up the text
      text = segment["text"].strip()
      text = " ".join(text.split())  # Remove extra whitespace

      # Format the output
      text_output += f"[{start_time_str} -> {end_time_str}] {speaker}:\n{text}\n\n"

    # Log speaker mapping for reference
    self.logger.info("Speaker mapping:")
    for original, mapped in speaker_map.items():
      self.logger.info(f"{original} -> {mapped}")

    end_time = time.time()
    self.logger.info("Finished transcribing audio file.")
    self.logger.info(f"Elapsed time: {end_time - start_time:.2f} seconds, in minutes: {(end_time - start_time) / 60:.2f}")

    return text_output

  def transcribe_folder(self, folder_path: str, frame_rate: int = 16000, save_transcriptions: bool = False) -> Dict[str, str]:
    """
    Transcribe all audio files in a folder.

    Args:
        folder_path (str): Path to the folder containing audio files.
        frame_rate (int): The frame rate to use for audio processing.
        save_transcriptions (bool): Whether to save transcriptions to text files.

    Returns:
        Dict[str, str]: A dictionary mapping file names to their transcriptions.
    """
    transcriptions = {}
    transcriptions_folder = os.path.join(folder_path, "transcriptions")
    if save_transcriptions and not os.path.exists(transcriptions_folder):
      os.makedirs(transcriptions_folder)

    audio_extensions = (".wav", ".mp3", ".flac", ".ogg", ".m4a")

    for item in os.listdir(folder_path):
      full_path = os.path.join(folder_path, item)

      if os.path.isfile(full_path) and item.lower().endswith(audio_extensions):
        try:
          text = self.transcribe(input_file=full_path, frame_rate=frame_rate)
          transcriptions[item] = text
          if save_transcriptions:
            with open(os.path.join(transcriptions_folder, f"{item}.txt"), "w") as f:
              f.write(text)
        except Exception as e:
          self.logger.error(f"Error processing {item}: {str(e)}")
      else:
        self.logger.info(f"Skipping non-audio file: {item}")

    return transcriptions

  def set_progress_callback(self, callback):
    self.progress_callback = callback


if __name__ == "__main__":
  gena = HuggingFaceSTT(
    model=os.getenv("MODEL_ID"),
    language="danish",
    device="infer",
    num_speakers=2,  # Specify the number of speakers if known
  )
  current_dir = os.getcwd()
  asset_dir = os.path.join(current_dir, "assets")

  gena.transcribe_folder(folder_path=asset_dir, save_transcriptions=True)
