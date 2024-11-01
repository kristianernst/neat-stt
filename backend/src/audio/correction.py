from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import Dict, List, Any
from src.configuration.log import get_logger

class TranscriptionCorrector:
    def __init__(self, model_name: str = "gpt2", device: str = "cpu"):
        self.logger = get_logger()
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        
    def correct_transcription(self, segment: Dict[str, Any], confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Correct transcription using language model and logprobs.
        """
        text = segment["text"]
        logprobs = segment.get("logprobs", [])
        
        # Find low confidence words using logprobs
        corrections = []
        for word_probs in logprobs:
            max_prob = max(word_probs['probs'])
            if max_prob < confidence_threshold:
                # Get context and alternatives
                alternatives = word_probs['tokens'][:5]  # Top 5 alternatives
                corrected_word = self._get_best_word(text, alternatives)
                corrections.append(corrected_word)
        
        # Apply corrections
        corrected_text = text
        for correction in corrections:
            corrected_text = self._apply_correction(corrected_text, correction)
            
        return {
            **segment,
            "text": corrected_text,
            "corrections": corrections
        }
    
    def _get_best_word(self, context: str, alternatives: List[str]) -> str:
        """
        Use language model to pick the best alternative based on context.
        """
        inputs = self.tokenizer(context, return_tensors="pt").to(self.device)
        
        best_score = float('-inf')
        best_word = alternatives[0]
        
        for word in alternatives:
            # Add word to context and get score
            test_input = context + " " + word
            with torch.no_grad():
                outputs = self.model(**inputs)
                score = outputs.logits[0, -1, :].max().item()
                
            if score > best_score:
                best_score = score
                best_word = word
                
        return best_word
    
    def _apply_correction(self, text: str, correction: str) -> str:
        """
        Apply a single correction to the text.
        """
        # Implement correction logic here
        # This is a simple example - you might want more sophisticated replacement logic
        return text.replace(correction['original'], correction['corrected']) 