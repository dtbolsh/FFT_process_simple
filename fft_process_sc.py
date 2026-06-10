import os
import sys
import subprocess
#import ast
#example call:
#python fft_entire_im.py path/to/single/cell/dir [signal,channels]
#sys argv:    0                1                          2

# Path to a Python interpreter that runs any Python script (env python)

def path_parser(generic_path):
    """input something in the form of '~/Documents/GitHub/...' """
    return os.path.abspath(os.path.expanduser(generic_path))

#path to virtual environment
generic_python_path = "~/Anaconda3/envs/basic-env/python.exe"

python_bin =  path_parser(generic_python_path)
   
# Path to the script that must run under the virtualenv
generic_script_path = '~/Documents/Github/Image-process-app/pyscripts/fluor_stack_process_single_cell_fft.py'
script_file = path_parser(generic_script_path)

single_cell_dir = os.path.abspath(sys.argv[1])
signal_channels = sys.argv[2]

if (type(single_cell_dir) != str) | (type(signal_channels) != str):
    print('Something wrong with script call args')
    print(single_cell_dir, "Type = ",type(single_cell_dir))
    print(signal_channels, "Type = ",type(signal_channels))

else:
    #input single cell folder for processing
    sc_dirs = os.listdir(single_cell_dir) #list folders that link back to image files. these contain masked cells and their corresponding mask
    
    for folder in sc_dirs: 
        folder_path = os.path.join(single_cell_dir,folder)
        #isolated subprocess that has huge RAM requirement in each iteration
        p = subprocess.Popen([python_bin,"-u",script_file, folder_path,signal_channels],
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in p.stdout:
            print("CHILD:", line, end="")
