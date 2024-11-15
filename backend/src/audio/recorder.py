import queue
import time
import wave
from typing import Optional, Mapping

import numpy as np
import pyaudio

from src.configuration.log import get_logger


class AudioRecorder:
  def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024, channels: int = 1):
    self.logger = get_logger()
    self.sample_rate = sample_rate
    self.chunk_size = chunk_size
    self.channels = channels
    self.audio = pyaudio.PyAudio()
    self.stream: Optional[pyaudio.Stream] = None
    self.is_recording = False
    self.audio_queue: queue.Queue = queue.Queue()

    # Find input device
    self.input_device = self._find_input_device()
    if self.input_device is None:
      raise RuntimeError("No suitable input device found")

  def _find_input_device(self) -> Optional[Mapping[str, str | int | float]]:
    """Find the first available input device."""
    self.logger.info("Searching for input devices...")

    # List all audio devices
    info = self.audio.get_host_api_info_by_index(0)
    num_devices = info.get("deviceCount")

    if isinstance(num_devices, int):
      for i in range(num_devices):
        device_info = self.audio.get_device_info_by_index(i)
        self.logger.info(f"Found device: {device_info['name']}")

        max_channels = device_info.get("maxInputChannels")
        if isinstance(max_channels, int) and max_channels > 0:
          self.logger.info(f"Selected input device: {device_info['name']}")
          return device_info

    return None

  def start_recording(self) -> None:
    """Start recording audio in a separate thread."""
    if not self.input_device:
      raise RuntimeError("No input device available")

    self.logger.info(f"Starting recording with device: {self.input_device['name']}")
    self.is_recording = True

    try:
      self.stream = self.audio.open(
        format=pyaudio.paInt16,
        channels=self.channels,
        rate=self.sample_rate,
        input=True,
        input_device_index=int(self.input_device["index"]),
        frames_per_buffer=self.chunk_size,
        stream_callback=self._audio_callback,
      )
      self.stream.start_stream()
      self.logger.info("Audio stream started successfully")
    except Exception as e:
      self.logger.error(f"Failed to start audio stream: {str(e)}")
      raise

  def _audio_callback(self, in_data, frame_count, time_info, status):
    """Callback function for audio stream."""
    if self.is_recording:
      audio_data = np.frombuffer(in_data, dtype=np.int16)
      self.audio_queue.put(audio_data)
    return (in_data, pyaudio.paContinue)

  def get_audio_chunk(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
    """Get the next chunk of audio data."""
    try:
      return self.audio_queue.get(timeout=timeout)
    except queue.Empty:
      return None

  def stop_recording(self) -> None:
    """Stop recording audio."""
    self.is_recording = False
    if self.stream:
      self.stream.stop_stream()
      self.stream.close()
    self.audio.terminate()
    self.logger.info("Stopped recording audio")

  def list_devices(self):
    """List all available audio devices."""
    self.logger.info("Available audio devices:")
    info = self.audio.get_host_api_info_by_index(0)
    num_devices = info.get("deviceCount")

    for i in range(num_devices):
      device_info = self.audio.get_device_info_by_index(i)
      device_name = device_info.get("name")
      max_inputs = device_info.get("maxInputChannels")
      max_outputs = device_info.get("maxOutputChannels")
      self.logger.info(f"Device {i}: {device_name}")
      self.logger.info(f"  Max inputs: {max_inputs}, Max outputs: {max_outputs}")


if __name__ == "__main__":
  # Create and configure the recorder
  recorder = AudioRecorder()

  # Create a wave file
  wave_file = wave.open("test_recording.wav", "wb")
  wave_file.setnchannels(1)  # Mono
  wave_file.setsampwidth(2)  # Changed from 4 to 2 bytes for int16
  wave_file.setframerate(16000)  # Sample rate

  print("Starting recording... Press Ctrl+C to stop")
  recorder.start_recording()

  try:
    while True:
      chunk = recorder.get_audio_chunk(timeout=0.1)
      if chunk is not None:
        # Normalize the float32 data to [-1, 1] range and convert to int16
        normalized = np.clip(chunk, -1.0, 1.0)
        audio_int16 = (normalized * 32767).astype(np.int16)
        wave_file.writeframes(audio_int16.tobytes())
      time.sleep(0.001)

  except KeyboardInterrupt:
    print("\nStopping recording...")
    recorder.stop_recording()
    wave_file.close()
    print("Recording saved to test_recording.wav")
