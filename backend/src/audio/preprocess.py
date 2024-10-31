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
