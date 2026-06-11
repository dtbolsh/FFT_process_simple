# FFT_process_simple
Basic scripts to process oscillatory signals in cell microscopy data.

# Image-process-app

Python/command-line pipeline for processing fluorescence microscopy timelapses. Designed for analysis of MinDE protein oscillations in yeast cells, but applicable to any oscillating fluorescence data. Input files are `.tiff` or `.nd2` timelapses, but can be adapted for other file extension from non-Nikon microscopes.

---

## Overview

Analysis is performed in three sequential stages:

1. **Cell segmentation** — generates a labeled mask from a timelapse image
    Note that if you have your own segmentation pipeline, that can be used instead of cellpose. The next step just needs a labeled mask (background pixels are 0, cells are 1,2,3...) and the raw fluorescence timeseries.
2. **Single-cell cropping** — extracts individual cells into zarr arrays with metadata
3. **FFT analysis** — performs temporal FFT on per-cell fluorescence intensity to extract oscillation data

Currently, the code assumes that the fluorescence order is green, red. Adjust the code if this not your imaging paradigm.

Scripts are organized into two levels:
- `pyscripts/` — child process scripts that operate on a single image
- Root folder — directory-looping scripts that iteratively apply the child scripts across a folder of images

---

## Setup

### Main environment

Install and activate the main conda environment using the provided yaml file:

```bash
conda env create -f environment.yml
conda activate basic-env
```

### Cellpose environments (for segmentation)

Cellpose3 and Cellpose4-SAM each require their own conda environment, set up separately by the user.

**Cellpose4-SAM** (requires a CUDA-capable GPU):

```bash
conda create -n cellpose4 python=3.10 -y
conda activate cellpose4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install "cellpose>=4.0"
pip install nd2
```

To verify GPU is accessible:

```python
from cellpose import core
print("Cellpose GPU enabled:", core.use_gpu())
```

**Cellpose3** can be set up similarly without the GPU-specific torch installation. See Cellpose documentation for details.

---

## Stage 1: Cell Segmentation

Generates a 2D mask tiff from a timelapse image. Background pixels are set to 0; each cell is labeled with a unique sequential integer.

Three options are available:

### 1. Cellpose4-SAM
Most robust option. Requires a GPU and the `cellpose4` environment. Run via the corresponding script in `pyscripts/`, which launches a subprocess in the `cellpose4` environment automatically.

### 2. Cellpose3
Does not require a GPU. May detect clusters of cells as single objects — downstream filtering by cell size is recommended to exclude these.

---

## Stage 2: Single-Cell Cropping

Takes a timelapse file and its corresponding mask as inputs. Loops over each labeled cell and saves cropped data for downstream analysis.

**Run on a single image:**
```bash
python pyscripts/single_cell_cropping.py path/to/mask path/to/image
```

**Run over a directory of images:**
```bash
python cell_cropper_dir_loop.py path/to/mask_folder path/to/image_folder
```

### Output structure

A folder called `individual_cells/` is created in the image directory. Inside, a subfolder is created for each image:

```
individual_cells/
  <image_name>/
    cells_metadata.csv    # cell size, location, background fluorescence, etc.
    cells.zarr/           # one zarr array per cell (includes time dimension)
    masks.zarr/           # matching bounding-box mask for each cell
```

The mask zarr is used in later stages to restrict FFT analysis to pixels belonging to the cell.

---

## Stage 3: FFT Analysis

Performs temporal FFT on per-pixel fluorescence intensity across the timelapse, using the cell mask to restrict analysis to each cell's pixels. Results are compiled into CSV files.

**Run on a single image's cells:**
```bash
python pyscripts/fluor_stack_process_single_cell_fft.py path/to/individual_cells/<image_name> [0,1]
```

**Run over a directory:**
```bash
python fft_process_sc.py path/to/individual_cells [0,1]
```

The second argument specifies which fluorescence channel(s) to process. Channel `0` is green, channel `1` is red (assumes green was acquired first). When both are specified, output CSV columns are prefixed with `green_` and `red_`.

> **Note:** Currently, passing `[1]` alone (red channel only) is likely to cause an error. Use `[0]` or `[0,1]` for now.

---