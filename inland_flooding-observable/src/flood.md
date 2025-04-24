---
theme: dashboard
toc: false
title: Flood data
---
<!-- to make the plot span length of the window -->

# Flood data

```js
// import { from Url } from "https://cdn.skypack.dev/geotiff";
import proj4 from "proj4";
import { of, from, merge, Observable } from 'rxjs';
import { map, concatAll } from 'rxjs/operators';

// const utmLatLon = proj4("ESPG:32618", "ESPG:4326");

const us = await FileAttachment("./data/counties-10m.json").json();
const flood = await FileAttachment("./data/preprocessed.csv").csv();
// Created geojson file by using command: ogr2ogr -f "GeoJSON" Connecticut.geojson NHDFlowline.shp
const flowlineCT = await FileAttachment("./data/ShapeGeoJSON/Connecticut.geojson").json();
const flowlineMA = await FileAttachment("./data/ShapeGeoJSON/Massachusetts.geojson").json();
const flowlineNH = await FileAttachment("./data/ShapeGeoJSON/NewHampshire.geojson").json();
const flowlineVT = await FileAttachment("./data/ShapeGeoJSON/Vermont.geojson").json();

// const s2_geojson_fileList = await FileAttachment("./data/img_s2_geojson/2023-07/files.json").json();

// async function loadGeoJson(fileList) {
//   const geojsonevent = fileList.map(name => {
//     return FileAttachment(`./data/img_s2_geojson/2023-07/${name}`).json();
// });
// return Promise.all(geojsonevent);
// }
// const s2_geojsons = await loadGeoJson(s2_geojson_fileList);

// const merge_s2_geojsons = {
//   type: "FeatureCollection",
//   features: s2_geojsons.flatMap(geojson => geojson.features)
// };

// const s2_geojsons = await FileAttachment("./data/mask_cloud_latlon.geojson").json();

// const tifgeojsoncloudlatlon = {
//   type: "FeatureCollection",
//   features: tifgeojsoncloud.features.map(feature => ({
//     ...feature,
//     geometry: {
//       ...feature.geometry,
//       coordinates: feature.geometry.coordinates.map(ring =>
//         ring.map(([x, y]) => {
//           // Convert UTM to lat/lon
//           let [lon, lat] = utmLatLon.forward([x, y]);
//           return [lon, lat];
//           // Apply the transformation
//           //return [(lon / 10000), (lat / 10000) * -1];
//         })
//       )
//     }
//   }))
// };

// const geojsonFiles = await Promise.all([
//     FileAttachment("./data/img_s2_geojson/2023-07/GILN3_337_20230706T153819_20230706T155055_T18TYN_VIS.geojson").json(),
//     FileAttachment("./data/img_s2_geojson/2023-07/ASTN3_326_20230711T153821_20230711T154201_T18TYN_VIS.geojson").json(),
//     FileAttachment("./data/img_s2_geojson/2023-07/GILN3_337_20230711T153821_20230711T154201_T18TYN_VIS.geojson").json(),
//     FileAttachment("./data/img_s2_geojson/2023-07/ASTN3_326_20230706T153819_20230706T155055_T18TYN_VIS.geojson").json()
// ]);

// // Try making smaller geojsons
const geojsonFile1 = await FileAttachment("./data/img_s2_geojson/2023-07/GILN3_337_20230706T153819_20230706T155055_T18TYN_VIS.geojson").json();
const geojsonFile2 = await FileAttachment("./data/img_s2_geojson/2023-07/ASTN3_326_20230711T153821_20230711T154201_T18TYN_VIS.geojson").json();
const geojsonFile3 = await FileAttachment("./data/img_s2_geojson/2023-07/GILN3_337_20230711T153821_20230711T154201_T18TYN_VIS.geojson").json();
const geojsonFile4 = await FileAttachment("./data/img_s2_geojson/2023-07/ASTN3_326_20230706T153819_20230706T155055_T18TYN_VIS.geojson").json();

// const merged_GeoJson = await FileAttachment("./data/img_s2_geojson/2023-07/merged.geojson").json();

// const merged_GeoJson = {
//   type: "FeatureCollection",
//   features: geojsonFiles.flatMap(geojson => geojson.features)
// };

// Extracting the major rivers by filtering ftype (similar to a feature ID for rivers/major rivers/lakes) and length > 0.6km
const majorRiversCT = {
  type: "FeatureCollection",
  features: flowlineCT.features.filter(feature => 
    feature.properties.ftype == 558 && feature.properties.lengthkm >= 0.6
    )
  };

const majorRiversMA = {
  type: "FeatureCollection",
  features: flowlineMA.features.filter(feature => 
    feature.properties.ftype == 558 && feature.properties.lengthkm >= 0.6
    )
  };

const majorRiversVT = {
  type: "FeatureCollection",
  features: flowlineVT.features.filter(feature => 
    feature.properties.ftype == 558 && feature.properties.lengthkm >= 0.6
    )
  };

const majorRiversNH = {
  type: "FeatureCollection",
  features: flowlineNH.features.filter(feature => 
    feature.properties.ftype == 558 && feature.properties.lengthkm >= 0.6
    )
  };

const stateID = ["25015", "50", "25", "09"];
// Filtering only the required states from the us shape file. topojson encodes a cleaner version of the GeoJSON with the selected states
const statesforIDs = {
  type: "GeometryCollection",
  geometries: us.objects.states.geometries.filter(geo => stateID.includes(geo.id))
};
const states = topojson.feature(us, statesforIDs);

// Converting csv to geojson. FeatureCollection to collect geometry of the type point. This means lon and lat will be collected as numbers in coordinates format as required by GeoJSON
const floodgeojson = {
  type: "FeatureCollection",
  features: flood.map(event => ({
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [+event.longitude, +event.latitude],
    },
    properties:{
      state: event.state
    }
  }
  )) 
};

const statesAbbr = ['MA', 'VT', 'CT', 'NH'];
const floodGeoJSONs = {};

statesAbbr.forEach(state => {
  floodGeoJSONs[`floodgeojson${state}`] = {
    type: "FeatureCollection",
    features: flood
      .filter(event => event.state === state)
      .map(event => ({
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [+event.longitude, +event.latitude],
        },
        properties: {
          state: event.state
        }
      }))
  };
});

```

