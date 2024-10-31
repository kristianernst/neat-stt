from pydub import AudioSegment
import torchaudio
import torch
import numpy as np

# read m4a file using pydub
audio = AudioSegment.from_file("test.m4a")

# Crop to 2 minutes (120000 milliseconds)
two_minutes = 120000
cropped_audio = audio[:two_minutes]

# Export the cropped audio using mp4 format
cropped_audio.export("test_2min.m4a", format="mp4", codec="aac")

