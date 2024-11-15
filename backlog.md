# Neat STT next steps

### ML
- [ ] experiment with better segmentation, some weirdness happens in danish at least "Skrevet af Nicolai Winther, and "tak" and "tak for mødet" is repeatedly said for no reason, so there might be something wrong with the way i process the audio. (only happens in danish, when multiple speakers. probably a limitation of the model.)
- [ ] convert to coreml for faster inference potentially?
- [ ] LLM correction of transcription
- [ ] LLM summarizer / analyzer (preferably locally too. might not work well with non-english, then default to groc or something)


### UI
- [x] Make smaller button animations for copy to clipboard and download
- [x] better rendering
