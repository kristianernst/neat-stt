import os
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = os.getenv("MODEL_ID")
HF_TOKEN = os.getenv("HF_TOKEN")
DIARIZATION_MODEL = os.getenv("DIARIZATION_MODEL")
MAX_CHUNK_LENGTH_MS = int(os.getenv("MAX_CHUNK_LENGTH"))
MIN_CHUNK_LENGTH_MS = int(os.getenv("MIN_CHUNK_LENGTH"))
LOG_LEVEL = os.getenv("LOG_LEVEL")
APPLICATION_NAME = os.getenv("APPLICATION_NAME")

assert MODEL_ID, "MODEL_ID is not set"
if not HF_TOKEN:
  raise ValueError("HF_TOKEN is not set")
assert DIARIZATION_MODEL, "DIARIZATION_MODEL is not set"
assert MAX_CHUNK_LENGTH_MS, "MAX_CHUNK_LENGTH is not set"
assert MIN_CHUNK_LENGTH_MS, "MIN_CHUNK_LENGTH is not set"
assert LOG_LEVEL, "LOG_LEVEL is not set"
assert APPLICATION_NAME, "APPLICATION_NAME is not set"
