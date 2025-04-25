# Flood Detection in Urban Areas Using Satellite Imagery and Machine Learning

https://www.mdpi.com/2073-4441/14/7/1140

This paper explores the use of **Sentinel-1 SAR imagery** and **machine learning models** to detect urban flooding in San Diego. The authors tested a range of methods, including supervised classifiers like **Support Vector Machines (SVM)**, **Random Forest (RF)**, and **Maximum Likelihood Classifier (MLC)**, alongside a custom **unsupervised change detection (CD)** framework that combines **Otsu thresholding**, **fuzzy logic**, and **iso-clustering**.

### Key takeaways:

- **Unsupervised change detection performed as well as supervised models**, achieving 87% accuracy with minimal training data.
- **SAR imagery is highly effective**, especially when cloud cover affects optical imagery; it enables reliable detection during adverse weather.
- The **main challenge** in classification was confusion between floodwater and urban surfaces like pavement or rooftops, especially in RF results.
- **Using pre- and post-flood images** proved critical for identifying true flood extent and helped reduce false positives.
- The authors emphasized that **well-preprocessed inputs** and **temporal image alignment** are essential for improving classification accuracy.

---

## Implications for Inland Flooding Project

This study directly supports several aspects of our inland flooding project, while also suggesting practical ways we could evolve the current approach.

### What we're doing right:

- Penny’s use of **unsupervised K-means clustering** to detect water regions aligns well with their change detection logic, both methods are lightweight and don’t require large labeled datasets.
- Our reliance on **NDWI masks and flowline filtering** echoes their goal of adding contextual spatial information to improve accuracy.
- The **focus on manually reviewed imagery** (e.g., image curation by Penny) reflects their findings that data quality often matters more than quantity.

### Where we could take it further:

- Consider adopting a **change detection framework** using pre- and post-flood optical imagery (NDWI difference maps), even without SAR. This approach may enhance temporal analysis and limit false positives.
- If Sentinel-1 SAR becomes available for our regions of interest, it may offer robustness in cloudy conditions that Sentinel-2 lacks.
- We could try **fuzzy classification or iso-clustering** instead of K-means, building on their method that showed strong accuracy with minimal inputs.
- Similar to their method, we might test **multi-step unsupervised workflows**, like first thresholding with NDWI, followed by clustering only in suspected flood zones.
- Finally, the paper reinforces that even a small amount of **ground truth**, like road closures or flood photos, goes a long way in validating or fine-tuning our approach.
