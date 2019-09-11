#!/usr/bin/env python3

# Adapted from https://github.com/spacetx/starfish/blob/master/notebooks/SeqFISH.ipynb

import argparse

import os
from copy import deepcopy
import numpy as np
import pandas as pd

import skimage.filters
#from skimage.morphology import opening, dilation, disk
from skimage.transform import SimilarityTransform, warp

from functools import partial

import starfish
import starfish.data
from starfish.spots import DetectSpots
from starfish.types import Features

ap = argparse.ArgumentParser()
ap.add_argument( 
    "-o", 
    "--outfile", 
    required = True, 
    help = "Path to output file"
)
args = vars( ap.parse_args() )

# Select seqFISH data for a single field of view.
exp = starfish.data.SeqFISH( use_test_data=True )
img = exp[ 'fov_000' ].get_image( 'primary' )

# The first step in seqFISH is to do some rough registration. For this example
# data, the rough registration has already been done by the authors, so this
# step is omitted.
# FIXME: how do we do it, if it hasn't been done?

# Remove image background, using a White Tophat filter, which measures the
# background with a folling disck morphological element and subtracts it from
# the image.
wth = starfish.image.Filter.WhiteTophat( masking_radius = 3 )
background_corrected = wth.run( img, in_place = False )

# Scale images to equalize spot intensities across channels.
# The number of peaks are not uniform across rounds and channels, which
# prevents histogram matching across channels. Instead, a percentile value is
# identified and set as the maximum across channels, and the dynamic range is
# extended to equalize the channel intensities
clip = starfish.image.Filter.Clip( 
    p_max = 99.9, 
    expand_dynamic_range = True, 
    is_volume = True 
)
scaled = clip.run( background_corrected, in_place = False )

# Remove residual background.
# The background is fairly uniformly present below intensity=0.5. However,
# starfish's clip method only supports percentiles. To solve this problem, the
# intensities can be directly edited in the underlying numpy array.
clipped = deepcopy( scaled )
clipped.xarray.values[ clipped.xarray.values < 0.7 ] = 0

# In the example in the notebook, they first try using a local blob detector to
# detect the spots. However, they report that based on visual inspection of
# results using a local blob detector, it looks like the spot correspondence
# across rounds is not being detected well. 
# So instead, they then try using the PixelSpotDetector.
glp = starfish.image.Filter.GaussianLowPass( sigma = ( 0.3, 1, 1 ), is_volume=True )
blurred = glp.run( clipped )
psd = starfish.spots.DetectPixels.PixelSpotDecoder(
    codebook = exp.codebook, 
    metric = 'euclidean', 
    distance_threshold = 0.5,
    magnitude_threshold = 0.1, 
    min_area = 7, 
    max_area = 50,
)
pixel_decoded, ccdr = psd.run( blurred )

# Create a data frame of the spot intensities.
spots_df = pixel_decoded.to_features_dataframe()

# Add a column with the area of the spot.
spots_df['area'] = np.pi*spots_df['radius']**2

# This step limits results to only those that pass thresholds. However in this
# dataset this would only be two rows, so have left it commented out for now.
#spots_df = spots_df.loc[spots_df[Features.PASSES_THRESHOLDS]]

# Write it out to a file.
spots_df.to_csv( args[ 'outfile' ], index=None, sep='\t' )
