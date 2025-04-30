// merge-geojson.js
const fs = require('fs');
const path = require('path');

// Directory containing the GeoJSON files
const dirPath = './data/img_s2_geojson/2023-07/';

let mergedGeoJson = {
  type: "FeatureCollection",
  features: []
};

// Read all GeoJSON files and merge them
fs.readdirSync(dirPath).forEach(file => {
  if (file.endsWith('.geojson')) {
    const filePath = path.join(dirPath, file);
    const geojsonData = JSON.parse(fs.readFileSync(filePath));
    mergedGeoJson.features = mergedGeoJson.features.concat(geojsonData.features);
    if (mergedGeoJson.features.length > 10000) {
      fs.writeFileSync('./data/img_s2_geojson/2023-07/merged_partial.geojson', JSON.stringify(mergedGeoJson));
      mergedGeoJson.features = []
    }
  }
});

// Write the merged output
fs.writeFileSync('./data/img_s2_geojson/2023-07/merged.geojson', JSON.stringify(mergedGeoJson));
console.log('GeoJSON files merged successfully!');