import torch
from typing import Tuple
import torchaudio
from torchaudio import functional as F
import noisereduce as nr
import numpy as np
from pydub import AudioSegment

from src.configuration.log import get_logger

logger = get_logger()


def read_audio(input_file: str, device: str) -> Tuple[torch.Tensor, int]:
    """
    Read an audio file and return the waveform and sample rate.
    """
    logger.info("Reading audio file ...")
    try:
        # Try using torchaudio
        waveform, sample_rate = torchaudio.load(input_file)
        # Normalize
        waveform /= torch.abs(waveform).max()
    except Exception as e:
        logger.warning(f"torchaudio.load failed: {e}, falling back to pydub")
        # If torchaudio fails, use pydub
        audio = AudioSegment.from_file(input_file)
        sample_rate = audio.frame_rate

        # Get samples and reshape for multi-channel audio
        samples = np.array(audio.get_array_of_samples())
        if audio.channels > 1:
            samples = samples.reshape((-1, audio.channels)).T  # Shape: [channels, samples]
        else:
            samples = samples.reshape((1, -1))

        waveform = torch.from_numpy(samples).float()
        # Normalize
        waveform /= torch.abs(waveform).max()

    return waveform, sample_rate

def load_audio_segment(input_file: str) -> AudioSegment:
    """
    Load an audio file using pydub.
    """
    logger.info("Loading audio segment ...")
    return AudioSegment.from_file(input_file)

def read_audio_from_numpy(audio_data: np.ndarray, sample_rate: int) -> Tuple[torch.Tensor, int]:
    """
    Convert numpy array audio data to torch tensor format expected by STT.
    
    Args:
        audio_data: Audio data as numpy array
        sample_rate: Sample rate of the audio
        
    Returns:
        Tuple containing:
        - Waveform as torch tensor
        - Sample rate (possibly resampled to 16000)
    """
    logger.info("Converting numpy audio data to torch tensor...")
    
    # Convert to torch tensor
    waveform = torch.from_numpy(audio_data).float()
    if len(waveform.shape) == 1:
        waveform = waveform.unsqueeze(0)
    
    # Ensure proper sample rate
    if sample_rate != 16000:
        logger.info(f"Resampling audio from {sample_rate}Hz to 16000Hz")
        waveform = F.resample(waveform, sample_rate, 16000)
        sample_rate = 16000
    
    # Normalize
    waveform /= torch.abs(waveform).max()
    
    return waveform, sample_rate
