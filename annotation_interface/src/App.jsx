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
// import vid5 from "./videos/videoMP4s/5.mp4";
// import vid6 from "./videos/videoMP4s/6.mp4";
// import vid7 from "./videos/videoMP4s/7.mp4";
// import vid8 from "./videos/videoMP4s/8.mp4";

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
    vid0, vid1, vid0, vid2,
    vid0, vid3, vid0, vid4,
    vid0
  ];

  // Current video index
  const [currVideoIndex, setCurrVideoIndex] = useState(0);

  // For video progress tracking
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);

  // CSV-related states
  const [csvData, setCsvData] = useState([]);  // Will hold codes from the 'Probe' column
  const [csvIndex, setCsvIndex] = useState(0); // Which row are we on across all segments/videos?
  const [segmentColors, setSegmentColors] = useState([]); // Colors for current video's segments
  const [error, setError] = useState(null); // To handle errors

  const playerRef = useRef(null);
  const previousCsvDataRef = useRef([]); // To detect changes in CSV data

  // Function to fetch and parse CSV
  const fetchAndParseCSV = () => {
    // const fileName = currVideoIndex;
    const csvFilePath = `pred.csv`;
    // console.log("Fetching CSV from:", fileName);


    Papa.parse(csvFilePath, {
      download: true,
      header: true, // Indicates that the first row contains headers
      delimiter: ',', // Specify the delimiter
      skipEmptyLines: true, // Skip empty lines in the CSV
      complete: (results) => {
        try {
          // Log the raw data from PapaParse
          console.log("Parsed CSV Data (raw):", results.data);

          const allRows = results.data;

          // Check if the 'Probe' column exists
          if (!results.meta.fields.includes('Probe')) {
            throw new Error("");
          }
          
          // Extract the 'Probe' column values and normalize to uppercase
          const extractedCodes = allRows.map((row, index) => {
            const code = row['Probe'];
            if (typeof code !== 'string') {
              console.warn(`Row ${index + 2}: 'Probe' value is not a string. Received:`, code);
              return "";
            }
            return code.trim().toUpperCase(); // Convert to uppercase
          });

          // Log the extracted codes
          console.log("Extracted codes (Probe column):", extractedCodes);

          // Check if the CSV data has changed
          const isDataChanged = JSON.stringify(extractedCodes) !== JSON.stringify(previousCsvDataRef.current);
          if (isDataChanged) {
            // Update the previous CSV data reference
            previousCsvDataRef.current = extractedCodes;

            // Update the state with the extracted codes
            setCsvData(extractedCodes);

            // Reset csvIndex if needed


            setCsvIndex(0); 


            // Removed immediate call to updateSegmentColors
            // The useEffect watching duration and csvData will handle it
          }
        } catch (parseError) {
          console.error("Error processing CSV data:", parseError);
          setError(parseError.message);
        }
      },
      error: (err) => {
        console.error("Error fetching or parsing CSV:", err);
        setError(err.message);
      },
    });
  };

  // Function to update segment colors based on csvData and current csvIndex
  const updateSegmentColors = (currentCsvData, currentIndex) => {
    const numberOfSegments = Math.ceil(duration / 5); // each segment = 5 seconds

    if (currentCsvData.length > 0 && numberOfSegments > 0) {
      // Ensure we don't exceed the csvData length
      const endIndex = Math.min(currentIndex + numberOfSegments, currentCsvData.length);
      const codesForThisVideo = currentCsvData.slice(currentIndex, endIndex);
      console.log("Codes for this video:", codesForThisVideo);

      const newSegmentColors = codesForThisVideo.map((code) => {
        return colorMap[code] || "gray";
      });

      // If there are fewer codes than segments, fill the rest with gray
      while (newSegmentColors.length < numberOfSegments) {
        newSegmentColors.push("gray");
      }

      setSegmentColors(newSegmentColors);
      setCsvIndex(endIndex);
    }
  };


  useEffect(() => {
    // Initial fetch
    fetchAndParseCSV();
    // Set up polling to fetch CSV every 5 seconds
    const intervalId = setInterval(() => {
      fetchAndParseCSV();
    }, 5000); // 5000ms = 5 seconds

    // Clean up the interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  // Whenever duration or csvData changes, update the segment colors
  useEffect(() => {
    if (csvData.length > 0 && duration > 0) {
      const Time = Date.now();

      updateSegmentColors(csvData, csvIndex);

            
      const Time2 = Date.now();
      const timeActual = (Time2- Time)*100
      console.log ("the time is",Time2- Time);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [duration, csvData]); // Trigger when either duration or csvData changes

  // When the video ends, go to next video
  const handleOnEnded = () => {
    if (currVideoIndex < orderedList.length - 1) {
      
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
    }
  };

  // Called continuously as the video plays
  const handleOnProgress = (state) => {
    setProgress(state.playedSeconds);
  };

  // Called once when the video loads to set the total duration
  // Then we slice out that many rows from our CSV array to get colors
  const handleOnDuration = (dur) => {
    setDuration(dur);
  };

  return (
    <div style={{ margin: "20px" }}>
      {error && <div style={{ color: "red" }}>Error: {error}</div>}
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