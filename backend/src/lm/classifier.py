from typing import Optional, Union
import json

from openai.types.chat import ChatCompletionMessage

from src.lm.helpers.client import LLMClient
from src.lm.prompts import GENERAL_REFLECTION_INST
from src.configuration.environment import SMALL_LLM_MODEL, SMALL_LLM_ENDPOINT
from src.configuration.log import get_logger


class TranscriptClassifier:
    def __init__(self, llm_client: LLMClient):
        self.logger = get_logger()
        self.llm_client = llm_client

    def classify(self, transcript_sample: str, max_sample_length: int = 2000) -> Optional[str]:
        """
        Classify the type of transcript (meeting or lecture).
        
        Args:
            transcript_sample: First portion of the transcript
            max_sample_length: Maximum length of transcript to analyze
            
        Returns:
            String containing transcript type ('meeting' or 'lecture') or None if classification fails
        """
        self.logger.info("Starting transcript classification")
        
        # Take a sample from the start of the transcript
        sample = transcript_sample[:max_sample_length]
        self.logger.debug(f"transcript sample: {sample}")
        
        try:
            conversation = [
                {"role": "system", "content": GENERAL_REFLECTION_INST},
                {"role": "user", "content": f"Please analyze this transcript, run the function classify_transcript_type on it:\n\n{sample}"}
            ]
            
            response: Union[ChatCompletionMessage, None] = self.llm_client.ask(
                messages=conversation,
                temperature=0.1,
                max_tokens=500,
                stream=False,
                response_format={"type": "json_object"}
            )
            if response:
              try:
                return json.loads(response.content).get("type")
              except KeyError as e:
                self.logger.error(f"Failed to parse response: {str(e)}")
                raise KeyError(f"Failed to parse response: {str(e)}")
              except ValueError as e:
                self.logger.error(f"Failed to parse response: {str(e)}")
                raise ValueError(f"Failed to parse response: {str(e)}")
              except Exception as e:
                self.logger.error(f"Failed to parse response: {str(e)}")
                raise
        except Exception as e:
            self.logger.error(f"Classification failed: {str(e)}")
            raise
          
if __name__ == "__main__":
    import time
    logger = get_logger()
    classifier = TranscriptClassifier(
      LLMClient(model_name=SMALL_LLM_MODEL, base_url=SMALL_LLM_ENDPOINT)
    )
    # keep stats in a dict
    
    # from concurrent.futures import ThreadPoolExecutor, as_completed
    # stats = {}
    # start_time = time.time()
    # with ThreadPoolExecutor(max_workers=10) as executor:
    #   futures = [executor.submit(classifier.classify, "Hello, how are you?, this lecture will be about the history of the internet") for _ in range(10)]
    #   for future in as_completed(futures):
    #     try:
    #       result = future.result()
    #       stats[result] = stats.get(result, 0) + 1
    #     except Exception as e:
    #       raise
    
    # logger.info(stats)
    # logger.info(f"Time taken: {time.time() - start_time} seconds") # takes 5-6 seconds
    
    # normal loop
    start_time = time.time()
    stats = {}
    for _ in range(10):
      result = classifier.classify("Hello, how are you?, this lecture will be about the history of the internet")
      stats[result] = stats.get(result, 0) + 1
    logger.info(stats)
    logger.info(f"Time taken: {time.time() - start_time} seconds") # takes 1.4 seconds