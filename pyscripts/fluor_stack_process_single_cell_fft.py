""" Code to iterate over a directory and provide comprehensive information on the cellular level, including:
    - mean fluorescence in each channel,
    - Oscillation information as quantified by FFT (torch)
    inputs: single_cell_folder, signal_channels (list like [0,1] or [0])
    outputs: dataframe of single cells in a given image
"""
#import modules
import numpy as np
import sys
import os
import ast
#from scipy import ndimage
import pandas as pd
#import tifffile

import time
#import nd2
#from skimage.measure import label, regionprops, regionprops_table

import torch
import zarr

########## Define important functions ##########

def detrend_timeseries(Y):
    start_time = time.time()
    T, H, W = Y.shape
    
    #make the time-axis to use in the fit
    t = torch.arange(T, dtype=Y.dtype, device=Y.device) #offers option for on-GPU is you have your array there
    
    # Compute sums for computing the coefficients
    sum_t = t.sum()
    sum_t2 = (t ** 2).sum()
    n = T
    
    sum_y = Y.sum(dim=0)
    sum_ty = (Y * t.view(-1, 1, 1)).sum(dim=0)
    
    # Compute coefficients a (slope) and b (intercept)
    denominator = sum_t2 - (sum_t ** 2) / n
    a = (sum_ty - (sum_t * sum_y) / n) / denominator
    b = (sum_y - a * sum_t) / n
    
    # Calculate and subtract the trend
    trend = a.unsqueeze(0) * t.view(-1, 1, 1) + b.unsqueeze(0)
    print("--- %s seconds ---" % (time.time() - start_time))
    del t, sum_t, sum_t2, n, sum_y, sum_ty, denominator, a, b
    return Y - trend

def fft_process(c_im):

    """takes a single-channel timeseries input and outputs power spectrum"""
    print('FFT analysis...',flush=True) # replacing with torch fft process
    c_im_torch = torch.from_numpy(c_im.astype('float32'))
    del c_im
    c_im_c=detrend_timeseries(c_im_torch) #get polynomial correction
    del c_im_torch
    
    img_fft=torch.abs(torch.fft.rfft(c_im_c,axis=0)).detach().numpy() #this should be a 32 bit float w/ no. of frequency slices in half (i.e. only the positive half of the PS)
    del c_im_c
    ps=np.abs(img_fft) #apply FFT along the time axis and collect the frequency (bin) and power (intensity).
    del img_fft #clear memory
    return ps

