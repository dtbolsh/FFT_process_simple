import os
import sys
import subprocess

def path_parser(generic_path):
    """input something in the form of '~/Documents/GitHub/...' """
    return os.path.abspath(os.path.expanduser(generic_path))

# Path to a Python interpreter that runs any Python script
python_bin =  path_parser("~/Anaconda3/envs/cellpose4/python.exe")
print("python bin exists: ",os.path.exists(python_bin))
# Path to the script that must run under the virtualenv
script_file = path_parser("~/Documents/GitHub/Image-process-app/pyscripts/cp4_run.py")
print("script file exists: ", os.path.exists(script_file))
folder = sys.argv[1]
folder = os.path.abspath(folder) #folder of dic images passed on through command line; can be adapted to segment on fluorescence (E.g. frame 1 of MinE channel, or time-mean of MinE channel)

p = subprocess.Popen([python_bin,"-u",script_file, folder],
                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
for line in p.stdout:
    print("CHILD:", line, end="")