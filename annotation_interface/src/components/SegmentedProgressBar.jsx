import React, { useState, useEffect } from "react";

/**
 * Segmented progress bar where each segment = 5 seconds.
 * Number of segments = Math.ceil(duration / 5).
 *
 * Props:
 *   - progress: current time of the video in seconds
 *   - duration: total duration of the video in seconds
 *   - segmentColors: array of colors for each segment (e.g. ["red", "blue", ...])
 *   - barWidth: total width of the bar in px
 *   - barHeight: height of the bar in px
 */
function SegmentedProgressBar({
  progress,
  duration,
  segmentColors = [],
  barWidth = 1280,
  barHeight = 10,
}) {
  const SEGMENT_DURATION = 5;
  const numberOfSegments = Math.ceil(duration / SEGMENT_DURATION);
  const [fillColors, setFillColors] = useState([]);

  useEffect(() => {
    const updatedFillColors = Array.from({ length: numberOfSegments }).map(
      (_, i) => {
        const segmentStart = i * SEGMENT_DURATION;
        const segmentEnd = (i + 1) * SEGMENT_DURATION;

        let fillFraction = 0;
        if (progress >= segmentEnd) {
          fillFraction = 1;
        } else if (progress > segmentStart) {
          fillFraction = (progress - segmentStart) / SEGMENT_DURATION;
        }

        const segmentColor = segmentColors[i] || "#999"; // Default to #999 if undefined
        return {
          fillFraction,
          fillColor: segmentColor,
        };
      }
    );

    setFillColors(updatedFillColors);
  }, [progress, duration, segmentColors, numberOfSegments]);

  return (
    <div
      style={{
        display: "flex",
        width: `${barWidth}px`,
        height: `${barHeight}px`,
        backgroundColor: "#e0e0e0",
        marginTop: "10px",
      }}
    >
      {fillColors.map((segment, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            backgroundColor: "#e0e0e0",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${(segment.fillFraction * 100).toFixed(2)}%`,
              height: "100%",
              backgroundColor: segment.fillColor,
              transition: "width 0.3s linear, background-color 0.3s linear",
            }}
          />
        </div>
      ))}
    </div>
  );
}


export default SegmentedProgressBar;