def get_image_red_green_data(im_zarr,mask_zarr,signal_channels): #change to im and mask zarrs containing individual cells

    """returns all important info from image on a single-cell level. 
    inputs: locations of zar files for fluorescent images (format t,c,x,y) and their corresponding masks (x,y)
        signal_channels (list of channel indeces containing data to process with FFT (e.g. [0] or [0,1])).
        This last argument to be passed in through the terminal sys_args."""
    



    cells_dat = []
    print('generating dataframe for image and saving cells',flush=True)
    
    store_mask = zarr.open(mask_zarr, mode='r')
    store_fluor = zarr.open(im_zarr, mode='r')
    
    keys = list(store_fluor.keys()) #later, add check for same length of store_mask and store_fluor
    for key in keys: #iterate over labeled mask
        i = int(key.split('_')[-1]) #get cell number as int
        print(key,'   ', i)
        
        #load im and mask into memory, keys should be identical
        im = store_fluor[key][:]
        mask = store_mask[key][:]
        
        
        #print('fluorescence analysis',flush=True)
        green = im[:,0,:,:] #Verify that this is indeed the order of channels. Later, make general to allow for single-color, or more than 2 color imaging.
        red = im[:,1,:,:]
        #print('averaging channels and looping over cells',flush=True)
        r_mean=np.mean(red,axis=0) #time average of fluorescence
        g_mean=np.mean(green,axis=0)
    
        mask_cell = np.where(mask == i,1,np.nan) #array to grab single cell (mask image could have bits of neighboring cells)
        #probably don't need the _masked arrays here with this strategy, but it shouldn't hurt
        cell_r = np.nanmean(r_mean*mask_cell)
        cell_g = np.nanmean(g_mean*mask_cell)
        
        
        #frequency information
        freqs = []
        amps = []
        norm_amps = []
        for s in signal_channels:
            im_c = im[:,s,:,:]
            ps = fft_process(im_c)
            #ps_norm = ps/np.sum(ps,axis=0) #later, include line to allow saving of ps_norm to tiff files
            #print('calculating power and freq...',flush=True)
            img_sum_power = np.sum(ps,axis=0)
            img_power = np.max(ps,axis=0) #gets absolute amplitude of wave
            img_norm_power=np.max(ps,axis=0)/img_sum_power #Normalizes amplitude of pixels between 0 and 1
            img_freq=np.argmax(ps,axis=0) # x (freq) at which y (amplitude) is highest - peak freq of region
            #del img_sum_power, ps, im_c #clear up memory before dumping results to lists
            freqs.append(img_freq)
            amps.append(img_power)
            norm_amps.append(img_norm_power)
            #del img_freq,img_norm_power,img_power #clear up mem again
        
        
        
        c_freq = [np.nanmedian(freq*mask_cell) for freq in freqs] 
        c_freq_var = [np.nanvar(freq*mask_cell) for freq in freqs] #within-cell freq noise to determine oscillation state
        c_amp = [np.nanmean(amp*mask_cell) for amp in amps]
        c_norm_amp = [np.nanmean(norm_amp*mask_cell) for norm_amp in norm_amps]

        #save individual cell as tiff file #commented for now, include as option later? I basically never use this, but it could be useful for odd morphologies...
        # cell_raw = im[:,:,y_min:y_max,x_min:x_max]
        # cell_raw_path = cell_repo + "\\cell_{}.tiff".format(i)
        # tifffile.imwrite(cell_raw_path,cell_raw,imagej=True)
        # del cell_raw
        #make dictionaries from data and make pd dataframe
        data_dict = {'label':key,'Red':cell_r,'Green':cell_g} #generic fluor dict
        #add oscillation information
        colors = ['green','red']
        for s in signal_channels:
            data_dict[colors[s]+'_freq_bin'] = c_freq[s]
            data_dict[colors[s]+'_freq_var'] = c_freq_var[s]
            data_dict[colors[s]+'_amp'] = c_amp[s]
            data_dict[colors[s]+'_norm_amp'] = c_norm_amp[s]
        dl = {key: [value] for key, value in data_dict.items()}
        d = pd.DataFrame.from_dict(dl)
        
        cells_dat.append(d)
        #del row, y_min, y_max, x_min, x_max, mask_cell, cell_r, cell_g, c_freq, c_freq_var, c_amp, c_norm_amp, data_dict, colors, dl


    df = pd.concat(cells_dat) #make one large dataframe with named columns
    df1 = df.reset_index(drop=True)
    #df_1 = pd.merge(p,df1,left_index = True,right_index = True) #merge with cell shape and location dataframe
    
    #del im, mask, df, df1, cells_dat #clear up RAM
    
    #generate frequency color-code images
    #print('generating frequency color-coded images') implement later? or just make separate functionality from saved power spectra
    #c_ps = temporalColorCode(ps[3:15])
    #c_ps_norm = temporalColorCode(ps_norm[3:15]) #note that the first ones run on 6/27/24 had a broader range of bins to color
    
    #del ps, ps_norm

    return df1

###########################

#scipt call to just include path to "individual cells" folder (sys.argv[1]) and signal_channels (sys.argv[2])
cells_loc = os.path.abspath(sys.argv[1])
print(cells_loc)
metadata_df_path = os.path.abspath(
    os.path.join(cells_loc,'cells_metadata.csv'))
p = pd.read_csv(metadata_df_path)


mask_zarr = os.path.join(cells_loc,'masks.zarr')
im_zarr = os.path.join(cells_loc,'cells.zarr')

signal_channels = ast.literal_eval(sys.argv[2]) #in the form of [0] or [0,1] etc

#image = nd2.imread(fluor_file) #later, make generic to allow tif files here as well
#mask = tifffile.imread(mask_file)
print("--------------------------Analyzing {} file-------------------------".format(cells_loc),flush=True)


df_fov = get_image_red_green_data(im_zarr,mask_zarr,signal_channels)

df_fov['fov'] = 0
#df_fov['Filename'] = fluor_file
#df_fov['Directory'] = fluor_dir
#df_fov['Mask_name'] = mask_file
#df_fov['Mask_dir'] = mask_dir
df_1 = pd.merge(p,df_fov,on = 'label') #merge with cell shape and location dataframe

#tifffile.imwrite(save_fd + "\\masks\\" + "adaptive_mask_{}_{}.tiff".format(d,f),results[1]) # Code for saving the mask for each fov for troubleshooting purposes
#tifffile.imwrite(save_fd + "\\freq_color\\un-normed\\" + "FFT_fov_{}_{}.tiff".format(d,f),results[2])
#tifffile.imwrite(save_fd + "\\freq_color\\normed\\" + "FFT_fov_{}_{}.tiff".format(d,f),results[3])
parent_dir, short_name = os.path.split(cells_loc)
paparent_dir = os.path.split(parent_dir)[0]
results_folder = os.path.join(paparent_dir,"results_dfs_sc")
if not os.path.exists(results_folder):
    os.makedirs(results_folder)
df_path = os.path.join(results_folder, "df_{}.csv".format(short_name))
df_1.to_csv(df_path)

print('Done!')

