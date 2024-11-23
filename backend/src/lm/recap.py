import os
from typing import List

from src.lm.helpers import TextChunker, LLMClient
from src.configuration.environment import LARGE_LLM_MODEL, SMALL_LLM_MODEL, LARGE_LLM_ENDPOINT, SMALL_LLM_ENDPOINT, O1_LLM_ENDPOINT, O1_LLM_MODEL
from src.configuration.log import get_logger
from src.lm.prompts import MEETING_SCRATCHPAD_INST, LECTURE_SCRATCHPAD_INST, MEETING_RECAP_INST, LECTURE_RECAP_INST, MEETING_O1_INST, LECTURE_O1_INST
from src.lm.classifier import TranscriptClassifier


class RecapGenerator:
  def __init__(
    self,
    max_tokens: int = 4000,
    max_chunk_length: int = 1000,
    chunk_strategy: str = "semantic",
    max_context_length: int = 4096,
    buffer: int = 500,
  ):
    self.logger = get_logger()
    self.logger.debug(f"Parameters: max_tokens={max_tokens}, max_context_length={max_context_length}, buffer={buffer}")
    self.max_tokens = max_tokens
    self.max_context_length = max_context_length
    self.buffer = buffer
    self.chunker = TextChunker(max_chunk_length=max_chunk_length, strategy=chunk_strategy)
    self.small_llm_client = LLMClient(model_name=SMALL_LLM_MODEL, base_url=SMALL_LLM_ENDPOINT)
    self.large_llm_client = LLMClient(model_name=LARGE_LLM_MODEL, base_url=LARGE_LLM_ENDPOINT)
    self.o1_llm_client = LLMClient(model_name=O1_LLM_MODEL, base_url=O1_LLM_ENDPOINT)
    self.classifier = TranscriptClassifier(self.small_llm_client)

  def generate_recap(self, transcript: str) -> str:
    self.logger.info("Starting summarization process")
    # First, classify the transcript
    transcript_type = self.classifier.classify(transcript)
    
    if not transcript_type:
        self.logger.warning("Classification failed, defaulting to meeting type")
        transcript_type = "meeting"
    else:
      self.logger.info(f"\n\n{'='*10}\nTranscript classified as {transcript_type}\n{'='*10}\n\n")
      self.recap_inst = LECTURE_RECAP_INST if transcript_type == "lecture" else MEETING_RECAP_INST
      self.scratchpad_inst = LECTURE_SCRATCHPAD_INST if transcript_type == "lecture" else MEETING_SCRATCHPAD_INST
      self.reflection_inst = LECTURE_O1_INST if transcript_type == "lecture" else MEETING_O1_INST

    try:
        scratch_pad = self._generate_scratchpad(transcript)
        combined_scratchpad = "\n\n".join(scratch_pad)
        reduced_scratchpad = self._reduce_scratchpad(combined_scratchpad) # will only reduce if length > max_context_length
        reflection = self._generate_reflection(reduced_scratchpad)
        return self._recap(reduced_scratchpad, reflection)
    except Exception as e:
        self.logger.error(f"Summarization failed: {str(e)}", exc_info=True)
        raise

  def _generate_scratchpad(self, transcript: str) -> List[str]:
    chunks = self.chunker.chunk_text(transcript)
    num_chunks = len(chunks)
    self.logger.info(f"Generating scratchpad for {num_chunks} chunks")
    
    scratch_pad = []

    for i, chunk in enumerate(chunks, 1):
      self.logger.debug(f"Processing chunk {i}/{num_chunks} of length {len(chunk)}")
      try:
        conversation = [
          {"role": "system", "content": self.scratchpad_inst},
          {"role": "user", "content": f"Do not hallucinate, only reference the text chunk. Sometimes the transcribed words are not accurate try and infer the actual words. Chunk {i} of {num_chunks}:\n{chunk}"},
        ]
        res = self.o1_llm_client.ask(
          messages=conversation,
          temperature=0.1,
          max_tokens=self.max_tokens,
          stream=True,
        )
        scratch_pad.append(res)
        self.logger.debug(f"Successfully processed chunk {i}, response length: {len(res)}")
      except Exception as e:
        self.logger.error(f"Failed to process chunk {i}: {str(e)}", exc_info=True)
        raise

    return scratch_pad

  def _reduce_scratchpad(self, text: str, max_iterations: int = 3) -> str:
    iteration = 0
    while iteration < max_iterations:
      text_length = len(text)
      self.logger.debug(f"Recursive summarization iteration {iteration + 1}, text length: {text_length}")

      if text_length <= self.max_context_length - self.buffer:
        self.logger.debug("Text length within acceptable limits, stopping recursive summarization")
        break

      self.logger.info(f"Text too long ({text_length} chars), performing iteration {iteration + 1}")
      try:
        scratchpad_chunks = self.chunker.chunk_text(text)
        summarized_chunks = []

        for i, chunk in enumerate(scratchpad_chunks, 1):
          self.logger.debug(f"Processing recursive chunk {i}/{len(scratchpad_chunks)}")
          conversation = [
            {
              "role": "system",
              "content": "Please provide a concise summary of the following notes, focusing on the most important points. retain the key information and list it as bullet points.",
            },
            {"role": "user", "content": chunk},
          ]
          res = self.small_llm_client.ask(
            messages=conversation,
            temperature=0.1,
            max_tokens=self.max_tokens,
            stream=True,
          )
          summarized_chunks.append(res)

        text = "\n\n".join(summarized_chunks)
        iteration += 1
      except Exception as e:
        self.logger.error(f"Failed during recursive summarization iteration {iteration + 1}: {str(e)}", exc_info=True)
        raise

    if iteration >= max_iterations:
      self.logger.warning(f"Reached maximum iterations ({max_iterations}) in recursive summarization")

    return text
  
  def _generate_reflection(self, scratchpad: str) -> str:
    self.logger.debug("Generating reflection from summarized scratchpad")
    try:
      msgs = [
        {"role": "system", "content": self.reflection_inst},
        {"role": "user", "content": f"Here are the notes:\n{scratchpad}"},
      ] 
      reflection = self.o1_llm_client.ask(
        messages=msgs,
        temperature=0.0,
        max_tokens=self.max_tokens,
        stream=True,
      )
      return reflection
    except Exception as e:
      self.logger.error("Failed to generate reflection: " + str(e), exc_info=True)
      raise e

  def _recap(self, scratchpad: str, reflection: str) -> str:
    self.logger.debug("Generating reflection from summarized scratchpad")
    try:
      msgs = [
        {"role": "system", "content": self.recap_inst},
        {"role": "user", "content": f"Here are the notes:\n{scratchpad}"},
        {"role": "user", "content": f"Here is the reflection o1 has made:\n{reflection}"},
      ]
      recap = self.o1_llm_client.ask(
        messages=msgs,
        temperature=0.0,
        max_tokens=self.max_tokens,
        stream=True,
      )
      self.logger.debug(f"Generated recap of length: {len(recap)}")
      return recap
    except Exception as e:
      self.logger.error("Failed to generate reflection: " + str(e), exc_info=True)
      raise

if __name__ == "__main__":
  import time
  
  logger = get_logger()
  src_path = "src"
  lm_path = "lm"
  test_foldername = "tests"
  
  test_path = os.path.join(src_path, lm_path, test_foldername)
  in_path = "in"
  filename = "raw.txt"
  
  file_path = os.path.join(test_path, in_path, filename)
  out_name = filename.split(".")[0] + "_summary.md"
  out_file_path = os.path.join(test_path, "out", out_name)

  start_time = time.time()
  logger.info(f"Starting summarization at {start_time}")
  with open(file_path, "r", encoding="utf-8") as file:
    transcript = file.read()

  recap_generator = RecapGenerator(max_tokens=10_000, max_chunk_length=1800, chunk_strategy="semantic")
  res = recap_generator.generate_recap(transcript=transcript)
  end_time = time.time()
  logger.info(f"Summarization completed at {end_time}, took {end_time - start_time} seconds")

  with open(out_file_path, "w", encoding="utf-8") as file:
    file.write(res)