```js
import maplibregl from "npm:maplibre-gl";
//import * as turf from '@turf/turf';

const map = new maplibregl.Map({
  container: "map",
  zoom: 7,
  center: [-72.341494491472361, 43.094864061263102],
  hash: true,
  style: {
    version: 8,
    sources: {
      osm: {
        type: "raster", // image as data points
        tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "&copy; OpenStreetMap Contributors",
        maxzoom: 19
      }
    },
    layers: [
      {
        id: "osm",
        type: "raster",
        source: "osm"
      }
    ]
  },
  maxZoom: 18,
  maxPitch: 85
});

map.addControl(
  new maplibregl.NavigationControl({
    visualizePitch: true,
    showZoom: true,
    showCompass: true
  })
);

map.on("move", () => {
  const center = map.getCenter();
  document.getElementById("coordinates").innerHTML = 
  `Center: ${center.lng.toFixed(4)}, ${center.lat.toFixed(4)}`;
});

// map.on("moveend", async() => {
//   const bounds = map.getBounds();

//   if (map.getZoom() > 10) {
//     const geojson = await 
//   }
// })

// map.on("load", () => {
//         map.addSource('s2_geojson', {
//           type: "geojson",
//           data: s2_geojsons,
//         });
//         map.addLayer({
//           id: 'geojsonlayer',
//           type: "fill",
//           source: 's2_geojson',
//           paint: {
//             "fill-color": "#FF0000",
//             "fill-opacity": 0.8,
//           },
//         });
//       });

map.on("load", () => {
        //  map.addSource("geojsonFile4", {
        //    type: "geojson",
        //    data: geojsonFile4,
        //  });

        //  map.addLayer({
        //    id: "geojsonFileLayer4",
        //    type: "fill",
        //    source: "geojsonFile4",
        //    paint: {
        //      "fill-color": "#FF0000",
        //      "fill-opacity": 0.8,
        //    },
        //  });

        //  map.addSource("geojsonFile3", {
        //    type: "geojson",
        //    data: geojsonFile3,
        //  });

        //  map.addLayer({
        //    id: "geojsonFileLayer3",
        //    type: "fill",
        //    source: "geojsonFile3",
        //    paint: {
        //      "fill-color": "#FF0000",
        //      "fill-opacity": 0.8,
        //    },
        //  });

        map.addSource("geojsonFile2", {
           type: "geojson",
           data: geojsonFile2,
         });

         map.addLayer({
           id: "geojsonFile1Layer",
           type: "fill",
           source: "geojsonFile2",
           paint: {
             "fill-color": "#FF0000",
             "fill-opacity": 0.8,
           },
         });

       });

// map.on("load", () => {
//         map.addSource("merged_geojson", {
//           type: "geojson",
//           data: merged_GeoJson,
//         });

//         map.addLayer({
//           id: "mergedlayer",
//           type: "fill",
//           source: "merged_geojson",
//           paint: {
//             "fill-color": "#FF0000",
//             "fill-opacity": 0.8,
//           },
//         });
//       });
    //   Object.keys(s2_geojsons).forEach((file, index) => {
    //     const sourceID = ``
    //   })
    //   map.addSource('geojsons', {
    //     type: 'geojson',
    //     data: tifgeojsoncloud
    //   });
    //   map.addLayer({
    //   id: 'tifflayer',
    //   type: 'fill',
    //   source: 'geotiff',
    //   layout: {},
    //   paint: {
    //     'fill-color': '#088',
    //     'fill-opacity': 0.8
    //   }
    // });
    // console.log("Sources:", map.getSource('geotiff'));
    // console.log("Layers:", map.getSource('tifflayer'));
    //map.fitBounds(turf.bbox(tifgeojsoncloud), { padding: 20 });
    

function updateFLLayers(){
  // Check if MR is checked
  const showMR = document.getElementById('filterMaskMR').checked;
  if (!showMR){
    ['CT', 'MA', 'NH', 'VT'].forEach(state => {
      if (map.getLayer(`flowlineLayer${state}`)) {
        map.removeLayer(`flowlineLayer${state}`);
        map.removeSource(`flowline${state}`);
      }
    });
    return; // Exit the function early
  }

  // Check if CT is checked
  const showMRCT = document.getElementById('filterCT').checked;
    if (showMRCT) {
      if (!map.getLayer('flowlineLayerCT')) {
        map.addSource('flowlineCT', {
          type: 'geojson',
          data: majorRiversCT
        });
        map.addLayer({
          id: 'flowlineLayerCT',
          type: 'line',
          source: 'flowlineCT',
          paint: {
            'line-color': '#0000FF',
            'line-width': 2
          }
        });
      }
    } else {
      if (map.getLayer('flowlineLayerCT')) {
        map.removeLayer('flowlineLayerCT');
        map.removeSource('flowlineCT');
      }
    }

    // Check if MA is checked
    const showMRMA = document.getElementById('filterMA').checked;
    if (showMRMA) {
      if (!map.getLayer('flowlineLayerMA')) {
        map.addSource('flowlineMA', {
          type: 'geojson',
          data: majorRiversMA
        });
        map.addLayer({
          id: 'flowlineLayerMA',
          type: 'line',
          source: 'flowlineMA',
          paint: {
            'line-color': '#0000FF',
            'line-width': 2
          }
        });
      }
    } else {
      if (map.getLayer('flowlineLayerMA')) {
        map.removeLayer('flowlineLayerMA');
        map.removeSource('flowlineMA');
      }
    }

    // Check if NH is checked
    const showMRNH = document.getElementById('filterNH').checked;
    if (showMRNH) {
      if (!map.getLayer('flowlineLayerNH')) {
        map.addSource('flowlineNH', {
          type: 'geojson',
          data: majorRiversNH
        });
        map.addLayer({
          id: 'flowlineLayerNH',
          type: 'line',
          source: 'flowlineNH',
          paint: {
            'line-color': '#0000FF',
            'line-width': 2
          }
        });
      }
    } else {
      if (map.getLayer('flowlineLayerNH')) {
        map.removeLayer('flowlineLayerNH');
        map.removeSource('flowlineNH');
      }
    }

    // Check if VT is checked
    const showMRVT = document.getElementById('filterVT').checked;
    if (showMRVT) {
      if (!map.getLayer('flowlineLayerVT')) {
        map.addSource('flowlineVT', {
          type: 'geojson',
          data: majorRiversVT
        });
        map.addLayer({
          id: 'flowlineLayerVT',
          type: 'line',
          source: 'flowlineVT',
          paint: {
            'line-color': '#0000FF',
            'line-width': 2
          }
        });
      }
    } else {
      if (map.getLayer('flowlineLayerVT')) {
        map.removeLayer('flowlineLayerVT');
        map.removeSource('flowlineVT');
      }
    }
}

document.querySelectorAll('.state-filter').forEach(checkbox => {
  checkbox.addEventListener('change', updateFLLayers);
});
document.querySelectorAll('.feature-filter').forEach(checkbox => {
  checkbox.addEventListener('change', updateFLLayers);
});

function updateFPLayers(){
  // Check if MR is checked
  const showFP = document.getElementById('filterMaskFP').checked;
  if (!showFP){
    ['CT', 'MA', 'NH', 'VT'].forEach(state => {
      if (map.getLayer(`floodgeojsonLayer${state}`)) {
        map.removeLayer(`floodgeojsonLayer${state}`);
        map.removeSource(`floodGeoJSONs_floodgeojson${state}`);
      }
    });
    return; // Exit the function early
  }

  // Check if CT is checked
  const showFPCT = document.getElementById('filterCT').checked;
    if (showFPCT) {
      if (!map.getLayer('floodgeojsonLayerCT')) {
        map.addSource('floodGeoJSONs_floodgeojsonCT', {
          type: 'geojson',
          data: floodGeoJSONs.floodgeojsonCT
        });
        map.addLayer({
          id: 'floodgeojsonLayerCT',
          source: 'floodGeoJSONs_floodgeojsonCT',
          type: 'circle',
          paint: {
            'circle-radius': 4,
              'circle-color': '#FF0000',
              'circle-opacity': 0.8
          }
        });
      }
    } else {
      if (map.getLayer('floodgeojsonLayerCT')) {
        map.removeLayer('floodgeojsonLayerCT');
        map.removeSource('floodGeoJSONs_floodgeojsonCT');
      }
    }

    // Check if MA is checked
    const showFPMA = document.getElementById('filterMA').checked;
    if (showFPMA) {
      if (!map.getLayer('floodgeojsonLayerMA')) {
        map.addSource('floodGeoJSONs_floodgeojsonMA', {
          type: 'geojson',
          data: floodGeoJSONs.floodgeojsonMA
        });
        map.addLayer({
          id: 'floodgeojsonLayerMA',
          type: 'circle',
          source: 'floodGeoJSONs_floodgeojsonMA',
          paint: {
            'circle-radius': 4,
              'circle-color': '#FF0000',
              'circle-opacity': 0.8
          }
        });
      }
    } else {
      if (map.getLayer('floodgeojsonLayerMA')) {
        map.removeLayer('floodgeojsonLayerMA');
        map.removeSource('floodGeoJSONs_floodgeojsonMA');
      }
    }

    // Check if NH is checked
    const showFPNH = document.getElementById('filterNH').checked;
    if (showFPNH) {
      if (!map.getLayer('floodgeojsonLayerNH')) {
        map.addSource('floodGeoJSONs_floodgeojsonNH', {
          type: 'geojson',
          data: floodGeoJSONs.floodgeojsonNH
        });
        map.addLayer({
          id: 'floodgeojsonLayerNH',
          type: 'circle',
          source: 'floodGeoJSONs_floodgeojsonNH',
          paint: {
            'circle-radius': 4,
              'circle-color': '#FF0000',
              'circle-opacity': 0.8
          }
        });
      }
    } else {
      if (map.getLayer('floodgeojsonLayerNH')) {
        map.removeLayer('floodgeojsonLayerNH');
        map.removeSource('floodGeoJSONs_floodgeojsonNH');
      }
    }

    // Check if VT is checked
    const showFPVT = document.getElementById('filterVT').checked;
    if (showFPVT) {
      if (!map.getLayer('floodgeojsonLayerVT')) {
        map.addSource('floodGeoJSONs_floodgeojsonVT', {
          type: 'geojson',
          data: floodGeoJSONs.floodgeojsonVT
        });
        map.addLayer({
          id: 'floodgeojsonLayerVT',
          type: 'circle',
          source: 'floodGeoJSONs_floodgeojsonVT',
          paint: {
            'circle-radius': 4,
              'circle-color': '#FF0000',
              'circle-opacity': 0.8
          }
        });
      }
    } else {
      if (map.getLayer('floodgeojsonLayerVT')) {
        map.removeLayer('floodgeojsonLayerVT');
        map.removeSource('floodGeoJSONs_floodgeojsonVT');
      }
    }
}

document.querySelectorAll('.state-filter').forEach(checkbox => {
  checkbox.addEventListener('change', updateFPLayers);
});
document.querySelectorAll('.feature-filter').forEach(checkbox => {
  checkbox.addEventListener('change', updateFPLayers);
})

```

<div id="map" style="width: 100%; height: 450px;"></div>
<link rel="stylesheet" href="npm:maplibre-gl/dist/maplibre-gl.css">
<script src="https://d3js.org/d3.v6.min.js"></script>

<div id="coordinates" style="color: black; position: absolute; bottom: 150px; left: 10px; background: white; padding: 5px; border-radius: 3px; z-index: 1;">
  Center: Loading...
</div>

<div id="filter">
<h3>States:</h3>
<label><input type="checkbox" class="state-filter" id="filterMA" value="25" checked > Massachusetts </label>
<label><input type="checkbox" class="state-filter" id="filterVT" value="50" checked > Vermont </label>
<label><input type="checkbox" class="state-filter" id="filterNH" value="25015" checked > New Hampshire </label>
<label><input type="checkbox" class="state-filter" id="filterCT" value="09" checked > Connecticut </label>

<h4>Masks:</h4>
<label><input type="checkbox" class="feature-filter" id="filterMaskFP" checked> Flood Points</label>
<label><input type="checkbox" class="feature-filter" id="filterMaskMR" checked> Major Rivers</label>
</div>