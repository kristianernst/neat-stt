from typing import List, Optional, Literal
from dataclasses import dataclass

ModelType = Literal["whisper", "mms", "other"]


@dataclass
class ModelConfig:
  name: str
  type: ModelType
  processor: str
  model: str
  supported_languages: Optional[List[str]] = None

  @classmethod
  def from_dict(cls, config_dict: dict) -> "ModelConfig":
    return cls(
      name=config_dict["name"],
      type=config_dict["type"],
      processor=config_dict["processor"],
      model=config_dict["model"],
      supported_languages=config_dict.get("supported_languages"),
    )


# Predefined model configurations
WHISPER_CONFIG = ModelConfig(
  name="deepdml/whisper-large-v3-turbo",
  type="whisper",
  processor="WhisperProcessor",
  model="WhisperForConditionalGeneration",
  supported_languages=["english", "danish", "german"],  # Add more as needed
)

MMS_CONFIG = ModelConfig(
  name="facebook/mms-1b-fl102",
  type="mms",
  processor="AutoProcessor",
  model="AutoModelForSpeechSeq2Seq",
  supported_languages=["english", "danish", "german"],  # Add languages supported by MMS
)

# Dictionary of available models
AVAILABLE_MODELS = {"whisper": WHISPER_CONFIG, "mms": MMS_CONFIG}
