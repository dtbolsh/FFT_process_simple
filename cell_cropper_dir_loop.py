"""
Created on Thu Dec  4 12:37:38 2025

@author: bolshakov
"""
#loop over im and mask directories and save cropped cells

import os
import sys
import subprocess
#import ast
#example call:
#python cell_cropper_dir_loop.py path/to/mask/dir path/to/fluor/dir 
#sys argv:    0                1                2                   

# Path to a Python interpreter that runs any Python script (env python)

def path_parser(generic_path):
    """input something in the form of '~/Documents/GitHub/...' """
    return os.path.abspath(os.path.expanduser(generic_path))

#path to virtual environment
generic_python_path = "~/Anaconda3/envs/basic-env/python.exe"

python_bin =  path_parser(generic_python_path)
print("python bin exists: ",os.path.exists(python_bin))
   
# Path to the script that must run under the virtualenv
generic_script_path = '~/Documents/Github/Image-process-app/pyscripts/single_cell_cropping.py'
script_file = path_parser(generic_script_path)
print("script file exists: ",os.path.exists(script_file))

mask_dir = os.path.abspath(sys.argv[1])
fluor_dir = os.path.abspath(sys.argv[2])

print("mask_dir exists ",os.path.exists(mask_dir))
print("fluor_dir exists ",os.path.exists(fluor_dir))



if (type(mask_dir) != str) | (type(fluor_dir) != str):
    print('Something wrong with script call args')
    print(mask_dir, "Type = ",type(mask_dir))
    print(fluor_dir, "Type = ",type(fluor_dir))

else:
    #generate pairs of fluorescent and mask files for processing
    fluor_contents = os.listdir(fluor_dir)
    mask_contents = os.listdir(mask_dir)
    file_pairs = []
    for f in fluor_contents:
        if (("Green" in f) or ("Red" in f)) and ("nd2" in f): #adjusting to fit files that have DIC channel in addition to fluor
            point_name = f.split("_Channel")[0] #NIS elements point loop naming convention. everything before the channel specification is the user-specified point name that is shared between fluor and dic
            print(point_name)
            mask_f = list(filter(lambda item: point_name + '_Channel' in item, mask_contents)) #needed to add the channel bit because some point names contain others (e.g. point_1 in point_1-2)
            if len(mask_f)==0:
                print(f"No mask file found for file {f}!")
                continue
            if len(mask_f) > 1:
                print(mask_f)
                print(f">1 mask file found for file {f}!")
                continue
            else:
                file_pair = [f,mask_f[0]]
                file_pairs.append(file_pair)
        #print(file_pairs)
    for file_pair in file_pairs: 
        fluor_file = os.path.join(fluor_dir,file_pair[0])
        mask_file = os.path.join(mask_dir,file_pair[1]) 
        
        #isolated subprocess that has huge RAM requirement in each iteration
        p = subprocess.Popen([python_bin,"-u",script_file, mask_file, fluor_file],
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in p.stdout:
            print("CHILD:", line, end="")
