import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { VideoAnnotation, Emotion } from '@/types/video';
import { EMOTIONS, getEmotionColor, getEmotionGradient } from '@/lib/emotions';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';

interface AnnotationTimelineProps {
  annotations: VideoAnnotation[];
  duration: number;
  currentTime: number;
  onAnnotationChange: (index: number, emotion: Emotion) => void;
  className?: string;
}

export function AnnotationTimeline({
  annotations,
  duration,
  currentTime,
  onAnnotationChange,
  className
}: AnnotationTimelineProps) {
  const [activeSegment, setActiveSegment] = useState<number | null>(null);
  const [filterEmotion, setFilterEmotion] = useState<Emotion | 'All'>('All');

  const visibleAnnotations = filterEmotion === 'All'
    ? annotations
    : annotations.filter((a) => a.emotion === filterEmotion);

  const handleEmotionChange = (originalIndex: number, emotion: Emotion) => {
    onAnnotationChange(originalIndex, emotion);
    setActiveSegment(null);
  };

  const progressPercentage = duration ? (currentTime / duration) * 100 : 0;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Timeline header */}
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg font-semibold text-foreground">Event Timeline</h3>
        <div className="flex items-center gap-4">
          <div className="text-sm text-muted-foreground hidden sm:block">
            {visibleAnnotations.length}/{annotations.length} segments • 5s each
          </div>
          <div className="w-40">
            <Select value={filterEmotion} onValueChange={(v) => setFilterEmotion(v as Emotion | 'All')}>
              <SelectTrigger>
                <SelectValue placeholder="Filter emotions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All emotions</SelectItem>
                {EMOTIONS.map((e) => (
                  <SelectItem key={e} value={e}>{e}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Color-coded event timeline bar */}
      <div className="relative h-2 rounded-full overflow-hidden flex">
        {annotations.map((annotation, idx) => {
          let barClass = '';
          switch (annotation.emotion) {
            case 'Happy':
              barClass = 'bg-green-500';
              break;
            case 'Sad':
              barClass = 'bg-blue-500';
              break;
            case 'Angry':
              barClass = 'bg-red-500';
              break;
            case 'Neutral':
              barClass = 'bg-gray-600';
              break;
            default:
              barClass = 'bg-gray-600';
          }
          return (
            <div
              key={idx}
              className={barClass}
              style={{ flex: 1 }}
            />
          );
        })}
        {/* Progress overlay */}
        <div
          className="absolute top-0 left-0 h-full bg-black/20 pointer-events-none"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>

      {/* Annotation segments */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-2">
        {visibleAnnotations.map((annotation) => {
          const originalIndex = annotations.indexOf(annotation);
          const isActive = currentTime >= annotation.startTime && currentTime < annotation.endTime;
          // Explicit Tailwind color classes
          const emotionBgClass = {
            Happy: 'bg-green-500',
            Sad: 'bg-blue-500',
            Angry: 'bg-red-500',
            Neutral: 'bg-gray-600',
          }[annotation.emotion];
          const emotionBorderClass = {
            Happy: 'border-green-500',
            Sad: 'border-blue-500',
            Angry: 'border-red-500',
            Neutral: 'border-gray-600',
          }[annotation.emotion];
          return (
            <DropdownMenu key={originalIndex} open={activeSegment === originalIndex} onOpenChange={(open) => setActiveSegment(open ? originalIndex : null)}>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "relative h-16 p-2 border-2 transition-all duration-300 overflow-hidden group text-white",
                    emotionBgClass,
                    emotionBorderClass,
                    isActive && "ring-2 ring-primary ring-offset-2 ring-offset-background scale-105",
                    "hover:scale-105 hover:shadow-glow"
                  )}
                >
                  <div className="flex flex-col items-center justify-center space-y-1 relative z-10">
                    <div className="text-xs font-medium text-white/90">
                      {annotation.startTime}s-{annotation.endTime}s
                    </div>
                    <div className="text-xs font-bold text-white">
                      {annotation.emotion}
                    </div>
                  </div>
                  <ChevronDown className="absolute bottom-1 right-1 h-3 w-3 text-white/70" />
                  {/* Hover effect */}
                  <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-40 bg-popover border border-border shadow-medium">
                <div className="p-2">
                  <div className="text-xs font-medium text-muted-foreground mb-2">
                    Select emotion:
                  </div>
                  {EMOTIONS.map((emotion) => {
                    const menuBgClass = {
                      Happy: 'bg-green-500',
                      Sad: 'bg-blue-500',
                      Angry: 'bg-red-500',
                      Neutral: 'bg-gray-600',
                    }[emotion];
                    return (
                      <DropdownMenuItem
                        key={emotion}
                        onClick={() => handleEmotionChange(originalIndex, emotion)}
                        className={cn(
                          "flex items-center gap-2 cursor-pointer rounded px-2 py-1 hover:bg-accent",
                          annotation.emotion === emotion && "bg-accent"
                        )}
                      >
                        <div
                          className={cn(
                            "w-3 h-3 rounded-full",
                            menuBgClass
                          )}
                        />
                        <span className="text-sm">{emotion}</span>
                      </DropdownMenuItem>
                    );
                  })}
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 pt-4 border-t border-border">
        <div className="text-sm font-medium text-muted-foreground">Emotions:</div>
        {EMOTIONS.map((emotion) => (
          <div key={emotion} className="flex items-center gap-2">
            <div
              className={cn(
                "w-4 h-4 rounded",
                `bg-${getEmotionColor(emotion)}`
              )}
            />
            <span className="text-sm text-foreground">{emotion}</span>
          </div>
        ))}
      </div>
    </div>
  );
}