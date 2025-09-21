import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, ListMusic, Music2 } from 'lucide-react';

//  MOCK DATA 
// Using free assets from Pixabay
const mockTracks = [
  {
    id: 1,
    title: "Ambient Classical Guitar",
    artist: "William King",
    artwork: "https://cdn.pixabay.com/audio/2023/10/02/11-19-14-16_200x200.jpg",
    url: "https://cdn.pixabay.com/audio/2023/10/02/audio_35b072f623.mp3",
    duration: 132,
  },
  {
    id: 2,
    title: "The Beat of Nature",
    artist: "Olexy",
    artwork: "https://cdn.pixabay.com/audio/2023/11/14/09-00-50-943_200x200.jpg",
    url: "https://cdn.pixabay.com/audio/2023/11/14/audio_41a804b53c.mp3",
    duration: 121,
  },
  {
    id: 3,
    title: "Moment",
    artist: "SergeQuadrado",
    artwork: "https://cdn.pixabay.com/audio/2023/08/03/10-25-37-251_200x200.jpg",
    url: "https://cdn.pixabay.com/audio/2023/08/03/audio_b29cce323b.mp3",
    duration: 129,
  },
    {
    id: 4,
    title: "Powerful Beat",
    artist: "penguinmusic",
    artwork: "https://cdn.pixabay.com/audio/2023/09/26/11-13-10-850_200x200.png",
    url: "https://cdn.pixabay.com/audio/2023/09/26/audio_a72f238d2f.mp3",
    duration: 104,
  },
];

//  UTILITY FUNCTIONS 
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

//  CHILD COMPONENTS 

const Header = () => (

        Waveform

);

const TrackItem = ({ track, isPlaying, isCurrent, onPlay }) => (
     onPlay(track.id)}
    >

        {track.title}
        {track.artist}
      
      {formatTime(track.duration)}
      {isCurrent && isPlaying ? (

      ) : (
        
      )}
      {`
        .playing-icon { display: flex; align-items: flex-end; height: 16px; gap: 2px; }
        .playing-bar { width: 3px; height: 100%; animation: play 1.2s ease-in-out infinite; }
        .playing-bar1 { animation-delay: 0s; }
        .playing-bar2 { animation-delay: 0.2s; }
        .playing-bar3 { animation-delay: 0.4s; }
        @keyframes play {
          0% { transform: scaleY(0.1); }
          20% { transform: scaleY(1); }
          80% { transform: scaleY(0.1); }
          100% { transform: scaleY(0.1); }
        }
      `}
    
);

const TrackList = ({ tracks, currentTrack, isPlaying, onPlayTrack }) => (

      Your Library

      {tracks.map(track => (
         onPlayTrack(track.id)}
        />
      ))}

);

const PlayerControls = ({ 
  currentTrack, 
  isPlaying, 
  progress,
  duration,
  volume,
  onPlayPause, 
  onNext, 
  onPrev,
  onSeek,
  onVolumeChange
}) => {
  if (!currentTrack) {
    return (
      
          Select a song to play
      
    );
  }

  return (

        {/* Track Info */}

            {currentTrack.title}
            {currentTrack.artist}

        {/* Player Controls */}

              {isPlaying ?  : }

            {formatTime(progress)}
             
            {formatTime(duration)}

        {/* Volume Controls */}
        
            {volume > 0 ?  : }

  );
};

//  MAIN APP COMPONENT 

function App() {
  const [tracks, setTracks] = useState([]);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [volume, setVolume] = useState(0.5);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const audioRef = useRef(null);

  useEffect(() => {
    // Simulate API call
    const fetchTracks = () => {
      try {
        setTimeout(() => {
          setTracks(mockTracks);
          setIsLoading(false);
        }, 1000);
      } catch (err) {
        setError("Failed to load tracks.");
        setIsLoading(false);
      }
    };
    fetchTracks();
  }, []);
  
  const currentTrack = currentTrackIndex !== null ? tracks[currentTrackIndex] : null;

  // Effect to handle audio source changes
  useEffect(() => {
    if (audioRef.current && currentTrack) {
        if (audioRef.current.src !== currentTrack.url) {
            audioRef.current.src = currentTrack.url;
        }
        if (isPlaying) {
            audioRef.current.play().catch(e => console.error("Error playing audio:", e));
        } else {
            audioRef.current.pause();
        }
    }
  }, [currentTrack, isPlaying]);

  // Effect to handle volume
  useEffect(() => {
    if (audioRef.current) {
        audioRef.current.volume = volume;
    }
  }, [volume]);

  const handlePlayPause = useCallback(() => {
    if (currentTrackIndex === null && tracks.length > 0) {
      setCurrentTrackIndex(0);
    }
    setIsPlaying(prev => !prev);
  }, [currentTrackIndex, tracks.length]);
  
  const playTrack = useCallback((trackId) => {
    const trackIndex = tracks.findIndex(t => t.id === trackId);
    if (trackIndex !== -1) {
      if (trackIndex === currentTrackIndex) {
        handlePlayPause();
      } else {
        setCurrentTrackIndex(trackIndex);
        setIsPlaying(true);
      }
    }
  }, [tracks, currentTrackIndex, handlePlayPause]);

  const handleNextTrack = useCallback(() => {
    if (tracks.length > 0) {
      setCurrentTrackIndex(prevIndex => (prevIndex + 1) % tracks.length);
      setIsPlaying(true);
    }
  }, [tracks.length]);

  const handlePrevTrack = useCallback(() => {
    if (tracks.length > 0) {
      setCurrentTrackIndex(prevIndex => (prevIndex - 1 + tracks.length) % tracks.length);
      setIsPlaying(true);
    }
  }, [tracks.length]);

  const handleTimeUpdate = () => {
    if (audioRef.current) {
        setProgress(audioRef.current.currentTime);
    }
  };

  const handleSeek = (e) => {
    if (audioRef.current) {
        audioRef.current.currentTime = e.target.value;
        setProgress(e.target.value);
    }
  };
  
  const handleVolumeChange = (e) => {
    setVolume(parseFloat(e.target.value));
  };

  if (isLoading) {
    return (

          Loading Music...

    );
  }

  if (error) {
    return (
      
        {error}
      
    );
  }

  return (

       {
            // Optional: You can get accurate duration here
        }}
      />
    
  );
}

export default App;