# **Flood Detection in Gaofen-3 SAR Images via Fully Convolutional Networks**

https://www.mdpi.com/1424-8220/18/9/2915

This study introduces a flood detection framework that uses **SAR imagery from China’s Gaofen-3 satellite** and applies a deep learning model based on **Fully Convolutional Networks (FCN)**. It addresses the need for fast, accurate, and robust flood detection using radar imagery, which is less affected by cloud cover and lighting conditions compared to optical imagery.

### Key Takeaways:

- **Model architecture**: The authors propose a modified FCN based on VGG16, named **FCN16**, optimized for SAR image segmentation. It replaces 7×7 kernels with 3×3 ones, reducing training complexity and improving efficiency.
- **Robust to speckle noise**: Unlike many SAR-based models that require noise filtering (which may degrade image quality), this FCN-based model works directly on preprocessed but unfiltered SAR data, treating speckle noise as a form of natural data augmentation.
- **High performance**: FCN16 outperformed both the original FCN and traditional threshold-based methods (like M1), achieving **F1 scores consistently above 0.9** across multiple flood scenes with different SAR polarizations.
- **Efficiency**: The model reduced training time by over 50% compared to FCN and had much faster inference time (about 2 minutes for full-scene classification), making it suitable for near real-time applications.
- **Low data requirements**: The model performed well with as little as 10–20% of flood-positive training samples, highlighting its potential for use in data-scarce emergency situations.

---

## Implications for the Inland Flooding Project

### What aligns with our current approach:

- Penny’s project currently uses unsupervised clustering on Sentinel-2 optical imagery. While the source data type differs, the **emphasis on efficient flood segmentation and limited ground truth data** aligns well with this FCN-based approach.
- The **use of pre- and post-event SAR imagery** in this study echoes our practice of image filtering and temporal comparison, but with added robustness against cloud conditions.
- The study reinforces the importance of **keeping preprocessing minimal** and focusing on training with generalizable model architectures, a principle already present in Penny’s NDWI + K-means workflow.

### Where we could take the project further:

- **Integrate FCN or U-Net architectures**: If sufficient SAR data becomes available, we could explore adapting a lightweight FCN or U-Net model similar to FCN16 to process either SAR or NDWI inputs for flood prediction.
- **Evaluate on SAR imagery**: Sentinel-1 SAR data can be tested to replicate a similar pipeline and allow comparison with optical results, particularly useful in cases where cloud cover limits visibility.
- **Consider removing filtering**: This study shows that deep models can tolerate speckle noise. We could assess whether omitting NDWI smoothing improves detection by preserving more spatial detail.
- **Expand benchmarking metrics**: Metrics like F1 score, precision, and recall used here could be introduced into our model validation pipeline to better measure clustering performance beyond visual inspection.
- **Efficiency focus**: The low training time and good generalization suggest that even a basic FCN implementation could be used to quickly train a new model on fresh flood data with minimal labeled input, ideal for scaling Penny’s work to new flood-prone areas.
