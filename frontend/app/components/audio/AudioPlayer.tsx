import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  BsFillPlayFill,
  BsPauseFill,
  BsVolumeUp,
  BsVolumeDown,
  BsVolumeMute,
} from 'react-icons/bs';
import Slider from './Slider';

interface AudioPlayerProps {
  src: string;
  onEnded?: () => void;
}

export default function AudioPlayer({ src, onEnded }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handlers = {
      loadedmetadata: () => setDuration(audio.duration || 0),
      timeupdate: () => setCurrentTime(audio.currentTime || 0),
      ended: () => {
        setIsPlaying(false);
        onEnded?.();
      },
    };

    Object.entries(handlers).forEach(([event, handler]) => {
      audio.addEventListener(event, handler);
    });

    return () => {
      Object.entries(handlers).forEach(([event, handler]) => {
        audio.removeEventListener(event, handler);
      });
    };
  }, [onEnded]);

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeChange = useCallback((value: number) => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = value;
    setCurrentTime(value);
  }, []);

  const handleVolumeChange = useCallback((value: number) => {
    if (!audioRef.current) return;
    audioRef.current.volume = value;
    setVolume(value);
    setIsMuted(value === 0);
  }, []);

  const toggleMute = () => {
    if (!audioRef.current) return;
    const newMutedState = !isMuted;
    audioRef.current.muted = newMutedState;
    setIsMuted(newMutedState);
  };

  const VolumeIcon = isMuted || volume === 0 ? BsVolumeMute 
    : volume < 0.5 ? BsVolumeDown 
    : BsVolumeUp;

  return (
    <div className="flex flex-col space-y-2 bg-[var(--card-bg)] rounded-lg p-4">
      <audio ref={audioRef} src={src} className="hidden" />

      <div className="flex items-center space-x-4">
        <button
          onClick={togglePlay}
          className="w-8 h-8 flex items-center justify-center rounded-full
                     text-[var(--text-secondary)] hover:text-[var(--text-primary)]
                     transition-colors"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <BsPauseFill className="w-8 h-8" />
          ) : (
            <BsFillPlayFill className="w-8 h-8 translate-x-0.5" />
          )}
        </button>

        <div className="flex-1 flex items-center space-x-3">
          <span className="text-[var(--text-secondary)] text-sm font-mono min-w-[40px]">
            {formatTime(currentTime)}
          </span>

          <Slider
            min={0}
            max={duration}
            value={currentTime}
            onChange={handleTimeChange}
            size="md"
            className="flex-1"
          />

          <span className="text-[var(--text-secondary)] text-sm font-mono min-w-[40px]">
            {formatTime(duration)}
          </span>
        </div>

        <div className="flex items-center space-x-2 group">
          <button
            onClick={toggleMute}
            className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] 
                     transition-colors"
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            <VolumeIcon className="w-5 h-5" />
          </button>

          <div className="w-20 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <Slider
              min={0}
              max={1}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              size="sm"
              className="ml-2"
            />
          </div>
        </div>
      </div>
    </div>
  );
}