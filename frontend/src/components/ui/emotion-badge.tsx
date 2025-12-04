import { cn } from "@/lib/utils";
import { Emotion } from "@/types/video";
import { getEmotionColor } from "@/lib/emotions";

interface EmotionBadgeProps {
  emotion: Emotion;
  className?: string;
}

export function EmotionBadge({ emotion, className }: EmotionBadgeProps) {
  const colorClass = `bg-${getEmotionColor(emotion)}`;
  
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium text-background",
        colorClass,
        className
      )}
    >
      {emotion}
    </span>
  );
}