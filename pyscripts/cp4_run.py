print("Running segmentation - cellpose 4")
#file launched from seg_cp4_test.py, needs cellpose4-env to work.
from cellpose import models
import os
import sys
import tifffile
import time
#import tqdm #later will figure out progress bar
import nd2

# Print iterations progress


#print(cellpose.__version__) apparrently does not work

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
#contents = ['PointCdc48_KA1-2_ChannelDB-dia1_Seq0007.tif'] #testing out with just one im right now
#instantiate cellpose4 model:
model = models.CellposeModel(gpu=True) #make argument later on? GPU is basically essential for cellpose4

l = len(contents)
DIC_chan = -1 #assuming brightfield/dic is always imaged last in the point acquisition
for f in contents:
    start = time.time()
    #load image files. Currently, just for single-timepoint DIC image taken as part of point loop.
    if ( "dia"in f ) | ( "DIC" in f):
        print(f"loading image{f}")
        if ".tif" in f:
            im = tifffile.imread(os.path.join(folder, f)) #assumes 2D tiff shape x,y
        elif ".nd2" in f:
            with nd2.ND2File(os.path.join(folder, f)) as ndfile:
                arr = ndfile.to_dask()
                if len(arr.shape)>2: #arr must be in t,c,x,y shape
                    f0 = arr[0].compute() #t0
                    if len(f0.shape)>2: #multi-color image
                        im = f0[DIC_chan,:,:]
                    else:
                        im = f0.copy()
                else: #2D nd2 file
                    im = arr.compute() #load entire array into memory
        #run model on im
        print(f"calculating mask for {f}")
        print(im.shape)
        masks, flows, styles = model.eval(im)
        print(masks[0].shape,flows[0].shape,styles[0].shape)
        mask_name = f.split(".")[0] + "-mask.tif"
        tifffile.imwrite(os.path.join(folder,'masks',mask_name),masks)
    #other code if needed
    end = time.time()
    elapsed = end-start
    print(f"elapsed time = {elapsed}")