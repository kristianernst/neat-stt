import os
from dotenv import load_dotenv

load_dotenv()


APPLICATION_NAME = os.getenv("APPLICATION_NAME")
LOG_LEVEL = os.getenv("LOG_LEVEL")
HF_TOKEN = os.getenv("HF_TOKEN")

MODEL_ID = os.getenv("MODEL_ID")
DIARIZATION_MODEL = os.getenv("DIARIZATION_MODEL")
LARGE_LLM_ENDPOINT = os.getenv("LARGE_LLM_ENDPOINT")
SMALL_LLM_ENDPOINT = os.getenv("SMALL_LLM_ENDPOINT")
LARGE_LLM_MODEL = os.getenv("LARGE_LLM_MODEL")
SMALL_LLM_MODEL = os.getenv("SMALL_LLM_MODEL")
O1_LLM_ENDPOINT = os.getenv("O1_LLM_ENDPOINT")
O1_LLM_MODEL = os.getenv("O1_LLM_MODEL")

max_chunk = os.getenv("MAX_CHUNK_LENGTH")
min_chunk = os.getenv("MIN_CHUNK_LENGTH")
MAX_CHUNK_LENGTH_MS: int = int(max_chunk) if max_chunk else 0
MIN_CHUNK_LENGTH_MS: int = int(min_chunk) if min_chunk else 0
if MAX_CHUNK_LENGTH_MS == 0 or MIN_CHUNK_LENGTH_MS == 0:
  raise ValueError("MAX_CHUNK_LENGTH and MIN_CHUNK_LENGTH must be greater than 0, did you remember to set the environment variables?")

assert APPLICATION_NAME, "APPLICATION_NAME is not set"
assert LOG_LEVEL, "LOG_LEVEL is not set"
assert HF_TOKEN, "HF_TOKEN is not set"

assert MODEL_ID, "MODEL_ID is not set"
assert DIARIZATION_MODEL, "DIARIZATION_MODEL is not set"
assert LARGE_LLM_ENDPOINT, "LARGE_LLM_ENDPOINT is not set"
assert SMALL_LLM_ENDPOINT, "SMALL_LLM_ENDPOINT is not set"
assert LARGE_LLM_MODEL, "LARGE_LLM_MODEL is not set"
assert SMALL_LLM_MODEL, "SMALL_LLM_MODEL is not set"
assert O1_LLM_ENDPOINT, "O1_LLM_ENDPOINT is not set"
assert O1_LLM_MODEL, "O1_LLM_MODEL is not set"
