export type Emotion = 'Happy' | 'Sad' | 'Angry' | 'Neutral';

export interface VideoAnnotation {
  startTime: number;
  endTime: number;
  emotion: Emotion;
}

export interface Video {
  id: string;
  name: string;
  duration: number;
  thumbnail?: string;
  path: string;
}

export interface AnnotationData {
  videoId: string;
  annotations: VideoAnnotation[];
}