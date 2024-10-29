import { useState } from "react";
import type { MetaFunction } from "@remix-run/node";
import AudioUploader from "~/components/AudioUploader";
import TranscriptionDisplay from "~/components/TranscriptionDisplay";
import ConfigArea from "~/components/ConfigArea";
import AudioPreview from "~/components/AudioPreview";

export const meta: MetaFunction = () => {
  return [
    { title: "Audio Transcription Service" },
    { name: "description", content: "Transcribe your audio files with speaker diarization" },
  ];
};

export default function Index() {
  const [transcription, setTranscription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState("english");
  const [numSpeakers, setNumSpeakers] = useState(2);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleTranscription = async (file: File) => {
    setSelectedFile(file);
    setIsLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("language", language);
      formData.append("num_speakers", numSpeakers.toString());

      const response = await fetch("http://localhost:8000/transcribe", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        throw new Error("Failed to transcribe audio");
      }

      const data = await response.json();
      setTranscription(data.transcription);
    } catch (error) {
      console.error("Error:", error);
      setError(error instanceof Error ? error.message : 'Failed to transcribe audio');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setTranscription("");
    setError(null);
  };

  return (
    <div className="min-h-screen breathing-background relative">
      <div className="container mx-auto px-4 py-12 max-w-5xl relative z-10">
        <h1 className="text-4xl font-bold text-center mb-2 gradient-text">
          Audio Transcription
        </h1>
        <p className="text-center text-gray-400 mb-12">
          Transform your audio into text with speaker detection
        </p>
        
        <div className="space-y-8">
          <ConfigArea
            language={language}
            onLanguageChange={setLanguage}
            numSpeakers={numSpeakers}
            onNumSpeakersChange={setNumSpeakers}
            disabled={isLoading}
          />
          
          <div className="w-full max-w-2xl mx-auto">
            {selectedFile ? (
              <AudioPreview 
                file={selectedFile} 
                onClose={handleClearFile}
              />
            ) : (
              <AudioUploader 
                onFileSelect={handleTranscription} 
                isUploading={isLoading}
                language={language}
                numSpeakers={numSpeakers}
              />
            )}
          </div>
          
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
              {error}
            </div>
          )}
          
          <TranscriptionDisplay 
            transcription={transcription} 
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
} 