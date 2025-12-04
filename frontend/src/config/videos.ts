/**
 * Video Configuration
 * 
 * Maps frontend video files to backend video IDs and provides metadata.
 * This configuration serves as the single source of truth for video information.
 */

export interface VideoConfig {
  /** Backend video ID used in API calls (1-4) */
  id: number;
  
  /** Frontend identifier used in routing */
  frontendId: string;
  
  /** Actual video file name */
  fileName: string;
  
  /** Video duration in seconds */
  duration: number;
  
  /** Duration in milliseconds (for backend API) */
  durationMs: number;
  
  /** Video type for categorization */
  type: 'baseline' | 'stimulus';
  
  /** Human-readable description */
  description: string;
  
  /** Display name for UI */
  displayName: string;
}

/**
 * Complete video configuration array
 * Matches the backend VIDEO_DURATIONS mapping
 */
export const VIDEO_CONFIG: Readonly<VideoConfig[]> = [
  {
    id: 1,
    frontendId: 'video1',
    fileName: '1.mp4',
    duration: 180,
    durationMs: 180000,
    type: 'stimulus',
    description: 'First emotional stimulus video',
    displayName: 'Video 1 (3:00)'
  },
  {
    id: 2,
    frontendId: 'video2',
    fileName: '2.mp4',
    duration: 151,
    durationMs: 151000,
    type: 'stimulus',
    description: 'Second emotional stimulus video',
    displayName: 'Video 2 (2:31)'
  },
  {
    id: 3,
    frontendId: 'video3',
    fileName: '3.mp4',
    duration: 160,
    durationMs: 160000,
    type: 'stimulus',
    description: 'Third emotional stimulus video',
    displayName: 'Video 3 (2:40)'
  },
  {
    id: 4,
    frontendId: 'video4',
    fileName: '4.mp4',
    duration: 117,
    durationMs: 117000,
    type: 'stimulus',
    description: 'Fourth emotional stimulus video',
    displayName: 'Video 4 (1:57)'
  }
] as const;

/**
 * Get backend video ID from frontend ID
 * 
 * @param frontendId - Frontend video identifier (e.g., "video1")
 * @returns Backend video ID (1-4) or 0 if not found
 * 
 * @example
 * ```ts
 * getBackendVideoId('video2') // Returns: 2
 * getBackendVideoId('invalid') // Returns: 0
 * ```
 */
export function getBackendVideoId(frontendId: string): number {
  const config = VIDEO_CONFIG.find(v => v.frontendId === frontendId);
  return config?.id || 0;
}

/**
 * Get frontend video ID from backend ID
 * 
 * @param backendId - Backend video ID (1-4)
 * @returns Frontend video identifier or null if not found
 * 
 * @example
 * ```ts
 * getFrontendVideoId(2) // Returns: 'video2'
 * getFrontendVideoId(99) // Returns: null
 * ```
 */
export function getFrontendVideoId(backendId: number): string | null {
  const config = VIDEO_CONFIG.find(v => v.id === backendId);
  return config?.frontendId || null;
}

/**
 * Get complete video configuration by frontend ID
 * 
 * @param frontendId - Frontend video identifier
 * @returns Video configuration object or undefined
 * 
 * @example
 * ```ts
 * const config = getVideoConfig('video2');
 * console.log(config?.duration); // 151
 * ```
 */
export function getVideoConfig(frontendId: string): VideoConfig | undefined {
  return VIDEO_CONFIG.find(v => v.frontendId === frontendId);
}

/**
 * Get complete video configuration by backend ID
 * 
 * @param backendId - Backend video ID
 * @returns Video configuration object or undefined
 */
export function getVideoConfigById(backendId: number): VideoConfig | undefined {
  return VIDEO_CONFIG.find(v => v.id === backendId);
}

/**
 * Check if a video ID is valid
 * 
 * @param videoId - Video ID to validate (can be frontend or backend format)
 * @returns true if valid, false otherwise
 */
export function isValidVideoId(videoId: string | number): boolean {
  if (typeof videoId === 'number') {
    return VIDEO_CONFIG.some(v => v.id === videoId);
  }
  return VIDEO_CONFIG.some(v => v.frontendId === videoId);
}

/**
 * Get all supported video IDs (backend format)
 * 
 * @returns Array of backend video IDs [1, 2, 3, 4]
 */
export function getSupportedVideoIds(): number[] {
  return VIDEO_CONFIG.map(v => v.id);
}

/**
 * Format duration for display
 * 
 * @param seconds - Duration in seconds
 * @returns Formatted string (e.g., "2:31")
 */
export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

