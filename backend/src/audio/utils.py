import time
from typing import Any, Dict, List

from src.configuration.log import get_logger

logger = get_logger()


def merge_segments(segments: List[Dict[str, Any]], max_gap: float = 2.0) -> List[Dict[str, Any]]:
  """
  Merge segments from the same speaker that are close together.
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


def format_transcription_output(merged_segments: List[Dict[str, Any]]) -> str:
  """
  Format the transcription output text.
  """
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
  logger.info("Speaker mapping:")
  for original, mapped in speaker_map.items():
    logger.info(f"{original} -> {mapped}")

  return text_output


def time_to_str(seconds: float) -> str:
  """
  Convert time in seconds to a formatted string.
  """
  return time.strftime("%H:%M:%S", time.gmtime(seconds))
