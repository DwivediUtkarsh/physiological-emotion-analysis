// Import required modules
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

// Define the path to the CSV file
const csvFilePath = path.join(__dirname, 'alluser_allclass_median_normalized_allfeatures.csv');

// Initialize an empty array to store Probe values
const extractedCodes = [];

// Create a readable stream and pipe it to the CSV parser
fs.createReadStream(csvFilePath)
  .pipe(csv({ separator: '\t' })) // Assuming the CSV is tab-separated. Change if necessary.
  .on('data', (row) => {
    // Check if the 'Probe' column exists in the current row
    if ('Probe' in row) {
      extractedCodes.push(row['Probe']);
    } else {
      console.warn('Probe column not found in row:', row);
    }
  })
  .on('end', () => {
    console.log('CSV file successfully processed.');
    console.log('Extracted Probe Codes:', extractedCodes);
    
    // You can now use the extractedCodes array as needed
    // For example, you might want to write it to a new file:
    /*
    fs.writeFile('extractedProbeCodes.json', JSON.stringify(extractedCodes, null, 2), (err) => {
      if (err) throw err;
      console.log('Probe codes have been saved to extractedProbeCodes.json');
    });
    */
  })
  .on('error', (err) => {
    console.error('An error occurred while reading the CSV file:', err);
  });
