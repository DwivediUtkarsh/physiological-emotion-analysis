/**
 * Segmented Progress Bar Component
 * 
 * Displays video timeline as colored 5-second segments representing emotions.
 * Each segment changes color based on emotion predictions (HH, HL, LH, LL).
 * Progress fills dynamically as the video plays.
 */

import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface Segment {
  color: string;
  emotion?: string;
  probe?: string;
  timestamp?: number;
}

interface SegmentedProgressBarProps {
  /** Array of segment data with colors and emotion information */
  segments: Segment[];
  
  /** Current playback time in seconds */
  currentTime: number;
  
  /** Total video duration in seconds */
  duration: number;
  
  /** Additional CSS classes */
  className?: string;
  
  /** Callback when a segment is clicked */
  onSegmentClick?: (index: number) => void;
  
  /** Show legend */
  showLegend?: boolean;
  
  /** Bar height in pixels */
  barHeight?: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const SEGMENT_DURATION = 5; // Each segment represents 5 seconds

const EMOTION_LEGEND = [
  { color: '#eecdac', label: 'Happy/Excited', probe: 'HH' },
  { color: '#7fc087', label: 'Calm/Peaceful', probe: 'HL' },
  { color: '#f4978e', label: 'Anxious/Stressed', probe: 'LH' },
  { color: '#879af0', label: 'Sad/Bored', probe: 'LL' }
];

// ============================================================================
// COMPONENT
// ============================================================================

export function SegmentedProgressBar({
  segments,
  currentTime,
  duration,
  className,
  onSegmentClick,
  showLegend = true,
  barHeight = 12
}: SegmentedProgressBarProps) {
  
  // Calculate total number of segments based on video duration
  const totalSegments = useMemo(() => {
    return Math.ceil(duration / SEGMENT_DURATION);
  }, [duration]);
  
  // Calculate current segment index
  const currentSegmentIndex = useMemo(() => {
    return Math.floor(currentTime / SEGMENT_DURATION);
  }, [currentTime]);
  
  // Calculate fill percentages for each segment
  const segmentFills = useMemo(() => {
    return Array.from({ length: totalSegments }).map((_, index) => {
      const segmentStart = index * SEGMENT_DURATION;
      const segmentEnd = Math.min((index + 1) * SEGMENT_DURATION, duration);
      
      // Calculate fill percentage for this segment
      let fillFraction = 0;
      if (currentTime >= segmentEnd) {
        fillFraction = 1.0; // Fully played
      } else if (currentTime > segmentStart) {
        fillFraction = (currentTime - segmentStart) / SEGMENT_DURATION;
      }
      
      // Get segment data if available
      const segment = segments[index];
      const color = segment?.color || '#d1d5db'; // Default light gray
      const hasData = segment && segment.color !== '#d1d5db';
      
      return {
        fillFraction,
        color,
        emotion: segment?.emotion,
        probe: segment?.probe,
        hasData,
        isActive: index === currentSegmentIndex,
        segmentStart,
        segmentEnd
      };
    });
  }, [currentTime, duration, segments, totalSegments, currentSegmentIndex]);
  
  // ============================================================================
  // RENDER
  // ============================================================================
  
  return (
    <div className={cn("w-full space-y-3", className)}>
      {/* Segmented Timeline Bar */}
      <div
        className="flex w-full bg-gray-200 rounded-lg overflow-hidden shadow-sm"
        style={{ height: `${barHeight}px` }}
        role="progressbar"
        aria-valuenow={currentTime}
        aria-valuemin={0}
        aria-valuemax={duration}
        aria-label="Emotion timeline progress"
      >
        {segmentFills.map((segment, index) => (
          <div
            key={index}
            className={cn(
              "relative flex-1 bg-gray-300 transition-all duration-200",
              onSegmentClick && "cursor-pointer hover:opacity-80",
              segment.isActive && "ring-2 ring-blue-500 ring-inset z-10"
            )}
            onClick={() => onSegmentClick?.(index)}
            title={
              segment.hasData
                ? `Segment ${index + 1}: ${segment.emotion} (${segment.probe})\n` +
                  `Time: ${formatTime(segment.segmentStart)} - ${formatTime(segment.segmentEnd)}`
                : `Segment ${index + 1}: Loading prediction...\n` +
                  `Time: ${formatTime(segment.segmentStart)} - ${formatTime(segment.segmentEnd)}`
            }
          >
            {/* Filled portion of segment */}
            <div
              className="h-full transition-all duration-300 ease-linear"
              style={{
                width: `${segment.fillFraction * 100}%`,
                backgroundColor: segment.color
              }}
            />
            
            {/* Loading indicator for segments without data */}
            {!segment.hasData && segment.fillFraction > 0 && (
              <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-10">
                <div className="w-1 h-1 bg-gray-600 rounded-full animate-pulse" />
              </div>
            )}
            
            {/* Active segment indicator */}
            {segment.isActive && (
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-full">
                <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-blue-500" />
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Time labels and info */}
      <div className="flex items-center justify-between text-xs text-gray-600 px-1">
        <span className="font-mono tabular-nums">
          {formatTime(currentTime)}
        </span>
        
        <span className="text-gray-500">
          Segment {currentSegmentIndex + 1} of {totalSegments}
        </span>
        
        <span className="font-mono tabular-nums">
          {formatTime(duration)}
        </span>
      </div>
      
      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2 border-t border-gray-200">
          {EMOTION_LEGEND.map((item) => (
            <div key={item.probe} className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-sm shadow-sm"
                style={{ backgroundColor: item.color }}
                aria-label={`${item.label} color indicator`}
              />
              <span className="text-xs text-gray-700">{item.label}</span>
            </div>
          ))}
        </div>
      )}
      
      {/* Predictions status */}
      <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
        <span className="inline-flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          {segments.filter(s => s && s.color !== '#d1d5db').length} predictions loaded
        </span>
        {segments.length < totalSegments && (
          <span className="inline-flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
            Waiting for {totalSegments - segments.length} more
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Format time in MM:SS format
 * 
 * @param seconds - Time in seconds
 * @returns Formatted string (e.g., "2:31")
 */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================================================
// ADDITIONAL COMPONENTS
// ============================================================================

/**
 * Compact version of the progress bar for smaller displays
 */
export function CompactSegmentedProgressBar({
  segments,
  currentTime,
  duration,
  className
}: Pick<SegmentedProgressBarProps, 'segments' | 'currentTime' | 'duration' | 'className'>) {
  return (
    <SegmentedProgressBar
      segments={segments}
      currentTime={currentTime}
      duration={duration}
      className={className}
      showLegend={false}
      barHeight={8}
    />
  );
}

