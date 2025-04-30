#!/bin/bash

# Set input and output directories
BASE_PATH="./data/img_s2"
INPUT_DIR="./data/img_s2/2023-07"
INPUT_DIR_CLOUD="./data/img_s2/2023-07_CLOUD"
INPUT_DIR_NDWI="./data/img_s2/2023-07_NDWI"
OUTPUT_DIR_INT="./data/img_s2_geojson/2023-07_INT"
OUTPUT_DIR="./data/img_s2_geojson/2023-07"
OUTPUT_DIR_CLOUD="./data/img_s2_geojson/2023-07_CLOUD"
OUTPUT_DIR_NDWI="./data/img_s2_geojson/2023-07_NDWI"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR_INT"
mkdir -p "$OUTPUT_DIR_CLOUD"
mkdir -p "$OUTPUT_DIR_NDWI"

# Loop through all .tif files in the input directory
for file in "$INPUT_DIR"/*.tif; do
    # Extract filename without extension
    filename=$(basename "$file" .tif)

    # Reproject to EPSG:4326
    gdalwarp -t_srs EPSG:4326 "$file" "$OUTPUT_DIR_INT/${filename}_4326.tif"
    rm -f "$INPUT_DIR/${filename}.tif"

    # Convert to GeoJSON
    gdal_polygonize.py "$OUTPUT_DIR_INT/${filename}_4326.tif" -f "GeoJSON" "$OUTPUT_DIR/${filename}.geojson" mask DN
    rm -f "$OUTPUT_DIR_INT/${filename}_4326.tif"

    echo "Processed: $file -> $OUTPUT_DIR/${filename}.geojson"
done
echo "2023-07 done!"

# Loop through all .tif files in the input cloud directory
for file in "$INPUT_DIR_CLOUD"/*.tif; do
    # Extract filename without extension
    filename=$(basename "$file" .tif)

    # Reproject to EPSG:4326
    gdalwarp -t_srs EPSG:4326 "$file" "$OUTPUT_DIR_INT/${filename}_4326.tif"
    rm -f "$INPUT_DIR_CLOUD/${filename}.tif"

    # Convert to GeoJSON
    gdal_polygonize.py "$OUTPUT_DIR_INT/${filename}_4326.tif" -f "GeoJSON" "$OUTPUT_DIR_CLOUD/${filename}.geojson" mask DN
    rm -f "$OUTPUT_DIR_INT/${filename}_4326.tif"

    echo "Processed: $file -> $OUTPUT_DIR_CLOUD/${filename}.geojson"
done
echo "2023-07_Cloud done!"


# Loop through all .tif files in the input cloud directory
for file in "$INPUT_DIR_NDWI"/*.tif; do
    # Extract filename without extension
    filename=$(basename "$file" .tif)
    # Reproject to EPSG:4326
    gdalwarp -t_srs EPSG:4326 "$file" "$OUTPUT_DIR_INT/${filename}_4326.tif"
    rm -f "$INPUT_DIR_NDWI/${filename}.tif"

    # Convert to GeoJSON
    gdal_polygonize.py "$OUTPUT_DIR_INT/${filename}_4326.tif" -f "GeoJSON" "$OUTPUT_DIR_NDWI/${filename}.geojson" mask DN
    rm -f "$OUTPUT_DIR_INT/${filename}_4326.tif"

    echo "Processed: $file -> $OUTPUT_DIR_NDWI/${filename}.geojson"
done
echo "2023-07_NDWI done!"
rmdir "$INPUT_DIR_NDWI"
rmdir "$INPUT_DIR_CLOUD"
rmdir "$INPUT_DIR"
rmdir "$OUTPUT_DIR_INT"
rmdir "$BASE_PATH"