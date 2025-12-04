import { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { ArrowLeft, Save, RotateCcw, Loader2, Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { VideoPlayer } from '@/components/video/video-player';
import { AnnotationTimeline } from '@/components/video/annotation-timeline';
import { SegmentedProgressBar } from '@/components/video/SegmentedProgressBar';
import { Video, type VideoAnnotation, Emotion } from '@/types/video';
import { useToast } from '@/hooks/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { BackendAPI, type PredictionSegment } from '@/lib/backend-api';
import { getBackendVideoId, getVideoConfig } from '@/config/videos';

// Annotation mode type
type AnnotationMode = 'full' | 'video_only' | 'audio_only';

// Map emotion to number
const emotionToNumber = {
  Happy: 0,
  Sad: 1,
  Angry: 2,
  Neutral: 3,
};
const numberToEmotion = ['Happy', 'Sad', 'Angry', 'Neutral'];

// Generate empty annotations
const generateInitialAnnotations = (duration: number): VideoAnnotation[] => {
  const annotations: VideoAnnotation[] = [];
  for (let i = 0; i < Math.ceil(duration / 5); i++) {
    annotations.push({
      startTime: i * 5,
      endTime: Math.min((i + 1) * 5, duration),
      emotion: 'Neutral',
    });
  }
  return annotations;
};

// FastAPI backend helpers
const apiBase = 'http://localhost:8000';

async function fetchAnnotations(videoName: string, duration: number, mode: AnnotationMode = 'full'): Promise<VideoAnnotation[]> {
  const base = videoName.replace(/\.(mp4|webm|ogg)$/i, '');
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  const res = await fetch(`${apiBase}/annotations/${base}?duration=${duration}&mode=${mode}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!res.ok) throw new Error('Failed to fetch annotations');
  const data = await res.json();
  
  // Handle both admin response (object with usernames) and user response (array)
  const annotations = Array.isArray(data.annotations) ? data.annotations : data.annotations[Object.keys(data.annotations)[0]] || [];
  
  return annotations.map((annotation: number, i: number) => ({
    startTime: i * 5,
    endTime: Math.min((i + 1) * 5, duration),
    emotion: (numberToEmotion[annotation] || 'Neutral') as Emotion,
  }));
}

const saveAnnotations = async (videoName: string, duration: number, annotations: VideoAnnotation[], mode: AnnotationMode = 'full') => {
  const base = videoName.replace(/\.(mp4|webm|ogg)$/i, '');
  const arr = annotations.map(a => emotionToNumber[a.emotion]);
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Not authenticated');

  await fetch(`${apiBase}/annotations/${base}`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ video_name: base, duration, annotations: arr, mode }),
  });
};

export default function VideoAnnotation() {
  const navigate = useNavigate();
  const location = useLocation();
  const { videoId } = useParams();
  const video = location.state?.video as Video;

  // Active mode state
  const [activeMode, setActiveMode] = useState<AnnotationMode>('full');
  
  // Separate annotation arrays for each mode
  const [annotationsFull, setAnnotationsFull] = useState<VideoAnnotation[]>([]);
  const [annotationsVideoOnly, setAnnotationsVideoOnly] = useState<VideoAnnotation[]>([]);
  const [annotationsAudioOnly, setAnnotationsAudioOnly] = useState<VideoAnnotation[]>([]);
  
  // Original annotations for reset functionality
  const [originalAnnotationsFull, setOriginalAnnotationsFull] = useState<VideoAnnotation[]>([]);
  const [originalAnnotationsVideoOnly, setOriginalAnnotationsVideoOnly] = useState<VideoAnnotation[]>([]);
  const [originalAnnotationsAudioOnly, setOriginalAnnotationsAudioOnly] = useState<VideoAnnotation[]>([]);
  
  // Separate current times for each mode
  const [currentTimeFull, setCurrentTimeFull] = useState(0);
  const [currentTimeVideoOnly, setCurrentTimeVideoOnly] = useState(0);
  const [currentTimeAudioOnly, setCurrentTimeAudioOnly] = useState(0);
  
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const { toast } = useToast();
  
  // NEW: Emotion analysis API integration state
  const [predictions, setPredictions] = useState<PredictionSegment[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [processingStatus, setProcessingStatus] = useState<
    'idle' | 'starting' | 'processing' | 'completed' | 'error'
  >('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const stopPollingRef = useRef<(() => void) | null>(null);
  const hasNotifiedBackendRef = useRef(false);
  
  // NEW: Get video configuration for backend API
  const backendVideoId = videoId ? getBackendVideoId(videoId) : 0;
  const videoConfig = videoId ? getVideoConfig(videoId) : undefined;
  const userId = localStorage.getItem('username') || 'anonymous';

  useEffect(() => {
    if (!video) {
      navigate('/video-library');
      return;
    }

    // Check authentication
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    // Load annotation data for all three modes from backend
    const loadAnnotations = async () => {
      try {
        const [fullAnnotations, videoOnlyAnnotations, audioOnlyAnnotations] = await Promise.all([
          fetchAnnotations(video.name, video.duration, 'full'),
          fetchAnnotations(video.name, video.duration, 'video_only'),
          fetchAnnotations(video.name, video.duration, 'audio_only'),
        ]);
        
        setAnnotationsFull(fullAnnotations);
        setOriginalAnnotationsFull([...fullAnnotations]);
        
        // If video_only or audio_only don't exist, seed from full annotations
        const videoAnnotations = videoOnlyAnnotations.length > 0 ? videoOnlyAnnotations : [...fullAnnotations];
        const audioAnnotations = audioOnlyAnnotations.length > 0 ? audioOnlyAnnotations : [...fullAnnotations];
        
        setAnnotationsVideoOnly(videoAnnotations);
        setOriginalAnnotationsVideoOnly([...videoAnnotations]);
        
        setAnnotationsAudioOnly(audioAnnotations);
        setOriginalAnnotationsAudioOnly([...audioAnnotations]);
      } catch (error) {
        const initialAnnotations = generateInitialAnnotations(video.duration);
        
        setAnnotationsFull([...initialAnnotations]);
        setOriginalAnnotationsFull([...initialAnnotations]);
        
        setAnnotationsVideoOnly([...initialAnnotations]);
        setOriginalAnnotationsVideoOnly([...initialAnnotations]);
        
        setAnnotationsAudioOnly([...initialAnnotations]);
        setOriginalAnnotationsAudioOnly([...initialAnnotations]);
      }
    };
    loadAnnotations();
  }, [video, navigate]);

  // Helper functions to get current state based on active mode
  const getCurrentAnnotations = () => {
    switch (activeMode) {
      case 'full': return annotationsFull;
      case 'video_only': return annotationsVideoOnly;
      case 'audio_only': return annotationsAudioOnly;
      default: return annotationsFull;
    }
  };

  const getCurrentTime = () => {
    switch (activeMode) {
      case 'full': return currentTimeFull;
      case 'video_only': return currentTimeVideoOnly;
      case 'audio_only': return currentTimeAudioOnly;
      default: return currentTimeFull;
    }
  };

  const setCurrentAnnotations = (annotations: VideoAnnotation[]) => {
    switch (activeMode) {
      case 'full': setAnnotationsFull(annotations); break;
      case 'video_only': setAnnotationsVideoOnly(annotations); break;
      case 'audio_only': setAnnotationsAudioOnly(annotations); break;
    }
  };

  const handleAnnotationChange = (index: number, emotion: Emotion) => {
    const currentAnnotations = getCurrentAnnotations();
    const newAnnotations = [...currentAnnotations];
    newAnnotations[index].emotion = emotion;
    setCurrentAnnotations(newAnnotations);
    setHasChanges(true);

    toast({
      title: "Annotation Updated",
      description: `Segment ${index + 1} updated to ${emotion} (${activeMode})`,
    });
  };

  const handleVideoEnd = () => {
    setShowConfirmDialog(true);
    // NEW: Stop polling and notify backend
    handleVideoEndBackend();
  };

  const handleSave = async () => {
    try {
      const currentAnnotations = getCurrentAnnotations();
      await saveAnnotations(video.name, video.duration, currentAnnotations, activeMode);
      
      // Update the original annotations for the current mode
      switch (activeMode) {
        case 'full': setOriginalAnnotationsFull([...currentAnnotations]); break;
        case 'video_only': setOriginalAnnotationsVideoOnly([...currentAnnotations]); break;
        case 'audio_only': setOriginalAnnotationsAudioOnly([...currentAnnotations]); break;
      }
      
      setHasChanges(false);
      setShowConfirmDialog(false);
      toast({
        title: "Annotations Saved",
        description: `Saved ${currentAnnotations.length} emotion segments for ${activeMode} mode`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save annotations",
        variant: "destructive",
      });
    }
  };

  const handleSaveAll = async () => {
    try {
      await Promise.all([
        saveAnnotations(video.name, video.duration, annotationsFull, 'full'),
        saveAnnotations(video.name, video.duration, annotationsVideoOnly, 'video_only'),
        saveAnnotations(video.name, video.duration, annotationsAudioOnly, 'audio_only'),
      ]);
      
      // Update all original annotations
      setOriginalAnnotationsFull([...annotationsFull]);
      setOriginalAnnotationsVideoOnly([...annotationsVideoOnly]);
      setOriginalAnnotationsAudioOnly([...annotationsAudioOnly]);
      
      setHasChanges(false);
      setShowConfirmDialog(false);
      toast({
        title: "All Annotations Saved",
        description: "Saved annotations for all three modes",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save all annotations",
        variant: "destructive",
      });
    }
  };
  
  // =========================================================================
  // NEW: Backend API Integration Functions
  // =========================================================================
  
  /**
   * Handle video play - notify backend to start emotion analysis
   */
  const handleVideoPlayBackend = async () => {
    console.log('🎬 handleVideoPlayBackend called');
    console.log('  videoId (from URL):', videoId);
    console.log('  backendVideoId:', backendVideoId);
    console.log('  hasNotifiedBackendRef:', hasNotifiedBackendRef.current);
    console.log('  userId:', userId);
    
    // Only notify once per session
    if (hasNotifiedBackendRef.current || !backendVideoId) {
      console.log('⚠️ Skipping notification:', hasNotifiedBackendRef.current ? 'already notified' : 'invalid backendVideoId');
      return;
    }
    
    setProcessingStatus('starting');
    hasNotifiedBackendRef.current = true;
    
    try {
      console.log(`🎬 Video ${backendVideoId} started, notifying backend...`);
      
      // Notify backend
      const response = await BackendAPI.startVideo(backendVideoId, userId);
      setSessionId(response.session_id);
      setProcessingStatus('processing');
      
      console.log('✅ Backend notified successfully');
      
      // Start polling for predictions
      startPollingForPredictions();
      
      toast({
        title: "Emotion Analysis Started",
        description: "Backend is processing physiological signals",
      });
      
    } catch (error) {
      console.error('❌ Failed to notify backend:', error);
      setProcessingStatus('error');
      const message = error instanceof Error ? error.message : 'Unknown error';
      setErrorMessage(message);
      
      // Show error but don't block user from using manual annotation
      toast({
        title: "Backend Connection Failed",
        description: "You can still annotate manually",
        variant: "destructive",
      });
    }
  };
  
  /**
   * Handle video end - stop polling and notify backend
   */
  const handleVideoEndBackend = async () => {
    console.log('🎬 Video ended');
    
    // Stop polling
    if (stopPollingRef.current) {
      stopPollingRef.current();
      stopPollingRef.current = null;
    }
    
    // Notify backend (optional)
    if (sessionId && backendVideoId) {
      await BackendAPI.stopVideo(sessionId, backendVideoId);
    }
    
    setProcessingStatus('completed');
  };
  
  /**
   * Start polling for new predictions from backend
   */
  const startPollingForPredictions = () => {
    if (!backendVideoId) return;
    
    console.log('🔄 Starting prediction polling...');
    
    const stopPolling = BackendAPI.startPollingPredictions(
      backendVideoId,
      (segments) => {
        console.log(`📊 Received ${segments.length} predictions`);
        setPredictions(segments);
        
        if (segments.length > 0 && processingStatus === 'processing') {
          toast({
            title: "Predictions Updating",
            description: `${segments.length} emotion segments detected`,
          });
        }
      },
      5000, // Poll every 5 seconds
      userId // Pass userId for filtering
    );
    
    stopPollingRef.current = stopPolling;
  };
  
  // =========================================================================
  // NEW: Load Existing Predictions on Mount
  // =========================================================================
  
  useEffect(() => {
    if (!backendVideoId) return;
    
    const loadExistingPredictions = async () => {
      try {
        const segments = await BackendAPI.getVideoPredictions(backendVideoId, userId);
        if (segments.length > 0) {
          console.log(`📊 Loaded ${segments.length} existing predictions`);
          setPredictions(segments);
          setProcessingStatus('completed');
        }
      } catch (error) {
        console.error('Failed to load existing predictions:', error);
      }
    };
    
    loadExistingPredictions();
  }, [backendVideoId, userId]);
  
  // =========================================================================
  // NEW: Cleanup Polling on Unmount
  // =========================================================================
  
  useEffect(() => {
    return () => {
      if (stopPollingRef.current) {
        stopPollingRef.current();
      }
    };
  }, []);
  
  // =========================================================================
  // NEW: Prepare Segments for Progress Bar
  // =========================================================================
  
  const progressBarSegments = predictions.map(pred => ({
    color: pred.color,
    emotion: pred.emotion,
    probe: pred.probe,
    timestamp: pred.timestamp
  }));

  const handleReset = () => {
    switch (activeMode) {
      case 'full': 
        setAnnotationsFull([...originalAnnotationsFull]); 
        break;
      case 'video_only': 
        setAnnotationsVideoOnly([...originalAnnotationsVideoOnly]); 
        break;
      case 'audio_only': 
        setAnnotationsAudioOnly([...originalAnnotationsAudioOnly]); 
        break;
    }
    setHasChanges(false);
    toast({
      title: "Changes Reset",
      description: `Reverted changes for ${activeMode} mode`,
    });
  };

  const handleBack = () => {
    if (hasChanges) {
      const confirmed = window.confirm(
        "You have unsaved changes. Are you sure you want to go back?"
      );
      if (!confirmed) return;
    }
    navigate('/video-library');
  };

  if (!video) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button 
              variant="ghost" 
              onClick={handleBack}
              className="hover:bg-secondary"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Library
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-foreground">{video.name.replace(/\.(mp4|webm|ogg)$/i, '')}</h1>
              <p className="text-muted-foreground">
                Duration: {Math.floor(video.duration / 60)}:{(video.duration % 60).toString().padStart(2, '0')}
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            {hasChanges && (
              <Button 
                variant="outline" 
                onClick={handleReset}
                className="border-border hover:bg-secondary"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset {activeMode}
              </Button>
            )}
            <Button 
              onClick={() => setShowConfirmDialog(true)}
              disabled={!hasChanges}
              className="bg-gradient-primary hover:opacity-90"
            >
              <Save className="h-4 w-4 mr-2" />
              Save {activeMode}
            </Button>
            <Button 
              onClick={handleSaveAll}
              variant="outline"
              className="border-border hover:bg-secondary"
            >
              <Save className="h-4 w-4 mr-2" />
              Save All Modes
            </Button>
          </div>
        </div>

        {/* NEW: Processing Status Alerts */}
        {processingStatus === 'starting' && (
          <Alert className="mb-6">
            <Loader2 className="h-4 w-4 animate-spin" />
            <AlertDescription>
              Starting backend emotion analysis...
            </AlertDescription>
          </Alert>
        )}
        
        {processingStatus === 'processing' && (
          <Alert className="mb-6">
            <Activity className="h-4 w-4 animate-pulse" />
            <AlertDescription>
              Analyzing emotions in real-time... Predictions will appear as segments are processed.
            </AlertDescription>
          </Alert>
        )}
        
        {processingStatus === 'completed' && predictions.length > 0 && (
          <Alert className="mb-6 border-green-500 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-700">
              Emotion analysis complete! Loaded {predictions.length} prediction segments. 
              You can view them in the progress bar below or edit them manually.
            </AlertDescription>
          </Alert>
        )}
        
        {processingStatus === 'error' && (
          <Alert className="mb-6" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Backend connection failed: {errorMessage}. You can still use manual annotation.
            </AlertDescription>
          </Alert>
        )}
        
        {/* Three Mode Tabs */}
        <Tabs value={activeMode} onValueChange={(v) => setActiveMode(v as AnnotationMode)} className="mb-8">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="full">Full A/V</TabsTrigger>
            <TabsTrigger value="video_only">Video Only</TabsTrigger>
            <TabsTrigger value="audio_only">Audio Only</TabsTrigger>
          </TabsList>

          <TabsContent value="full" className="space-y-6">
            <Card className="bg-card border-border shadow-medium">
              <CardHeader>
                <CardTitle className="text-foreground">Full Audio & Video</CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <VideoPlayer
                  src={video.path}
                  onTimeUpdate={setCurrentTimeFull}
                  onPlay={handleVideoPlayBackend}
                  onEnded={handleVideoEnd}
                  className="w-full max-w-4xl mx-auto mb-6"
                />
                
                {/* NEW: Segmented Progress Bar showing emotion predictions */}
                {predictions.length > 0 && (
                  <div className="mb-6">
                    <SegmentedProgressBar
                      segments={progressBarSegments}
                      currentTime={currentTimeFull}
                      duration={video.duration}
                      showLegend={true}
                    />
                  </div>
                )}
                
                <AnnotationTimeline
                  annotations={annotationsFull}
                  duration={video.duration}
                  currentTime={currentTimeFull}
                  onAnnotationChange={handleAnnotationChange}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="video_only" className="space-y-6">
            <Card className="bg-card border-border shadow-medium">
              <CardHeader>
                <CardTitle className="text-foreground">Video Only (No Audio)</CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <VideoPlayer
                  src={video.path}
                  onTimeUpdate={setCurrentTimeVideoOnly}
                  onPlay={handleVideoPlayBackend}
                  onEnded={handleVideoEnd}
                  className="w-full max-w-4xl mx-auto mb-6"
                  forceMuted={true}
                />
                
                {/* NEW: Segmented Progress Bar showing emotion predictions */}
                {predictions.length > 0 && (
                  <div className="mb-6">
                    <SegmentedProgressBar
                      segments={progressBarSegments}
                      currentTime={currentTimeVideoOnly}
                      duration={video.duration}
                      showLegend={true}
                    />
                  </div>
                )}
                
                <AnnotationTimeline
                  annotations={annotationsVideoOnly}
                  duration={video.duration}
                  currentTime={currentTimeVideoOnly}
                  onAnnotationChange={handleAnnotationChange}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="audio_only" className="space-y-6">
            <Card className="bg-card border-border shadow-medium">
              <CardHeader>
                <CardTitle className="text-foreground">Audio Only (No Video)</CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <VideoPlayer
                  src={video.path}
                  onTimeUpdate={setCurrentTimeAudioOnly}
                  onPlay={handleVideoPlayBackend}
                  onEnded={handleVideoEnd}
                  className="w-full max-w-4xl mx-auto mb-6"
                  hideVideo={true}
                />
                
                {/* NEW: Segmented Progress Bar showing emotion predictions */}
                {predictions.length > 0 && (
                  <div className="mb-6">
                    <SegmentedProgressBar
                      segments={progressBarSegments}
                      currentTime={currentTimeAudioOnly}
                      duration={video.duration}
                      showLegend={true}
                    />
                  </div>
                )}
                
                <AnnotationTimeline
                  annotations={annotationsAudioOnly}
                  duration={video.duration}
                  currentTime={currentTimeAudioOnly}
                  onAnnotationChange={handleAnnotationChange}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Confirmation Dialog */}
        <AlertDialog open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
          <AlertDialogContent className="bg-popover border-border">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-foreground">
                Video Completed
              </AlertDialogTitle>
              <AlertDialogDescription className="text-muted-foreground">
                The video has finished playing. Are the emotion annotations correct? 
                You can still edit individual segments before saving.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="border-border hover:bg-secondary">
                Continue Editing
              </AlertDialogCancel>
              <AlertDialogAction 
                onClick={handleSave}
                className="bg-gradient-primary hover:opacity-90"
              >
                Save Annotations
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}