import { useState, useCallback, useEffect } from "react";
import type { MetaFunction } from "@remix-run/node";
import AudioUploader from "~/components/AudioUploader";
import TranscriptionControl from "~/components/TranscriptionControl";
import TranscriptionDisplay from "~/components/TranscriptionDisplay";
import AudioPreview from "~/components/AudioPreview";
import { TranscriptionSegment } from '../utils/transcription-formatter';
import { processSSEStream } from '~/utils/sseUtils';
import Header from "~/components/Header";
import Settings from "~/components/Settings";
import { useOutletContext } from "@remix-run/react";
import ConfigurationSummary from "~/components/ConfigurationSummary";

type ContextType = { isDark: boolean; setIsDark: (isDark: boolean) => void };

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
  const [segments, setSegments] = useState<TranscriptionSegment[]>([]);
  const [isStoppingTranscription, setIsStoppingTranscription] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false); // Indicates transcription in progress
  const [progress, setProgress] = useState(0); // New state for progress
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { isDark, setIsDark } = useOutletContext<ContextType>();

  const handleTranscription = async (file: File) => {
    setSelectedFile(file);
    setIsLoading(true);
    setIsTranscribing(true);
    setError(null);
    setSegments([]);
    setProgress(0);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);
    formData.append("num_speakers", numSpeakers.toString());

    try {
      const response = await fetch("http://localhost:8000/transcribe", {
        method: "POST",
        body: formData,
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to transcribe audio");
      }

      await processSSEStream(response.body, (eventType, eventData) => {
        switch (eventType) {
          case "ready":
            setIsLoading(false);
            break;
          case "transcription":
            setSegments(prev => {
              // If this is an update to the last segment, replace it
              if (prev.length > 0 && prev[prev.length - 1].speaker === eventData.speaker) {
                const newSegments = [...prev];
                newSegments[newSegments.length - 1] = eventData;
                return newSegments;
              }
              // Otherwise add as new segment
              return [...prev, eventData];
            });
            break;
          case "progress":
            setProgress(eventData.progress);
            break;
          case "error":
            setError(eventData.error);
            setIsTranscribing(false);
            break;
          case "close":
            setIsTranscribing(false);
            setProgress(100);
            break;
        }
      });
    } catch (error) {
      console.error("Error:", error);
      setError(error instanceof Error ? error.message : 'Failed to transcribe audio');
      setIsTranscribing(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartLive = () => {
    setIsLiveMode(true);
    setError(null);
    setSegments([]); // Clear previous segments
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
    } catch (error) {
      console.error("Error stopping transcription:", error);
      setError(error instanceof Error ? error.message : 'Failed to stop transcription');
    } finally {
      setIsStoppingTranscription(false);
      setIsTranscribing(false);
    }
  };

  const handleClearFile = useCallback(() => {
    setSelectedFile(null);
    setTranscription("");
    setError(null);
    setSegments([]);
    setIsTranscribing(false);
    setProgress(0);
    setIsLiveMode(false);
  }, []);

  const handleLanguageChange = useCallback((newLanguage: string) => {
    setLanguage(newLanguage);
  }, []);

  const handleNumSpeakersChange = useCallback((num: number) => {
    setNumSpeakers(num);
  }, []);

  const handleSegmentsUpdate = useCallback((segments: TranscriptionSegment[]) => {
    setSegments(segments);
  }, []);
  // Clear segments when switching modes
  useEffect(() => {
    if (isLiveMode) {
      setSegments([]);
    }
  }, [isLiveMode]);

  return (
    <div className="min-h-screen breathing-background relative">
      <Header isDark={isDark} onThemeChange={setIsDark} />
      <div className="container mx-auto px-4 pt-32 pb-12 max-w-5xl relative z-10">
        <div className="space-y-8">
          <ConfigurationSummary
            language={language}
            numSpeakers={numSpeakers}
            onOpenSettings={() => setIsSettingsOpen(true)}
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
                <TranscriptionControl
                  isLiveMode={isLiveMode}
                  isDisabled={isLoading}
                  isStoppingTranscription={isStoppingTranscription}
                  onStartLive={handleStartLive}
                  onStopLive={handleStopLive}
                />
              </>
            )}
          </div>
          
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
              {error}
            </div>
          )}
          
          <TranscriptionDisplay
            isLiveMode={isLiveMode}
            language={language}
            numSpeakers={numSpeakers}
            onSegmentsUpdate={handleSegmentsUpdate}
            transcription={transcription}
            isLoading={isLoading}
            segments={segments}
            setSegments={setSegments}
            isTranscribing={isTranscribing}
            progress={progress}
            setProgress={setProgress}
          />
        </div>
      </div>
      <Settings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        language={language}
        onLanguageChange={handleLanguageChange}
        numSpeakers={numSpeakers}
        onNumSpeakersChange={handleNumSpeakersChange}
        disabled={isLoading || isLiveMode}
      />
    </div>
  );
}