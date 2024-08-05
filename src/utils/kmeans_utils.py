import os
import json
import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
from utils import global_utils
import matplotlib.pyplot as plt
from shapely.affinity import rotate
from shapely.geometry import box, LineString
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from rasterio.features import geometry_mask
from sklearn.preprocessing import StandardScaler
from matplotlib.colors import Normalize, ListedColormap

def read_tif(file_path):
    """
    Read a TIFF file and return its data and profile information.

    Args:
        file_path (str) : The path to the TIFF file to be read.

    Returns:
        data (numpy.ndarray): The image data read from the TIFF file.
        profile (dict): Metadata and profile information of the TIFF file.
    """
    with rasterio.open(file_path) as src:
        return src.read(), src.bounds, src.crs, src.transform, src.profile

def apply_cloud_mask(image, cloud_mask):
    """
    Apply a cloud mask to the specified image by setting the masked areas to NaN.

    Args:
        image (numpy.ndarray): The input image data
        cloud_mask (numpy.ndarray): The cloud mask to be applied
    
    Returns:
        numpy.ndarray: The image with cloud-masked areas set to NaN
    """
    if cloud_mask.ndim == 2:
        cloud_mask = np.expand_dims(cloud_mask, axis=0)
    masked_image = image.copy().astype(np.float32)
    masked_image[:, cloud_mask[0] == 1] = np.nan
    return masked_image

def generate_flowline_mask(flowline_gdf, image_shape, transform):
    mask = geometry_mask([geometry for geometry in flowline_gdf.geometry],
                         out_shape=image_shape,
                         transform=transform,
                         invert=True)  
    return mask.astype(np.float32)

# def draw_perpendicular_lines(flowline_mask, interval=5):
#     flowline_coords = np.column_stack(np.nonzero(flowline_mask))
#     perpendicular_lines = []
#     for i in range(0, len(flowline_coords), interval):
#         if i + 1 < len(flowline_coords):
#             p1 = flowline_coords[i]
#             p2 = flowline_coords[i + 1]
#             line = LineString([p1, p2])
#             perp_line = rotate(line, 90, origin=p1)
#             perpendicular_lines.append(perp_line)
#     return perpendicular_lines

def add_image_data(df):
    '''
    Add the image data and save to df
    '''
    global_utils.print_func_header('add the image data')
    ndwi_mask_list = []
    cloud_mask_list = []
    sat_image_list = []
    masked_image_list = []
    gdf_mask_list = []
    area_abbr_list = global_utils.area_abbr_list

    for _, row in df.iterrows():
        state = row['state']
        state_full = [name for name, abbr in area_abbr_list.items() if abbr == state][0]
        shp_path = f'data/nhd/{state_full}/Shape/NHDFlowline.shp'
        gdf = gpd.read_file(shp_path)
        image_path = os.path.join(row['dir'], row['filename'])
        ndwi_path = os.path.join(row['dir_ndwi'], row['filename_ndwi'])
        cloud_path = os.path.join(row['dir_cloud'], row['filename_cloud'])
        sat_image, bounds, tiff_crs, transform, _  = read_tif(image_path)
        ndwi_mask, _, _, _, _ = read_tif(ndwi_path)
        cloud_mask, _, _, _, _ = read_tif(cloud_path)
        cloud_mask = cloud_mask[0]
        ndwi_mask = apply_cloud_mask(ndwi_mask, cloud_mask)
        masked_image = apply_cloud_mask(sat_image, cloud_mask)

        if gdf.crs != tiff_crs:
            gdf = gdf.to_crs(tiff_crs)

        bbox = box(bounds.left, bounds.bottom, bounds.right, bounds.top)
        filtered_gdf = gdf[gdf.geometry.intersects(bbox)]
        flowline_mask = generate_flowline_mask(filtered_gdf, sat_image.shape[1:], transform)

        pixel_size = np.mean([transform.a, transform.e])
        perpendicular_lines = draw_perpendicular_lines(flowline_mask, pixel_size)

        ndwi_mask_list.append(ndwi_mask)
        cloud_mask_list.append(cloud_mask)
        sat_image_list.append(sat_image)
        masked_image_list.append(masked_image)
        gdf_mask_list.append(flowline_mask)

    df['ndwi_mask'] = ndwi_mask_list
    df['cloud_mask'] = cloud_mask_list
    df['sat_image'] = sat_image_list
    df['masked_image'] = masked_image_list
    df['gdf_mask'] = gdf_mask_list

    global_utils.describe_df(df, 'df with standardized image data')

    # print the first row
    print('\nprint out the first row for inspection\n', df.iloc[0])
    return df

