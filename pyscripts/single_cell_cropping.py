#Script to crop and save single cells for further processing
#inputs: mask file and fluorescence file.

#with some help from chatgpt
import numpy as np
import zarr
from skimage import measure
import nd2
import tifffile
import sys
import os
import pandas as pd

#example call (in venv that has above packages installed): python path/to/single_cell_cropping.py path/to/mask.tiff path/to/fluor_timeseries.nd2
#mask file needs to be 2D (for this version), but code can be adapted for timeseries mask as well.

mask_path = sys.argv[1]
mask_dir = os.path.dirname(os.path.abspath(mask_path))
img_path = sys.argv[2]
img_dir = os.path.dirname(os.path.abspath(img_path))

mask = tifffile.imread(mask_path)          # labeled mask
img  = nd2.imread(img_path)  # image to crop. Format = t,c,x,y

f = os.path.split(os.path.abspath(img_path))[1] #get just file name
short_name = f.split('_Channel')[0] #works for nikon point_loop naming convention to get unique point name

#assert mask.shape[:2] == img.shape[:2], "Mask and image must align spatially." #change so matches actual image shape

# ---------------------------------------------------------
# Create a Zarr group to store object crops
# ---------------------------------------------------------
cell_save_folder = os.path.join(img_dir,"individual_cells", short_name)
if not os.path.exists(cell_save_folder):
    os.makedirs(cell_save_folder)


store_path = "cells.zarr" 
root = zarr.open_group(os.path.join(cell_save_folder,store_path), mode="w")

store_path_mask = "masks.zarr" 
root_mask = zarr.open_group(os.path.join(cell_save_folder,store_path_mask), mode="w")

#get background fluorescence information for entire image (harder to do later when looping over individual cells)

green = img[:,0,:,:] #Verify that this is indeed the order of channels. Later, make general to allow for single-color, or more than 2 color imaging.
red = img[:,1,:,:]
print('averaging channels',flush=True)
r_mean=np.mean(red,axis=0) #time average of fluorescence
g_mean=np.mean(green,axis=0)

#obtain background - inverse of masked pixels - needed for background correction of fluorescence
im_g_bg = np.where(mask == 0, g_mean, np.nan)
im_r_bg = np.where(mask == 0, r_mean, np.nan)

#get mean and median of background
g_bg_mean = np.nanmean(im_g_bg)
g_bg_median = np.nanmedian(im_g_bg)
r_bg_mean = np.nanmean(im_r_bg)
r_bg_median = np.nanmedian(im_r_bg)    


# ---------------------------------------------------------
# Extract and store each object
# ---------------------------------------------------------

# Get properties for each labeled region
regions = measure.regionprops(mask) 
data_for_df = []
for region in regions:
    label_id = region.label

    # bounding box is (min_row, min_col, max_row, max_col)
    min_row, min_col, max_row, max_col = region.bbox

    # extract the image crop
    crop_mask = mask[min_row:max_row, min_col:max_col].copy()
    crop = img[:,:,min_row:max_row, min_col:max_col].copy()

    # write the crop to a Zarr array named by its label
    root.create_dataset(
        name=f"cell_{label_id}",
        data=crop,
        compressor=zarr.Blosc(cname="zstd", clevel=3, shuffle=1),
        chunks=True,   # let Zarr choose chunk size automatically
        overwrite=True
    )
    root_mask.create_dataset(
        name=f"cell_{label_id}",
        data=crop_mask,
        compressor=zarr.Blosc(cname="zstd", clevel=3, shuffle=1),
        chunks=True,   # let Zarr choose chunk size automatically
        overwrite=True
    )
    data_for_df.append({
            'im_short_name': short_name,
            'label': f'cell_{label_id}',
            'area': region.area,
            'centroid': region.centroid,
            'orientation': region.centroid,
            'axis_major_length': region.axis_major_length,
            'axis_minor_length': region.axis_minor_length,
            'bbox': region.bbox,
            'r_bg_mean':r_bg_mean,'r_bg_median':r_bg_median,'g_bg_mean':g_bg_mean,'g_bg_median':g_bg_median #fluorescence background of image
            }
        )
    print(f"Saved cell {label_id} and its mask as cell_{label_id} in {store_path} and {store_path_mask} respectively")
    
df_from_list = pd.DataFrame(data_for_df)
df_from_list['Filename'] = img_path
#df_from_list['Directory'] = img_dir #img_path should contain entire path, not just local name
df_from_list['Mask_name'] = mask_path
#df_from_list['Mask_dir'] = mask_dir

df_from_list.to_csv(os.path.join(cell_save_folder,'cells_metadata.csv'), index=False)
print(f"Saved image and cell metadata file to {cell_save_folder}")

print("Done!")
