# Setup


## THE BACKEND

### AI SERVICES
So far, we use the following components for serving the AI models

#### Speech to text and diarization

Here we use the HuggingFace transformers library. The current models i recommend are the following:

- whisper model: "deepdml/whisper-large-v3-turbo"
- speaker diarization model: "pyannote/speaker-diarization-3.1"

**A note on the speaker diarization model**:
This model requires a sign up to use, and has a specific non-commercial license. In order for you to actually use it, you need to go in and accept the Terms of Use on a number of different pages on the HuggingFace website (the main url should guide you through this).

#### LLM

The large language models are currently served via the llama.cpp environment.
> **💡 why**?  I run on an M1 Max so leveraging the silicon GPU is a must, and llama.cpp is an easy way to do this

I recommend the following models:
- [llama3.2 3b instruct](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/blob/main/Llama-3.2-3B-Instruct-Q6_K.gguf) as a small model (used for generating the scratchpad to the large model, which the large model then uses to generate the recap)
- [marco o1](https://huggingface.co/bartowski/Marco-o1-GGUF/blob/main/Marco-o1-Q6_K_L.gguf) as a large model (used for generating the recap)


1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```


3. Create a `.env` file with your configuration

4. Start the backend server:
```bash
uvicorn src.main:app --reload
```

5. Run the llama.cpp server for the two models:
  * ```llama-server -m /path/to/llama3.2-3b-instruct.gguf -p 8081```
  * ```llama-server -m /path/to/marco-o1.gguf -p 8080```

--- 

## THE FRONTEND
### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```
2. Install dependencies:
```bash
npm install
```

3. Start the frontend server:
```bash
npm run dev
```


The application will be available at `http://localhost:5173`