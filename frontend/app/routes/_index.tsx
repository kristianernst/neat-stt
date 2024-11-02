import { useState, useCallback } from "react";
import type { MetaFunction } from "@remix-run/node";
import AudioUploader from "~/components/AudioUploader";
import LiveTranscriptionControl from "~/components/LiveTranscriptionControl";
import LiveTranscriptionDisplay from "~/components/LiveTranscriptionDisplay";
import RecordedTranscriptionDisplay from "~/components/RecordedTranscriptionDisplay";
import ConfigArea from "~/components/ConfigArea";
import AudioPreview from "~/components/AudioPreview";
import { formatTranscription } from '../utils/transcription-formatter';
import type { TranscriptionSegment } from '../utils/transcription-formatter';

export const meta: MetaFunction = () => {
  return [
    { title: "Audio Transcription Service" },
    { name: "description", content: "Transcribe your audio files with speaker diarization" },
  ];
};

export default function Index() {
  const [transcription, setTranscription] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [language, setLanguage] = useState("english");
  const [numSpeakers, setNumSpeakers] = useState(2);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDownloadReady, setIsDownloadReady] = useState(false);
  const [currentSegments, setCurrentSegments] = useState<TranscriptionSegment[]>([]);
  const [isStoppingTranscription, setIsStoppingTranscription] = useState(false);

  const handleTranscription = async (file: File) => {
    setSelectedFile(file);
    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);
    formData.append("num_speakers", numSpeakers.toString());

    try {
      const response = await fetch("http://localhost:8000/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to transcribe audio");
      }

      const data = await response.text();
      setTranscription(data);
    } catch (error) {
      console.error("Error:", error);
      setError(error instanceof Error ? error.message : 'Failed to transcribe audio');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartLive = () => {
    setIsLiveMode(true);
    setError(null);
  };

  const handleStopLive = async () => {
    try {
      setIsStoppingTranscription(true);
      const response = await fetch('http://localhost:8000/stop-live-transcribe', {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error("Failed to stop transcription");
      }
      setIsLiveMode(false);
      setIsDownloadReady(true);
    } catch (error) {
      console.error("Error stopping transcription:", error);
      setError(error instanceof Error ? error.message : 'Failed to stop transcription');
    } finally {
      setIsStoppingTranscription(false);
    }
  };

  const handleDownload = () => {
    const downloadFormat = window.confirm(
      'Choose a format:\nOK - Markdown (.md)\nCancel - Plain Text (.txt)'
    ) ? 'md' : 'txt';
    
    const formattedContent = formatTranscription(currentSegments, downloadFormat);
    const blob = new Blob([formattedContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription.${downloadFormat}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setIsLiveMode(false);
    setIsDownloadReady(false);
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setTranscription("");
    setError(null);
  };

  const handleLanguageChange = useCallback((newLanguage: string) => {
    setLanguage(newLanguage);
  }, []);

  const handleNumSpeakersChange = useCallback((num: number) => {
    setNumSpeakers(num);
  }, []);

  const handleSegmentsUpdate = useCallback((segments: TranscriptionSegment[]) => {
    setCurrentSegments(segments);
  }, []);

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
            onLanguageChange={handleLanguageChange}
            numSpeakers={numSpeakers}
            onNumSpeakersChange={handleNumSpeakersChange}
            disabled={isLoading || isLiveMode}
          />
          
          <div className="w-full max-w-2xl mx-auto space-y-4">
            {selectedFile ? (
              <AudioPreview 
                file={selectedFile} 
                onClose={handleClearFile}
              />
            ) : (
              <>
                <AudioUploader 
                  onFileSelect={handleTranscription}
                  isUploading={isLoading}
                  isDisabled={isLiveMode}
                />
                <div className="text-center">
                  <span className="text-gray-400">or</span>
                </div>
                <LiveTranscriptionControl
                  onStart={handleStartLive}
                  onStop={handleStopLive}
                  onDownload={handleDownload}
                  isLiveMode={isLiveMode}
                  isDownloadReady={isDownloadReady}
                  isDisabled={isLoading}
                  isStoppingTranscription={isStoppingTranscription}
                />
              </>
            )}
          </div>
          
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
              {error}
            </div>
          )}
          
          <LiveTranscriptionDisplay
            isLiveMode={isLiveMode}
            language={language}
            numSpeakers={numSpeakers}
            onSegmentsUpdate={handleSegmentsUpdate}
            isDownloadReady={isDownloadReady}
          />
          
          <RecordedTranscriptionDisplay
            transcription={transcription}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
} 