print("Running segmentation - cellpose 3, cyto3 model")
#needs cellpose 3 environment
from cellpose import core, utils, io, models, metrics
import os
import sys
import tifffile
import time
#import tqdm #later will figure out progress bar
import nd2

# Print iterations progress

import cellpose
#print(cellpose.__version__) #this attribute does not exist in cellpose for some reason

#load files in folder specified by command line
#print(sys.argv)
folder = sys.argv[1]
folder = os.path.abspath(folder)
print(folder)
#make save folder for masks, flows, styles
dirs= ['masks']
for d in dirs:
    if not os.path.exists(os.path.join(folder,d)):
        os.makedirs(os.path.join(folder,d))

contents = os.listdir(folder)

#set model parameters
model = models.CellposeModel(gpu=False,
                            model_type = 'cyto3')
#diameter = 10
diameter = 0
# use model diameter if user diameter is 0
diameter = model.diam_labels if diameter==0 else diameter
# threshold on flow error to accept a mask (set higher to get more cells, e.g. in range from (0.1, 3.0), OR set to 0.0 to turn off so no cells discarded):
flow_threshold = 0
# threshold on cellprob output to seed cell masks (set lower to include more pixels or higher to include fewer, e.g. in range from (-6, 6)):
cellprob_threshold = 1


#contents = [r"D:\20241121_4freq_mix2\Point4mix_1_ChannelDIC_10X_Seq0001.nd2"]

l = len(contents)

for f in contents:
    start = time.time()
    #load image files. Currently, just for single-timepoint DIC image taken as part of point loop.
    if ( "dia" in f ) | ( "DIC" in f):
        print(f"loading image{f}")
        if ".tif" in f:
            im = tifffile.imread(os.path.join(folder, f))
        if ".nd2" in f:
            im = nd2.imread(os.path.join(folder,f)) # adapt similarly to other microscope file extensions
        #run model on im
        print(f"calculating mask for {f}")
        print(im.shape) #if masking on fluorescence time-series, perform indexing and/or averaging before masking
        masks, flows, styles  = model.eval([im],
                          channels=[[0,0],[0,0]],
                          diameter=diameter,
                          flow_threshold=flow_threshold,
                          cellprob_threshold=cellprob_threshold,
                          )
        #print(masks[0].shape,flows[0].shape,styles[0].shape)
        mask_name = f.split(".")[0] + "-mask.tif"
        tifffile.imwrite(os.path.join(folder,'masks',mask_name),masks[0])
    #other code if needed
    end = time.time()
    elapsed = end-start
    print(f"elapsed time = {elapsed}")