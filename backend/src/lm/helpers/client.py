import os
from typing import List, Dict, Union, Optional
from openai import OpenAI
import traceback

from src.configuration.log import get_logger

__all__ = ["LLMClient"]


class LLMClient:
  def __init__(
    self,
    base_url: str,
    api_key: str = "not-needed",
    model_name: str = "any-model-name",
  ):
    self.logger = get_logger()
    self.logger.info(f"Initializing LLMClient with model: {model_name}")
    self.logger.debug(f"Base URL: {base_url}")
    self.client = OpenAI(base_url=base_url, api_key=api_key)
    self.model_name = model_name
    self.logger.debug("LLMClient initialized successfully")

  def ask(
    self,
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    max_tokens: int = 2000,
    stream: bool = True,
    response_format: Optional[Dict] = None,
    functions: Optional[List[Dict]] = None,
    function_call: Optional[Dict] = None,
  ) -> Union[str, None]:
    """
    Send a request to the LLM server and get the response.

    Args:
        messages: List of message dictionaries with 'role' and 'content'.
        temperature: Controls randomness (0.0 to 1.0).
        max_tokens: Maximum number of tokens to generate.
        stream: Whether to stream the response.
        functions: List of function definitions.
        function_call: Forced function call specification.

    Returns:
        Generated text response or None if error occurs.
    """
    self.logger.info(f"Sending request to LLM server (stream={stream})")
    self.logger.debug(f"Request parameters: temperature={temperature}, max_tokens={max_tokens}")
    self.logger.debug(f"Messages: {messages}")

    try:
      if len(messages) == 0:
        self.logger.warning("Empty messages list provided")
        return None

      kwargs = {
        "model": self.model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
      }

      if response_format:
        kwargs["response_format"] = response_format
      
      if functions:
        kwargs["functions"] = functions
      if function_call:
        kwargs["function_call"] = function_call

      response = self.client.chat.completions.create(**kwargs)

      if stream:
        self.logger.debug("Starting stream processing")
        full_response = []
        for chunk in response:
          if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response.append(content)
            print(content, end="", flush=True)
            self.logger.debug(f"Received chunk: {content}")
        print()
        complete_response = "".join(full_response)
        self.logger.info("Stream processing completed successfully")
        self.logger.debug(f"Final response length: {len(complete_response)} characters")
        return complete_response
      else:
        if hasattr(response.choices[0].message, 'function_call'):
          return response.choices[0].message
        return response.choices[0].message.content.strip()

    except Exception as e:
      self.logger.error(f"Error in LLMClient.ask: {str(e)}")
      self.logger.debug(f"Full traceback: {traceback.format_exc()}")
      return None
