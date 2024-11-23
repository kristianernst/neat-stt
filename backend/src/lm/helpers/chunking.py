from typing import List, Literal
import re

__all__ = ["TextChunker"]

ChunkingStrategy = Literal["fixed", "fixed_overlap", "semantic"]

from src.configuration.log import get_logger

class TextChunker:
  def __init__(self, max_chunk_length: int = 4096, strategy: ChunkingStrategy = "semantic", overlap: int = 0) -> None:
    """
    Initializes the TextChunker with a maximum chunk length and chunking strategy.

    Parameters:
        max_chunk_length (int): The maximum length of each text chunk. Must be positive.
        strategy (ChunkingStrategy): The chunking strategy ('fixed', 'fixed_overlap', 'semantic').
        overlap (int): Number of characters to overlap between chunks (used in 'fixed_overlap' strategy).

    Raises:
        ValueError: If parameters are invalid.
    """
    self.logger = get_logger()
    self.logger.debug(f"Initializing TextChunker with max_length={max_chunk_length}, strategy={strategy}, overlap={overlap}")
    
    if not isinstance(max_chunk_length, int) or max_chunk_length <= 0:
      self.logger.error(f"Invalid max_chunk_length: {max_chunk_length}")
      raise ValueError("max_chunk_length must be a positive integer.")

    if strategy not in ["fixed", "fixed_overlap", "semantic"]:
      self.logger.error(f"Invalid strategy: {strategy}")
      raise ValueError("strategy must be 'fixed', 'fixed_overlap', or 'semantic'.")

    if not isinstance(overlap, int) or overlap < 0:
      self.logger.error(f"Invalid overlap: {overlap}")
      raise ValueError("overlap must be a non-negative integer.")

    self.max_chunk_length = max_chunk_length
    self.strategy = strategy
    self.overlap = overlap
    self.logger.info(f"TextChunker initialized successfully with strategy: {strategy}")

  def chunk_text(self, text: str) -> List[str]:
    """
    Splits text into chunks based on the selected strategy.

    Parameters:
        text (str): The text to be chunked.

    Returns:
        List[str]: A list of text chunks.

    Raises:
        TypeError: If text is not a string.
    """
    
    text = text.strip()
    text_length = len(text)
    self.logger.debug(f"Starting text chunking, input length: {text_length} chars")
    self.logger.debug(f"First 50 chars of input: {text[:50]}...")

    if text_length == 0:
      self.logger.warning("Empty input text provided")
      return []

    if text_length <= self.max_chunk_length:
      self.logger.debug("Text length smaller than max chunk length, returning single chunk")
      return [text]

    chunks = []
    if self.strategy == "fixed":
      chunks = self._fixed_chunking(text)
    elif self.strategy == "fixed_overlap":
      chunks = self._fixed_chunking_with_overlap(text)
    else:
      chunks = self._semantic_chunking(text)

    self.logger.info(f"Chunking completed, produced {len(chunks)} chunks")
    self.logger.debug(f"Average chunk length: {sum(len(c) for c in chunks)/len(chunks):.2f} chars")
    return chunks

  def _fixed_chunking(self, text: str) -> List[str]:
    """Splits text into fixed-length chunks without overlap."""
    self.logger.debug("Using fixed chunking strategy")
    chunks = [text[i : i + self.max_chunk_length] for i in range(0, len(text), self.max_chunk_length)]
    self.logger.debug(f"Created {len(chunks)} fixed chunks")
    return chunks

  def _fixed_chunking_with_overlap(self, text: str) -> List[str]:
    """Splits text into fixed-length chunks with overlap."""
    self.logger.debug(f"Using fixed chunking with overlap strategy (overlap: {self.overlap})")
    chunks = []
    step = self.max_chunk_length - self.overlap
    for i in range(0, len(text), step):
      chunk = text[i : i + self.max_chunk_length]
      chunks.append(chunk)
    self.logger.debug(f"Created {len(chunks)} overlapping chunks")
    return chunks

  def _semantic_chunking(self, text: str) -> List[str]:
    """
    Splits text into chunks based on semantic boundaries.
    """
    self.logger.debug("Starting semantic chunking")
    return self._split_text_recursive(text, self.max_chunk_length, level=0)

  def _split_text_recursive(self, text: str, max_length: int, level: int) -> List[str]:
    """
    Recursively splits text into chunks no longer than max_length,
    using the appropriate delimiter based on the recursion level.
    It first tries at paragraph level, then sentence level, then comma level, and finally word level.

    Parameters:
        text (str): The text to be split.
        max_length (int): The maximum allowed length of each chunk.
        level (int): The current recursion level, indicating which delimiter to use.

    Returns:
        List[str]: A list of text chunks.
    """
    self.logger.debug(f"Recursive split at level {level}, text length: {len(text)}")
    
    if len(text) <= max_length:
      self.logger.debug("Text fits in single chunk, returning")
      return [text]

    # Define delimiters for each level
    delimiters = [
      "\n\n",  # Level 0: Paragraphs
      r"(?<=[.!?])\s+",  # Level 1: Sentences
      ",",  # Level 2: Commas
      " ",  # Level 3: Spaces (words)
    ]

    if level >= len(delimiters):
      self.logger.warning("Maximum recursion level reached, falling back to fixed-size chunks")
      # Fallback: Split text into fixed-size chunks
      return [text[i : i + max_length] for i in range(0, len(text), max_length)]

    delimiter = delimiters[level]
    self.logger.debug(f"Using delimiter for level {level}: {delimiter}")

    if level == 1:
      # For sentence splitting, use regex
      parts = re.split(delimiter, text)
    else:
      parts = text.split(delimiter)

    self.logger.debug(f"Split text into {len(parts)} parts")

    chunks = []
    current_chunk = ""
    for i, part in enumerate(parts):
      if current_chunk:
        separator = delimiter if level != 1 else " "
        tentative_chunk = current_chunk + separator + part
      else:
        tentative_chunk = part

      if len(tentative_chunk) <= max_length:
        current_chunk = tentative_chunk
      else:
        if current_chunk:
          # If current_chunk is too long, split it further
          if len(current_chunk) > max_length:
            self.logger.debug(f"Current chunk exceeds max length, recursive splitting at level {level + 1}")
            chunks.extend(self._split_text_recursive(current_chunk.strip(), max_length, level + 1))
          else:
            chunks.append(current_chunk.strip())
        current_chunk = part
        # If last part and it's too long, split it
        if i == len(parts) - 1 and len(current_chunk) > max_length:
          chunks.extend(self._split_text_recursive(current_chunk.strip(), max_length, level + 1))
          current_chunk = ""
    if current_chunk:
      if len(current_chunk) > max_length:
        self.logger.debug("Processing final chunk recursively")
        chunks.extend(self._split_text_recursive(current_chunk.strip(), max_length, level + 1))
      else:
        chunks.append(current_chunk.strip())

    self.logger.debug(f"Level {level} produced {len(chunks)} chunks")
    return chunks


