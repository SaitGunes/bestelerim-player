import { useState, useEffect, useRef, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { 
  Play, 
  Pause, 
  SkipForward, 
  SkipBack, 
  Volume2, 
  VolumeX,
  Music,
  Github,
  List,
  Shuffle,
  Repeat,
  Heart,
  Menu,
  X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Toaster, toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DEFAULT_ALBUM_ART = "https://images.pexels.com/photos/7605490/pexels-photo-7605490.jpeg";

function App() {
  const [mediaFiles, setMediaFiles] = useState([]);
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isShuffle, setIsShuffle] = useState(false);
  const [isRepeat, setIsRepeat] = useState(false);
  const [favorites, setFavorites] = useState([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  const audioRef = useRef(null);

  // Fetch media files
  const fetchMedia = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/media`);
      setMediaFiles(response.data.files);
    } catch (error) {
      console.error("Error fetching media:", error);
      toast.error("Medya dosyaları yüklenirken hata oluştu");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMedia();
  }, [fetchMedia]);

  // Audio event handlers
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);
    const handleEnded = () => {
      if (isRepeat) {
        audio.currentTime = 0;
        audio.play();
      } else {
        playNext();
      }
    };

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [isRepeat, currentTrack, mediaFiles]);

  // Volume effect
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  const playTrack = async (track) => {
    setCurrentTrack(track);
    setIsPlaying(true);
    
    // Record play stat
    try {
      await axios.post(`${API}/play/${encodeURIComponent(track.name)}`);
    } catch (error) {
      console.error("Error recording play:", error);
    }
  };

  const togglePlay = () => {
    if (!currentTrack && mediaFiles.length > 0) {
      playTrack(mediaFiles[0]);
      return;
    }
    
    if (isPlaying) {
      audioRef.current?.pause();
    } else {
      audioRef.current?.play();
    }
    setIsPlaying(!isPlaying);
  };

  const playNext = () => {
    if (!currentTrack || mediaFiles.length === 0) return;
    
    let nextIndex;
    if (isShuffle) {
      nextIndex = Math.floor(Math.random() * mediaFiles.length);
    } else {
      const currentIndex = mediaFiles.findIndex(f => f.id === currentTrack.id);
      nextIndex = (currentIndex + 1) % mediaFiles.length;
    }
    playTrack(mediaFiles[nextIndex]);
  };

  const playPrevious = () => {
    if (!currentTrack || mediaFiles.length === 0) return;
    
    const currentIndex = mediaFiles.findIndex(f => f.id === currentTrack.id);
    const prevIndex = currentIndex === 0 ? mediaFiles.length - 1 : currentIndex - 1;
    playTrack(mediaFiles[prevIndex]);
  };

  const handleSeek = (value) => {
    const newTime = (value[0] / 100) * duration;
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (value) => {
    setVolume(value[0] / 100);
    setIsMuted(false);
  };

  const toggleFavorite = (trackId) => {
    setFavorites(prev => 
      prev.includes(trackId) 
        ? prev.filter(id => id !== trackId)
        : [...prev, trackId]
    );
  };

  const formatTime = (time) => {
    if (!time || isNaN(time)) return "0:00";
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Audio element - load new track
  useEffect(() => {
    if (currentTrack && audioRef.current) {
      audioRef.current.src = currentTrack.url;
      audioRef.current.load();
      audioRef.current.play().catch(console.error);
    }
  }, [currentTrack]);

  return (
    <div className="app-container" data-testid="app-container">
      <Toaster position="top-right" theme="dark" />
      
      {/* Hidden Audio Element */}
      <audio ref={audioRef} preload="metadata" />

      {/* Mobile Header */}
      <div className="mobile-header fixed top-0 left-0 right-0 h-16 bg-black/80 backdrop-blur-xl border-b border-white/5 z-50 items-center justify-between px-4 md:hidden">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center">
            <Music className="w-5 h-5 text-indigo-400" />
          </div>
          <span className="font-semibold text-lg">Bestelerim</span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          data-testid="mobile-menu-btn"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </Button>
      </div>

      {/* Sidebar */}
      <aside className="sidebar" data-testid="sidebar">
        <div className="p-6">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-10">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg glow-primary">
              <Music className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight">Bestelerim</h1>
              <p className="text-xs text-muted-foreground">Müzik Oynatıcı</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="space-y-2">
            <Button 
              variant="ghost" 
              className="w-full justify-start gap-3 text-white hover:bg-white/10"
              data-testid="nav-all-songs"
            >
              <List className="w-5 h-5" />
              Tüm Şarkılar
            </Button>
            <Button 
              variant="ghost" 
              className="w-full justify-start gap-3 text-muted-foreground hover:text-white hover:bg-white/10"
              data-testid="nav-favorites"
            >
              <Heart className="w-5 h-5" />
              Favoriler
              {favorites.length > 0 && (
                <span className="ml-auto text-xs bg-indigo-500/30 px-2 py-0.5 rounded-full">
                  {favorites.length}
                </span>
              )}
            </Button>
          </nav>
        </div>

        {/* GitHub Link */}
        <div className="mt-auto p-6 border-t border-white/5">
          <a
            href="https://github.com/SaitGunes/bestelerim"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 text-muted-foreground hover:text-white transition-colors"
            data-testid="github-link"
          >
            <Github className="w-5 h-5" />
            <span className="text-sm">GitHub Repo</span>
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content" data-testid="main-content">
        {/* Hero Section */}
        <div className="hero-gradient p-8 md:p-12">
          <div className="max-w-4xl pt-16 md:pt-0">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 tracking-tight">
              Bestelerim
            </h2>
            <p className="text-lg text-muted-foreground max-w-xl">
              Kendi bestelerimi dinleyin ve keşfedin. GitHub üzerinden yayınlanan özel müzik koleksiyonum.
            </p>
            <div className="flex items-center gap-4 mt-6">
              <Button
                onClick={togglePlay}
                className="rounded-full px-8 py-6 bg-indigo-500 hover:bg-indigo-600 text-white font-semibold transition-all hover:scale-105 active:scale-95"
                data-testid="hero-play-btn"
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-5 h-5 mr-2" />
                    Duraklat
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    Oynat
                  </>
                )}
              </Button>
              <span className="text-muted-foreground">
                {mediaFiles.length} şarkı
              </span>
            </div>
          </div>
        </div>

        {/* Song List */}
        <div className="p-8 md:p-12">
          <h3 className="text-2xl font-semibold mb-6">Şarkılar</h3>
          
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map(i => (
                <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="song-list">
              {mediaFiles.map((file, index) => (
                <Card
                  key={file.id}
                  className={`song-card cursor-pointer border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all duration-300 ${
                    currentTrack?.id === file.id ? 'border-indigo-500/50 bg-indigo-500/10' : ''
                  }`}
                  onClick={() => playTrack(file)}
                  data-testid={`song-card-${index}`}
                >
                  <CardContent className="p-4 flex items-center gap-4">
                    {/* Album Art */}
                    <div className="relative w-14 h-14 rounded-lg overflow-hidden flex-shrink-0 bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
                      <img
                        src={DEFAULT_ALBUM_ART}
                        alt={file.display_name}
                        className="w-full h-full object-cover opacity-60"
                      />
                      <div className="play-overlay absolute inset-0 bg-black/50 flex items-center justify-center">
                        {currentTrack?.id === file.id && isPlaying ? (
                          <div className="now-playing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                            <span></span>
                          </div>
                        ) : (
                          <Play className="w-6 h-6 text-white" />
                        )}
                      </div>
                    </div>

                    {/* Track Info */}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium truncate text-white">
                        {file.display_name}
                      </h4>
                      <p className="text-sm text-muted-foreground truncate">
                        {file.type === 'audio' ? 'Ses Dosyası' : 'Video'}
                      </p>
                    </div>

                    {/* Favorite Button */}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="flex-shrink-0 hover:bg-white/10"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(file.id);
                      }}
                      data-testid={`favorite-btn-${index}`}
                    >
                      <Heart
                        className={`w-5 h-5 ${
                          favorites.includes(file.id)
                            ? 'fill-red-500 text-red-500'
                            : 'text-muted-foreground'
                        }`}
                      />
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Player Bar */}
      <div className="player-bar" data-testid="player-bar">
        <div className="h-full flex items-center justify-between px-4 md:px-8 max-w-screen-2xl mx-auto">
          {/* Current Track Info */}
          <div className="flex items-center gap-4 w-1/4 min-w-0">
            {currentTrack ? (
              <>
                <div className="w-14 h-14 rounded-lg overflow-hidden flex-shrink-0 bg-gradient-to-br from-indigo-500/20 to-purple-500/20">
                  <img
                    src={DEFAULT_ALBUM_ART}
                    alt={currentTrack.display_name}
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="min-w-0">
                  <h4 className="font-medium truncate text-sm" data-testid="current-track-name">
                    {currentTrack.display_name}
                  </h4>
                  <p className="text-xs text-muted-foreground">Beste</p>
                </div>
              </>
            ) : (
              <div className="text-muted-foreground text-sm">
                Şarkı seçilmedi
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="flex flex-col items-center gap-2 flex-1 max-w-xl">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                className={`hover:bg-white/10 ${isShuffle ? 'text-indigo-400' : 'text-muted-foreground'}`}
                onClick={() => setIsShuffle(!isShuffle)}
                data-testid="shuffle-btn"
              >
                <Shuffle className="w-4 h-4" />
              </Button>
              
              <Button
                variant="ghost"
                size="icon"
                className="hover:bg-white/10 text-white"
                onClick={playPrevious}
                data-testid="prev-btn"
              >
                <SkipBack className="w-5 h-5" />
              </Button>
              
              <Button
                size="icon"
                className="w-12 h-12 rounded-full bg-white text-black hover:bg-white/90 hover:scale-105 active:scale-95 transition-all"
                onClick={togglePlay}
                data-testid="play-pause-btn"
              >
                {isPlaying ? (
                  <Pause className="w-5 h-5" />
                ) : (
                  <Play className="w-5 h-5 ml-0.5" />
                )}
              </Button>
              
              <Button
                variant="ghost"
                size="icon"
                className="hover:bg-white/10 text-white"
                onClick={playNext}
                data-testid="next-btn"
              >
                <SkipForward className="w-5 h-5" />
              </Button>
              
              <Button
                variant="ghost"
                size="icon"
                className={`hover:bg-white/10 ${isRepeat ? 'text-indigo-400' : 'text-muted-foreground'}`}
                onClick={() => setIsRepeat(!isRepeat)}
                data-testid="repeat-btn"
              >
                <Repeat className="w-4 h-4" />
              </Button>
            </div>

            {/* Progress Bar */}
            <div className="flex items-center gap-3 w-full">
              <span className="text-xs text-muted-foreground w-10 text-right">
                {formatTime(currentTime)}
              </span>
              <Slider
                value={[duration ? (currentTime / duration) * 100 : 0]}
                onValueChange={handleSeek}
                max={100}
                step={0.1}
                className="flex-1"
                data-testid="progress-slider"
              />
              <span className="text-xs text-muted-foreground w-10">
                {formatTime(duration)}
              </span>
            </div>
          </div>

          {/* Volume */}
          <div className="flex items-center gap-3 w-1/4 justify-end">
            <Button
              variant="ghost"
              size="icon"
              className="hover:bg-white/10"
              onClick={() => setIsMuted(!isMuted)}
              data-testid="mute-btn"
            >
              {isMuted || volume === 0 ? (
                <VolumeX className="w-5 h-5 text-muted-foreground" />
              ) : (
                <Volume2 className="w-5 h-5" />
              )}
            </Button>
            <Slider
              value={[isMuted ? 0 : volume * 100]}
              onValueChange={handleVolumeChange}
              max={100}
              step={1}
              className="w-24 hidden md:flex"
              data-testid="volume-slider"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
