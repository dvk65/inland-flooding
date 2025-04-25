# A Satellite Imagery-Driven Framework for Rapid Resource Allocation in Flood Scenarios to Enhance Loss and Damage Fund Effectiveness

https://www.nature.com/articles/s41598-024-69977-1#Abs1

This study proposes a scalable, satellite-driven resource allocation framework designed to support climate disaster relief efforts, especially in response to major flooding. The system was developed to assist with timely fund distribution under the **UN COP28 Loss and Damage Fund** and was tested using the **2023 Thessaly flood in Greece**.

### Key Takeaways:

- **Satellite integration**: The framework combines **Sentinel-1 SAR** data (for flood mapping during or near the peak event) and **Sentinel-2 optical** data (for validation and NDWI computation). SAR was preferred for timeliness and cloud-penetration.
- **Thresholding techniques**: Four unsupervised methods (Otsu, Triangle, Standard Deviation, and Minimum Threshold) were tested to classify water vs. non-water pixels in SAR images. The **Standard Deviation threshold** provided the highest IoU and recall in most cases.
- **Exposure Index (EI)**: A new metric combining **flood hazard**, **building exposure**, and **population exposure** was introduced. This index enables policymakers to allocate post-disaster resources by municipality based on quantifiable spatial impact.
- **Data accessibility**: All datasets used (e.g., Sentinel imagery, Microsoft building footprints, WorldPop) are open-access, reinforcing reproducibility and adoption by low-income countries.
- **Limitations** include the temporal resolution of Sentinel-1 (12-day revisit), insufficient building attribute data (type, age), and the difficulty of SAR interpretation in dense urban areas due to surface reflectance issues.

---

## Implications for the Inland Flooding Project

### What aligns with our current approach:

- The **use of Sentinel-2 NDWI** for validating water presence matches Penny’s workflow, reinforcing the effectiveness of optical water indices.
- The **emphasis on municipal-level analysis** using open geospatial datasets (OSM boundaries, WorldPop, Microsoft buildings) parallels our Vermont-focused image analysis by region.
- Their **pixel-based flood detection approach** based on SAR pre/post-event differencing resembles Penny’s concept of comparing before-and-after flood images for improved detection.

### Where we could extend our work:

- **Explore SAR data and pixel-based change detection**: Incorporating Sentinel-1 SAR, if available, could complement Penny’s optical-only analysis—especially for cloud-obscured events.
- **Adopt a structured Exposure Index (EI)**: Integrating flood impact with building and population data could allow us to prioritize areas within Vermont more effectively, or simulate resource allocation needs.
- **Improve thresholding methodology**: Testing unsupervised segmentation methods like Standard Deviation or Triangle on water indices or SAR difference maps may yield better performance than default K-means.
- **Validation with cloud-free NDWI**: Like this study, we could incorporate cloud-filtered Sentinel-2 bands (e.g., Band 3 and 8) and compute NDWI masks to validate or refine our flood extent predictions.
- **Policy framing**: This paper’s linkage to international relief funding and climate adaptation strategy can serve as a reference point if our project expands toward community resilience or emergency planning policy research.