if __name__ == "__main__":
  test1 = """
  We’re excited to announce the release of Llama 3.1 70B Speculative Decoding (llama-3.1-70b-specdec) on GroqCloud, a >6x performance enhancement (vs Llama 3.1 70B on Groq)

  Our team achieved this performance jump from 250 T/s to 1660 T/s on our 14nm LPU architecture with software updates alone, and aren’t hitting a saturation point on our first generation silicon anytime soon. We’re excited for what this will mean for future performance potential as new models enter the AI ecosystem and as Groq matches that innovation with V2 hardware. This new version of Llama 3.1 70B Powered by Groq implements speculative decoding, a process that leverages a smaller and faster ‘draft model’ to generate tokens that are verified on the primary model. This innovative approach enables faster and more efficient processing, making it ideal for applications that require rapid and accurate language understanding.

  “Artificial Analysis has independently benchmarked Groq as serving Meta’s Llama 3.1 70B model at 1,665 output tokens per second on their new endpoint with speculative decoding. This is >6X faster than their current Llama 3.1 70B endpoint without speculative decoding and >20X faster than the median of other providers serving the model. Speculative decoding involves using a smaller and faster ‘draft model’ to generate tokens for the primary model to verify. Our independent quality evaluations of Groq’s speculative decoding endpoint confirm no quality degradation, validating Groq’s correct implementation of the optimization technique. Meta’s Llama 3.1 70B is the most commonly used open source AI model. This new endpoint will support developers in building for use-cases which benefit from fast inference including AI agents and applications which require real-time responses."

  George Cameron, Co-Founder, Artificial Analysis​
  Fast AI inference, like what Groq is providing for  llama-3.1-70B-specdec, is helping to unlock the full potential of GenAI.  Pushing the boundaries of speed is helping make AI models more useful to real-world applications, enabling developers to build more intelligent and capable applications, and increase the intelligence and capability of openly-available models. 
  The context window for llama-3.1-70b-specdec starts at 8k and will provide significant benefits for a wide range of applications, including but not limited to:

  Agentic workflows for content creation: With llama-3.1-70B-specdec, developers can build agentic workflows that can generate high-quality content such as articles, social media posts, and product descriptions, in real-time. 
  Conversational AI for customer service: llama-3.1-70B-specdec can be used to build conversational AI models that can understand and respond to customer inquiries in real-time. 
  Decision-making and planning: With llama-3.1-70B-specdec, developers can build AI models that can analyze complex data and make decisions in real-time.
  We’re committed to making this model more broadly available in the coming weeks. For now, paying customers will have exclusive access to llama-3.1-70B-specdec.

  Performance

  Artificial Analysis has included our llama-3.1-70B-specdec performance in their latest independent Llama 3.1 70B benchmark. See an overview of the results below and dive into the full report by Artificial Analysis here. 
  """

  chunker = TextChunker(max_chunk_length=1000, strategy="semantic")
  chunks = chunker.chunk_text(test1)

  for i, chunk in enumerate(chunks):
    print(f"Chunk {i + 1}:\n{chunk}\n\n")
