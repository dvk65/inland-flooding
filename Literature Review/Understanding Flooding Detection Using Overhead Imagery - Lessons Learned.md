### Overview:

[www.researchgate.net](https://www.researchgate.net/profile/Abdullah-Said-10/publication/347700942_Understanding_Flooding_Detection_Using_Overhead_Imagery_-_Lessons_Learned/links/6728eb2077b63d1220da5cd6/Understanding-Flooding-Detection-Using-Overhead-Imagery-Lessons-Learned.pdf)

This paper, co-authored by Dr. Philip Bogden, looks at how we can use overhead imagery and computer vision to detect flooded areas more accurately. The authors experimented with **U-Net neural networks**, a popular image segmentation model, and tried combining satellite/aerial images with **terrain data**, specifically HAND (Height Above Nearest Drainage), to improve flood detection.

### Key takeaways:

- **Manual labels matter**: Models trained on a small set of **manually labeled flood images** (from Hurricane Harvey) performed significantly better than those trained on crowd-sourced OpenStreetMap data.
- **HAND data helped in some cases**, especially to distinguish things like wet roads vs. actual flooding. But it also introduced noise when the terrain data didn’t match up well with the imagery.
- Adding HAND straight into the image input worked okay, but the paper suggests that **a better approach would be to process imagery and HAND separately**, and combine features later (like using two encoders instead of stacking them).
- They found that small, well-labeled datasets can outperform massive, noisy ones - and this was a key lesson for future work.

---

## Implications for Inland Flooding Project

What Penny’s already done aligns really well with what this paper is trying to achieve, just with a different technique.

### What we're doing right:

- **Using geospatial masks like NDWI and flowlines** is similar in spirit to how they use HAND. We’re already on the right track by enriching satellite imagery with meaningful context.
- **Visual inspection and manual filtering** of images - which Penny spent a lot of time doing - pays off. This paper confirms that clean, high-quality data trumps quantity.
- **Working with Vermont flood data from July 2023** gives us a strong foundation, just like how they used Hurricane Harvey data.

### Where we could take it further:

- Instead of K-means clustering, we could try **U-Net segmentation**, even with just 30–50 images if we can label them well. The paper shows that a small set of good training examples is enough.
- If we bring in DEM or HAND data later, we should **carefully align and pre-process** it. Or even better, use it after the main image segmentation step to refine results.
- We could explore a **dual-stream model** (one encoder for RGB, one for terrain), which they recommend as a better way to merge visual and geospatial data.