def preprocess_data(df):
    global_utils.print_func_header('preprocess the image data')
    scaled_image = []
    for index, row in df.iterrows():
        image = row['masked_image']
        reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])
        valid_pixels = ~np.isnan(reshaped_image).any(axis=1)
        valid_data = reshaped_image[valid_pixels]

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(valid_data)
        pca = PCA(n_components=0.90)
        scaled_data = pca.fit_transform(scaled_data)

        pca_image = np.full((reshaped_image.shape[0], scaled_data.shape[1]), np.nan)
        pca_image[valid_pixels] = scaled_data
        pca_image = pca_image.reshape(image.shape[1], image.shape[2], -1).transpose(2, 0, 1)
        scaled_image.append(pca_image)
    df['scaled_image'] = scaled_image

    # print the first row
    print('\nprint out the first row for inspection\n', df.iloc[0])

    array_columns = ['ndwi_mask', 'cloud_mask', 'sat_image', 'masked_image', 'gdf_mask', 'scaled_image']
    for col in array_columns:
        df[col] = df[col].apply(lambda x: json.dumps(x.tolist()))

    df.to_csv('data/kmeans_ready.csv', index=False)

    return df

def kmeans_clustering(image, init, n_clusters, condition):
    """
    Perform KMeans clustering on the specified image data.

    Args:
        image (numpy.ndarray): The input image data
        n_clusters (int): The number of clusters for KMeans
        condition (str): Condition 

    Returns:
        numpy.ndarray: The clustered image
        float: The inertia of the clustering result
    """
    reshaped_image = image.transpose(1, 2, 0).reshape(-1, image.shape[0])
    valid_pixels = ~np.isnan(reshaped_image).any(axis=1)
    valid_data = reshaped_image[valid_pixels]

    kmeans = KMeans(n_clusters=n_clusters, init=init, n_init='auto', max_iter=300, random_state=42).fit(valid_data)
    inertia = kmeans.inertia_
    # assign labels to valid pixels
    labels = np.full(reshaped_image.shape[0], -1)
    labels[valid_pixels] = kmeans.labels_

    # reshape labels
    clustered_image = labels.reshape(image.shape[1], image.shape[2])

    return clustered_image, inertia

def kmeans_clustering_default(df, init, n_clusters, condition):
    """
    Perform KMeans clustering on the image datasets.

    Args:
        df (pd.DataFrame): The dataset with file paths and other metadata for images
        n_clusters (int): The number of clusters for KMeans clustering
        condition (str): Condition to determine the clustering approach ('default', 'optimized', 'optimizing')
    """
    global_utils.print_func_header('run default KMeans clustering')
    ids = df['id'].unique()
    clustered_image_list = []
    for current_id in ids:
        id_group = df[df['id'] == current_id] 
        num_images = len(id_group)
        fig, axes = plt.subplots(num_images, 3 + n_clusters, figsize=(15, 5 * num_images))
        fig.suptitle(f'KMeans Clustering for ID: {current_id}', fontsize=16)
        if num_images == 1:
            axes = np.array([axes])
        for i, (index, row) in enumerate(id_group.iterrows()):
            scaled_image = row['scaled_image']
            sat_image = row['sat_image']
            ndwi_mask = row['ndwi_mask']
            clustered_image, _ = kmeans_clustering(scaled_image, init, n_clusters, condition)
            clustered_image_list.append(clustered_image)
            cmap = plt.cm.viridis
            cmap.set_bad(color='black')

            axes[i, 0].set_title(f"{row['period']} Original")
            axes[i, 0].imshow(sat_image.transpose(1, 2, 0))

            axes[i, 1].set_title(f"{row['period']} NDWI")
            axes[i, 1].imshow(np.ma.masked_invalid(np.squeeze(ndwi_mask)), cmap=cmap)

            axes[i, 2].set_title(f"{row['period']} KMeans")
            axes[i, 2].imshow(np.ma.masked_invalid(clustered_image), cmap=cmap)

            for j in range(n_clusters):
                cluster_mask = (clustered_image == j)
                cluster_image = np.zeros_like(clustered_image, dtype=float)
                cluster_image[cluster_mask] = 1  
                cmap_cluster = ListedColormap(['black', 'white']) 
                axes[i, j + 3].set_title(f"{row['period']} Cluster {j}")
                axes[i, j + 3].imshow(cluster_image, cmap=cmap_cluster, norm=Normalize(vmin=0, vmax=1))

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        plt.savefig(f"figs/kmeans_default/{row['id']}_s2_default.png")
        plt.close(fig)

        print(f'complete - KMeans clustering on {current_id}')
    df['clustered_image'] = clustered_image_list

    return df

def select_n_clusters(df, init, condition):
    """
    Perform KMeans clustering on the image datasets to find the optimal number of clusters.
    """
    global_utils.print_func_header('identify the optimal number of clusters')
    cluster_list = [2, 3, 4, 5, 6]
    inertia_result = []
    clustered_images = []

    test_image = df['scaled_image']
    for i in cluster_list:
        print(f'current - {i}')
        clustered_image, inertia = kmeans_clustering(test_image, init, i, condition=condition)
        inertia_result.append(inertia)
        clustered_images.append(clustered_image)

    plt.figure(figsize=(10, 6))
    plt.plot(cluster_list, inertia_result, marker='o', linestyle='--')
    plt.title('Elbow Method')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.savefig(f'figs/kmeans_optimizing/elbow_plot.png')
    plt.close()