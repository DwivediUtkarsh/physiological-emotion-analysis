import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Clock, FileVideo, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Video } from '@/types/video';

// Use Vite's import.meta.glob to get all video files
function getAllVideos(): Video[] {
  // Only mp4 files for now
  const videoFiles = import.meta.glob('@/assets/videos/*.{mp4,webm,ogg}', { eager: true, as: 'url' });
  return Object.entries(videoFiles)
    .map(([path, url]) => {
      // Extract file name from path
      const parts = path.split('/');
      const fileName = parts[parts.length - 1];
      // Extract number from filename only (e.g., "1.mp4" -> 1, "2.mp4" -> 2)
      // Match digits at the start of filename before the extension
      const match = fileName.match(/^(\d+)\./);
      const fileNumber = match ? parseInt(match[1], 10) : NaN;
      return {
        id: `video${fileNumber}`,  // Use filename number, not array index
        name: fileName,
        duration: 0, // Will be set after metadata loads
        path: url as string,
        thumbnail: '', // Optionally set a default thumbnail
        _sortOrder: fileNumber,  // For sorting
      };
    })
    .filter(v => !isNaN(v._sortOrder) && v._sortOrder > 0)  // Filter out 0.mp4 (baseline)
    .sort((a, b) => a._sortOrder - b._sortOrder)  // Sort by video number
    .map(({ _sortOrder, ...rest }) => rest);  // Remove sort helper
}

export default function VideoLibrary() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('token');
    const isAdmin = localStorage.getItem('isAdmin') === 'true';

    if (!token) {
      navigate('/login');
      return;
    }

    if (isAdmin) {
      navigate('/admin-dashboard');
      return;
    }

    setLoading(true);
    const loadedVideos = getAllVideos();
    setVideos(loadedVideos);
    setLoading(false);
  }, [navigate]);

  const handleVideoSelect = (video: Video) => {
    navigate(`/video-annotation/${video.id}`, { state: { video } });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    navigate('/login');
  };

  // Update duration and generate thumbnail after video metadata loads
  useEffect(() => {
    videos.forEach((video, idx) => {
      if ((video.duration === 0 || !video.thumbnail) && video.path) {
        const tempVideo = document.createElement('video');
        tempVideo.src = video.path;
        tempVideo.crossOrigin = 'anonymous';
        tempVideo.preload = 'auto';
        tempVideo.muted = true;
        tempVideo.onloadedmetadata = () => {
          const duration = Math.floor(tempVideo.duration);
          // Seek to 5 seconds or end if shorter
          const seekTime = duration > 5 ? 5 : Math.max(0, duration - 1);
          tempVideo.currentTime = seekTime;
        };
        tempVideo.onseeked = () => {
          // Draw frame to canvas
          const canvas = document.createElement('canvas');
          canvas.width = tempVideo.videoWidth;
          canvas.height = tempVideo.videoHeight;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);
            const thumbnailDataUrl = canvas.toDataURL('image/jpeg');
            setVideos(prev =>
              prev.map((v, i) =>
                i === idx
                  ? {
                      ...v,
                      duration: Math.floor(tempVideo.duration),
                      thumbnail: thumbnailDataUrl,
                    }
                  : v
              )
            );
          }
        };
      }
    });
  }, [videos]);

  const formatDuration = (seconds: number) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading videos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-foreground mb-2">Video Library</h1>
            <p className="text-muted-foreground text-lg">
              Select a video to start emotion annotation
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={handleLogout}
            className="border-border hover:bg-secondary"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-card border-border shadow-soft">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <FileVideo className="h-8 w-8 text-primary" />
                <div>
                  <p className="text-2xl font-bold text-foreground">{videos.length}</p>
                  <p className="text-sm text-muted-foreground">Total Videos</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-soft">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <Clock className="h-8 w-8 text-emotion-happy" />
                <div>
                  <p className="text-2xl font-bold text-foreground">
                    {Math.floor(videos.reduce((acc, video) => acc + video.duration, 0) / 60)}m
                  </p>
                  <p className="text-sm text-muted-foreground">Total Duration</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-soft">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <Play className="h-8 w-8 text-emotion-neutral" />
                <div>
                  <p className="text-2xl font-bold text-foreground">0</p>
                  <p className="text-sm text-muted-foreground">Annotated</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Video Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {videos.map((video) => (
            <Card 
              key={video.id} 
              className="group bg-card border-border shadow-soft hover:shadow-glow transition-all duration-300 cursor-pointer overflow-hidden"
              onClick={() => handleVideoSelect(video)}
            >
              <div className="relative aspect-video overflow-hidden">
                {video.thumbnail ? (
                  <img
                    src={video.thumbnail}
                    alt={video.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full bg-muted flex items-center justify-center">
                    <FileVideo className="h-12 w-12 text-muted-foreground" />
                  </div>
                )}
                
                {/* Play overlay */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                  <div className="bg-primary rounded-full p-4 transform scale-75 group-hover:scale-100 transition-transform duration-300">
                    <Play className="h-8 w-8 text-primary-foreground fill-current ml-1" />
                  </div>
                </div>

                {/* Duration badge */}
                <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                  {formatDuration(video.duration)}
                </div>
              </div>

              <CardContent className="p-4">
                <h3 className="font-semibold text-foreground mb-2 group-hover:text-primary transition-colors">
                  {video.name.replace(/\.(mp4|webm|ogg)$/i, '')}
                </h3>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>{formatDuration(video.duration)} duration</span>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleVideoSelect(video);
                    }}
                  >
                    Annotate
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {videos.length === 0 && (
          <div className="text-center py-12">
            <FileVideo className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-foreground mb-2">No videos found</h3>
            <p className="text-muted-foreground">Add some videos to get started with annotation.</p>
          </div>
        )}
      </div>
    </div>
  );
}