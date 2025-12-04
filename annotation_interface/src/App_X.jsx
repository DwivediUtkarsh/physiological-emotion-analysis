import React, { useState, useRef, useEffect } from "react";
import ReactPlayer from "react-player";
import Papa from "papaparse"; // For parsing CSV
import FileSaver from "file-saver";

// Import your videos
import vid0 from "./videos/videoMP4s/0.mp4";
import vid1 from "./videos/videoMP4s/1.mp4";
import vid2 from "./videos/videoMP4s/2.mp4";
import vid3 from "./videos/videoMP4s/3.mp4";
import vid4 from "./videos/videoMP4s/4.mp4";
import vid5 from "./videos/videoMP4s/5.mp4";
import vid6 from "./videos/videoMP4s/6.mp4";
import vid7 from "./videos/videoMP4s/7.mp4";
import vid8 from "./videos/videoMP4s/8.mp4";

// Import our custom segmented progress bar
import SegmentedProgressBar from "./components/SegmentedProgressBar";

// Map CSV codes to colors:
// #eecdac, #7fc087, #879af0, #f4978e
const colorMap = {
  "HH": "#eecdac",
  "LH": "#f4978e",
  "LL": "#879af0",
  "HL": "#7fc087",
  // anything else should become "gray"
  "": "black"
};


