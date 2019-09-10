#!/usr/bin/env python3

# Adapted from https://github.com/spacetx/starfish/blob/master/notebooks/DARTFISH.ipynb
# Reproduce UCSD Zhang lab DARTFISH results using SpaceTX Starfish.
# DARTFISH is a multiplexed image based transcriptomics assay from the Zhang
# lab (http://genome-tech.ucsd.edu/ZhangLab/).

# Using parameter values decided in the above notebook.

import argparse

import pandas as pd
import numpy as np
import os

from starfish import data, FieldOfView
from starfish.types import Features

from starfish.image import Filter
from starfish.spots import DetectPixels

ap = argparse.ArgumentParser()
ap.add_argument( 
    "-o", 
    "--outfile", 
    required = True, 
    help = "Path to output file"
)
args = vars( ap.parse_args() )

# Load DARTFISHv1 2017 example data from the cloud.
# The data represent human brain tissue from the human occipital cortex from
# one field of view (FOV) of a larger experiment. The data from one FOV
# correspond to 18 images from six imaging rounds (r), three colour channels
# (c), and one z-plane (z). Each image is 988x988 pixels.
use_test_data = os.getenv( "USE_TEST_DATA" ) is not None
experiment = data.DARTFISH( use_test_data=use_test_data )

imgs = experiment.fov().get_image(FieldOfView.PRIMARY_IMAGES)

# Filter and scale raw data before decoding into spatially resolved gene expression.
# First, we bring the intensities of all the images into the same scale as one
# another, by scaling each image by its maximum intensity. This is equivalent
# to scaling by the 100th percentile value of the pixel values in each image.
sc_filt = Filter.Clip( p_max=100, expand_dynamic_range=True )
norm_imgs = sc_filt.run( imgs )

# Next, for each imaging round and each pixel location, we zero the intensity
# values across all three colour channels, if the magnitude of this vector of
# colour channels is below a certain threshold (here 0.05). The code value
# associated with these pixels will be blank. This is necessary to support
# euclidean decoding for codebooks that include blank values.
z_filt = Filter.ZeroByChannelMagnitude( thresh=.05, normalize=False )
filtered_imgs = z_filt.run( norm_imgs )

# Decode the processed data into spatially resolved gene expression profiles.
# Here, Starfish decodes each pixel value, across all rounds and channels, into
# the corresponding target (gene) that it corresponds to. Contiguous pixels
# that map to the same target gene are called as one RNA molecule. Intuitively,
# pixel vectors are matched to the codebook by computing the euclidean distance
# between the pixel vector and all codewords. The minimal distance gene target
# is then selected, if it is within <distance_threshold> of any code.

# FIXME: The decoding operation requires some parameter tuning, which is described in
# the original notebook but left out here. Here, we take the parameter values
# decided in the original notebook and run with them.

# The magnitude threshold was decided by looking at the distribution of the
# pixel vector barcode magnitudes, to determine the maximum magnitude threshold
# at which to attempt to decode the pixel vector.
magnitude_threshold = 0.5 

# The area threshold defines the range of the size we expect our spots to be
# (min, max). This was set to be equivalent to the parameters determined by the
# Zhang lab.
area_threshold = ( 5, 30 )

# The distance threshold defines how close, in euclidean space, the pixel
# barcodes should be to the nearest barcode it was called to. Here, this is set
# to a large number, to allow manual inspection of decoded distances. FIXME:
# Keeping this as I'm not sure what a good value is.
distance_threshold = 3

# Set up a PixelSpotDetector.
psd = DetectPixels.PixelSpotDecoder(
    codebook=experiment.codebook,
    metric='euclidean',
    distance_threshold=distance_threshold,
    magnitude_threshold=magnitude_threshold,
    min_area=area_threshold[0],
    max_area=area_threshold[1]
)

# Run detection.
initial_spot_intensities, results = psd.run( filtered_imgs )

# Create a data frame of initial spot intensities.
spots_df = initial_spot_intensities.to_features_dataframe()
spots_df['area'] = np.pi*spots_df['radius']**2
spots_df = spots_df.loc[spots_df[Features.PASSES_THRESHOLDS]]

# Write it out to a file.
spots_df.to_csv( args[ 'outfile' ], index=None, sep='\t' )

