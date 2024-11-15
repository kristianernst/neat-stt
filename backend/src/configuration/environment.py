import os
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = os.getenv("MODEL_ID")
HF_TOKEN = os.getenv("HF_TOKEN")
DIARIZATION_MODEL = os.getenv("DIARIZATION_MODEL")
LOG_LEVEL = os.getenv("LOG_LEVEL")
APPLICATION_NAME = os.getenv("APPLICATION_NAME")


max_chunk = os.getenv("MAX_CHUNK_LENGTH")
min_chunk = os.getenv("MIN_CHUNK_LENGTH")
MAX_CHUNK_LENGTH_MS: int = int(max_chunk) if max_chunk else 0
MIN_CHUNK_LENGTH_MS: int = int(min_chunk) if min_chunk else 0

if MAX_CHUNK_LENGTH_MS == 0 or MIN_CHUNK_LENGTH_MS == 0:
  raise ValueError("MAX_CHUNK_LENGTH and MIN_CHUNK_LENGTH must be greater than 0, did you remember to set the environment variables?")

assert MODEL_ID, "MODEL_ID is not set"
assert HF_TOKEN, "HF_TOKEN is not set"
assert DIARIZATION_MODEL, "DIARIZATION_MODEL is not set"
assert LOG_LEVEL, "LOG_LEVEL is not set"
assert APPLICATION_NAME, "APPLICATION_NAME is not set"
