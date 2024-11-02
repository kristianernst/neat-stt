from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
MODEL_NAME = "meta-llama/Llama-2-7b-chat-hf"
# MODEL_NAME = "facebook/MobileLLM-1B"
#MODEL_NAME = "CohereForAI/aya-expanse-8b"
class SimpleTranscriptionCorrector:
    def __init__(self, device: str):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
        
        self.model.to(device)
        print(f"Model loaded and moved to {device}")
        self.model.eval()

    def correct_transcription(self, token_alternatives: list) -> str:
        """
        Correct transcription using token alternatives and their probabilities.
        """
        prompt = """Given these word alternatives with their probabilities, output the most likely correct sentence.
        Only output the corrected sentence, nothing else.
        
        Alternatives: """
        
        for position_alternatives in token_alternatives:
            sorted_alts = sorted(position_alternatives, key=lambda x: x[1], reverse=True)
            alternatives_str = "|".join(f"{word}({prob:.2f})" for word, prob in sorted_alts)
            prompt += f"[{alternatives_str}] "

        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=256,
                temperature=0.0,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
        corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the prompt from the output to get just the correction
        corrected = corrected.replace(prompt, "").strip()
        return corrected

if __name__ == "__main__":
    # Test case with multiple alternatives
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Using device: {device}")
    
    test_alternatives = [
        [("the", 0.95), ("a", 0.03), ("that", 0.02)],
        [("quick", 0.75), ("quck", 0.15), ("quit", 0.10)],
        [("brown", 0.65), ("brwn", 0.20), ("burn", 0.15)],
        [("fox", 0.92), ("box", 0.05), ("fax", 0.03)]
    ]
    
    corrector = SimpleTranscriptionCorrector(device=device)
    corrected = corrector.correct_transcription(test_alternatives)
    
    print("Input alternatives:")
    for i, alts in enumerate(test_alternatives):
        print(f"Position {i}: {alts}")
    print(f"\nCorrected: {corrected}")

