import coremltools as ct
from transformers import AutoTokenizer
import numpy as np

from configuration.log import get_logger


class CoreMLModel:
  def __init__(self, model_path: str, tokenizer_name: str):
    """
    Initialize the Core ML model and tokenizer.
    """
    self.logger = get_logger()
    self.model = ct.models.MLModel(model_path)
    self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

  def predict(self, text: str, max_length: int = 50) -> str:
    """
    Run inference on the Core ML model and return the generated text.
    """
    self.logger.info("Running inference on Core ML model ...")

    try:
      # Tokenize the input text
      inputs = self.tokenizer(text, return_tensors="np")

      input_ids = inputs["input_ids"].astype(np.int32)

      # Prepare inputs for Core ML
      coreml_inputs = {"input_ids": input_ids}

      # Run the model
      outputs = self.model.predict(coreml_inputs)

      # Extract and decode the output tokens
      output_ids = outputs["output_ids"]
      generated_text = self.tokenizer.decode(output_ids.flatten(), skip_special_tokens=True)
      return generated_text
    except Exception as e:
      self.logger.error(f"Error running inference on Core ML model: {e}")
      raise