export default function App() {
  // The list of all videos in the order you want to play them
  const orderedList = [
    vid5, vid0, vid3, vid0,
    vid7, vid0, vid8, vid0,
    vid1, vid0, vid2, vid0,
    vid4, vid0, vid6, vid0
  ];

  // Current video index
  const [currVideoIndex, setCurrVideoIndex] = useState(0);

  // For video progress tracking
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);

  // CSV-related states
  const [csvData, setCsvData] = useState([]);  // Will hold codes from the 18th column
  const [csvIndex, setCsvIndex] = useState(0); // Which row are we on across all segments/videos?
  const [segmentColors, setSegmentColors] = useState([]); // Colors for current video's segments

  const playerRef = useRef(null);
  // State Variable to Track Loaded Rows
  const [loadedRowCount, setLoadedRowCount] = useState(0);

  useEffect(() => {
    console.log("Starting CSV polling...");
  
    const fetchCSV = () => {
      const csvFilePath = 'alluser_allclass_median_normalized_allfeatures.csv';
  
      Papa.parse(csvFilePath, {
        download: true,
        header: true,
        delimiter: ',',
        skipEmptyLines: false,
        complete: (results) => {
          try {
            console.log("Fetched CSV Data:", results.data);
  
            const allRows = results.data;
            const totalRows = allRows.length;
  
            if (!results.meta.fields.includes('Probe')) {
              throw new Error("The 'Probe' column was not found in the CSV.");
            }
  
            // Only process the new (unloaded) rows
            const newRows = allRows.slice(loadedRowCount);
            if (newRows.length === 0) {
              console.log("No new rows to process.");
              return;
            }
  
            console.log(`Processing ${newRows.length} new rows.`);
  
            // Extract 'Probe' codes from new rows, normalizing them
            const newCodes = newRows.map((row, index) => {
              let code = row['Probe'];
  
              // If it's not even a string, treat it as empty
              if (typeof code !== 'string') {
                console.warn(
                  `Row ${loadedRowCount + index + 2}: 'Probe' value is not a string. Received:`,
                  code
                );
                code = "";
              }
  
              // Trim & make uppercase (optional, but helps consistency)
              code = code.trim().toUpperCase();
  
              // If it's empty or not recognized by colorMap, treat it as empty
              if (!code || !colorMap[code]) {
                code = ""; // So that colorMap[""] is undefined => "gray"
              }
  
              return code;
            });
  
            console.log("New extracted codes (normalized):", newCodes);
  
            // Append new codes to csvData
            setCsvData((prevData) => [...prevData, ...newCodes]);
  
            // Update the loaded row count
            setLoadedRowCount(totalRows);
          } catch (parseError) {
            console.error("Error processing CSV data:", parseError);
            // Optionally, set an error state here
          }
        },
        error: (err) => {
          console.error("Error fetching or parsing CSV:", err);
          // Optionally, set an error state here
        },
      });
    };
  
    // Initial fetch
    fetchCSV();
  
    // Poll every 5 seconds
    const intervalId = setInterval(fetchCSV, 5000);
  
    // Cleanup on unmount
    return () => clearInterval(intervalId);
  }, [loadedRowCount]);
  

  // When the video ends, go to next video
  const handleOnEnded = () => {
    if (currVideoIndex < orderedList.length - 1) {
      // const csvRows = [`start_time,video_id`]; // Add a header row
      // csvRows.push(`${startTime},${videoID}`);
      // const csvContent = csvRows.join('\n');
      // const csvBlob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      // FileSaver.saveAs(csvBlob, `start_times.csv`);

      // Get the current timestamp
      const startTime = Date.now();
    
      // Get the video ID
      const videoID = currVideoIndex;

      // Write start time and video ID to the CSV file
      const csvRow = [startTime, videoID];
      const csvData2 = new Blob([csvRow.join(',')], { type: 'text/csv;charset=utf-8;' });
      FileSaver.saveAs(csvData2, `start_times_${videoID}.csv`);

      setCurrVideoIndex((prevIndex) => prevIndex + 1);
      setProgress(0); // Reset progress for the next video
      setSegmentColors([]); // Reset segment colors for the next video
    }
  };

  // Called continuously as the video plays
  const handleOnProgress = (state) => {
    setProgress(state.playedSeconds);

    // Calculate current segment based on progress
    const currentSegment = Math.floor(state.playedSeconds / 5);

    // Check if we need to update the segment color for the current segment
    if (currentSegment < segmentColors.length && segmentColors[currentSegment] === "gray") {
      // Attempt to fetch the latest code for this segment
      const code = csvData[csvIndex + currentSegment];
      if (code) {
        const newColor = colorMap[code] || "gray";
        console.log(`Updating segment ${currentSegment} with code "${code}" to color "${newColor}"`);
        setSegmentColors((prevColors) => {
          const updatedColors = [...prevColors];
          updatedColors[currentSegment] = newColor;
          return updatedColors;
        });
      } else {
        console.log(`No code found for segment ${currentSegment}, defaulting to "gray"`);
        // Optionally, you can explicitly set it to gray, but it's already gray
      }
    }
  };

  // Called once when the video loads to set the total duration
  // Then we slice out that many rows from our CSV array to get colors
  const handleOnDuration = (dur) => {
    setDuration(dur);
    const numberOfSegments = Math.ceil(dur / 5);
  
    // Get exactly `numberOfSegments` codes for this video, 
    // or however many remain if we're short
    const codesForThisVideo = csvData.slice(csvIndex, csvIndex + numberOfSegments);
    console.log("Codes for this video:", codesForThisVideo);
  
    const newSegmentColors = codesForThisVideo.map((code) => {
      // If code was not recognized or empty, colorMap[code] => undefined => 'gray'
      return colorMap[code] || "gray";
    });
  
    // If CSV data runs out before we have enough segments,
    // fill the remaining segments with "gray"
    const needed = numberOfSegments - codesForThisVideo.length;
    for (let i = 0; i < needed; i++) {
      newSegmentColors.push("gray");
    }
  
    setSegmentColors(newSegmentColors);
    // Move your csvIndex forward by however many codes we actually used
    setCsvIndex((prevIndex) => prevIndex + codesForThisVideo.length);
  };
  

  return (
    <div style={{ margin: "20px" }}>
      <ReactPlayer
        ref={playerRef}
        url={orderedList[currVideoIndex]}
        playing={true}
        controls={true}
        onEnded={handleOnEnded}
        onProgress={handleOnProgress}
        onDuration={handleOnDuration}
        width="1280px"
        height="720px"
      />

      {/* Segmented progress bar */}
      <SegmentedProgressBar
        progress={progress}
        duration={duration}
        segmentColors={segmentColors}
        barWidth={1280}
        barHeight={10}
      />
    </div>
  );
}
