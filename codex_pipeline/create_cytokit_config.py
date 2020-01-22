#!/usr/bin/env python3

import argparse
import json
import logging
import math
import re
import sys
import yaml

logging.basicConfig( 
    level=logging.INFO, 
    format='%(levelname)-7s - %(message)s'
)
logger = logging.getLogger(__name__)

# collect_attribute()
# Returns the contents of the field matching the name(s) passed in the
# fieldNames argument.
# Field names are passed in a list because sometimes there is more than one
# possible name for the field. For example, in some files, the date field is
# called "date" and in others it is called "dateProcessed".
# The order the field names are passed in this list matters, because only the
# first one to match is returned.
# In some cases, the JSON file contains both versions of the field name, but
# only one of them has valid content. For example, some files have:
#   - "aperture": 0.75
#   - "numerical_aperture": 0.0
# So in this case we would only want the contents of the "aperture" field.
# In other cases, the "aperture" field doesn't exist, and only the
# "numerical_aperture" field is present, with valid content.
def collect_attribute( fieldNames, jsonObject ) :
    
    for fieldName in fieldNames:
        if fieldName in jsonObject:
            return jsonObject[ fieldName ]
    
    # If we're still here, it means we tried all the possible field names and
    # didn't find a match in the JSON, so we have to fail.
    fieldNameString = ", ".join( fieldNames )
    logger.error( "No match found for field name(s) in JSON file: %s" % fieldNameString )
    sys.exit()

# infer_nuclei_channel()
# Try to infer the name of the channel used as the nucleus marker. This is done
# in a very naive way, based on two assumptions:
#   1: The nucleus channel is probably "channel 1" in each cycle.
#   2: The nucleus channel is either called "DAPI" or "HOECHST".
def infer_nuclei_channel( channelNames, channelsPerCycle ) :
    
    # Fluorescent reporters known to be used to detect nuclei.
    # Using lower case, below pattern matching ignores case.
    nucleiMarkers = {
        "dapi" : 1,
        "hoechst" : 1
    }
    
    # Total number of channels across all cycles is the total number of assays.
    totalAssays = len( channelNames )
    
    # If the total number of assays cannot be divided evenly by the number of
    # channels per cycle, we have a problem.
    if totalAssays % channelsPerCycle :
        logger.error( "Total number of assays does not produce a whole number when divided by number of channels per cycle." )
        
        print( channelNames )

        print( "Number of assays: " + str( totalAssays ) )

        print( "Number of channels per cycle: " + str( numCycles ) )

        sys.exit()

    # The number of cycles is deduced by dividing the total number of assays by
    # the channels per cycle. This is because the number listed in the JSON
    # file is not always reliable.
    numCycles = int( totalAssays / channelsPerCycle )
    
    # Next we will search for the name of the reporter used to detect nuclei.
    # This is assumed to occupy the "first" channel position in each cycle, and
    # to be the same in all of the cycles. It must also match one of the known
    # nuclei reporters listed above, ignoring case.
    # Sometimes numbers are added to the end of the nuclei channel name to
    # denote cycle -- this is accounted for below.
    
    # Empty dictionary to collect nuclei reporter(s) found. We need to be
    # careful in case more than one is listed, in which case we wouldn't know
    # which one to list as the nuclei channel in the final config.
    nucleiChannelNames = {}
    
    # Initialise cycle counter and overall channel index counter.
    cycleIndex, channelIndex = 0, 0

    # For each cycle...
    while cycleIndex < numCycles :
        
        # Take the name of the channel at this channel index from the full list
        # of channels.
        channelName = channelNames[ channelIndex ]

        # Check if it matches a known marker.
        for marker in nucleiMarkers :

            # First match on just the marker name, with no trailing numbers.
            pattern = re.compile( "^" + marker + "$", re.IGNORECASE )
            match = pattern.match( channelName )
            
            if match :
                nucleiChannelNames[ channelName ] = 1
            
            else :

                # If this channel name didn't match this nuclei marker without
                # trailing numbers, see if it matches _with_ trailing numbers.
                patternWithIdx = re.compile( "^" + marker + "\d+$" )
                matchWithIdx = patternWithIdx.match( channelName )
            
                if matchWithIdx :
                    nucleiChannelNames[ channelName ] = 1

        cycleIndex += 1
        channelIndex += channelsPerCycle

    # If we got no matches, we don't know the nucleus channel.
    if len( nucleiChannelNames ) is 0 :
        logger.error( "No nuclei channel found. Cannot continue." )
        sys.exit()
    elif len( nucleiChannelNames ) > 1 :
        logger.error( "Found more than one possible nuclei channel. Cannot continue." )
        sys.exit()
    else :
        return next(iter(nucleiChannelNames.keys()))


# calculate_target_shape()
# Cytokit's nuclei detection U-Net (from CellProfiler) works best at 20x magnification.
# The CellProfiler U-Net requires the height and width of the images to be
# evenly divisible by 2 raised to the number of layers in the network, in this case 2^3=8.
# https://github.com/hammerlab/cytokit/issues/14
# https://github.com/CellProfiler/CellProfiler-plugins/issues/65
def calculate_target_shape( magnification, tileHeight, tileWidth ) :
    scaleFactor = 1
    if magnification is not 20 :
        scaleFactor = 20 / magnification

    dims = { 
        "height" : tileHeight, 
        "width" : tileWidth
    }
    
    # Width and height must be evenly divisible by 8, so we round them up to them
    # closest factor of 8 if they aren't.
    for dimension in dims:
        if dims[ dimension ] % 8 :
            newDim = int( 8 * math.ceil( float( dims[ dimension ] )/8 ) )
            dims[ dimension ] = newDim
    
    return [ dims[ "height" ], dims[ "width" ] ]


# main()
def main() :
    # Set up argument parser and parse the command line arguments.
    parser = argparse.ArgumentParser( 
        description = "Create a YAML config file for Cytokit, based on a JSON file from the CODEX Toolkit pipeline. YAML file will be created in current working directory unless otherwise specified."
    )
    parser.add_argument(
        "jsonFileName",
        help = "path to experiment.json file from CODEX Toolkit pipeline"
    )
    parser.add_argument(
        "-c",
        "--channel-names",
        help = "path to text file containing list of channel names."
    )
    parser.add_argument(
        "-o",
        "--outfile",
        help = "path to YAML output file."
    )

    args = parser.parse_args()
    
    if not args.outfile :
        args.outfile = "TEST_experiment.yaml"

    logger.info( "Output filename: " + args.outfile )

    if not args.channel_names :
        logger.info( "No channel names file passed. Will look for channel names in JSON config." )

    logger.info( "Reading config from " + args.jsonFileName + "..." )
    # Open the JSON config.
    with open( args.jsonFileName, 'r' ) as jsonFile:
        jsonData = jsonFile.read()
    logger.info( "Read file " + args.jsonFileName )

    # Create dictionary from JSON config.
    jsonObject = json.loads( jsonData )

    # Empty dictionaries to store sections of Cytokit config.
    cytokitConfigMain = {}
    cytokitConfigAcquisition = {}
    
    # Collect some initial values for the config. Sometimes we have to pass multiple
    # possible options (see comments above collect_attribute() function
    # definition).
    cytokitConfigMain[ "name" ] = collect_attribute( [ "name" ], jsonObject )
    cytokitConfigMain[ "date" ] = collect_attribute( [ "date", "dateProcessed" ], jsonObject )
    
    logger.info( "Populating acquisition section..." )

    cytokitConfigAcquisition[ "emission_wavelengths" ] = collect_attribute( [ "emission_wavelengths", "wavelengths" ], jsonObject )
    cytokitConfigAcquisition[ "axial_resolution" ] = collect_attribute( [ "zPitch", "z_pitch" ], jsonObject )
    cytokitConfigAcquisition[ "lateral_resolution" ] = collect_attribute( [ "xyResolution", "per_pixel_XY_resolution" ], jsonObject )
    cytokitConfigAcquisition[ "magnification" ] = collect_attribute( [ "magnification" ], jsonObject )
    cytokitConfigAcquisition[ "num_z_planes" ] = collect_attribute( [ "num_z_planes" ], jsonObject )
    cytokitConfigAcquisition[ "numerical_aperture" ] = collect_attribute( [ "aperture", "numerical_aperture" ], jsonObject )
    cytokitConfigAcquisition[ "objective_type" ] = collect_attribute( [ "objectiveType" ], jsonObject )
    cytokitConfigAcquisition[ "region_names" ] = collect_attribute( [ "region_names" ], jsonObject )
    cytokitConfigAcquisition[ "region_height" ] = collect_attribute( [ "region_height" ], jsonObject )
    cytokitConfigAcquisition[ "region_width" ] = collect_attribute( [ "region_width" ], jsonObject )
    cytokitConfigAcquisition[ "tile_height" ] = collect_attribute( [ "tile_height" ], jsonObject )
    cytokitConfigAcquisition[ "tile_width" ] = collect_attribute( [ "tile_width" ], jsonObject )
    cytokitConfigAcquisition[ "tile_overlap_x" ] = collect_attribute( [ "tile_overlap_X" ], jsonObject )
    cytokitConfigAcquisition[ "tile_overlap_y" ] = collect_attribute( [ "tile_overlap_Y" ], jsonObject )
    cytokitConfigAcquisition[ "tiling_mode" ] = collect_attribute( [ "tiling_mode" ], jsonObject )
    cytokitConfigAcquisition[ "per_cycle_channel_names" ] = collect_attribute( [ "channel_names" ], jsonObject )
    cytokitConfigAcquisition[ "num_cycles" ] = len( cytokitConfigAcquisition[ "per_cycle_channel_names" ] )
    
    if args.channel_names :
        with open( args.channel_names, 'r' ) as channelNamesFile :
            channelNames = channelNamesFile.read().splitlines()
        cytokitConfigAcquisition[ "channel_names" ] = channelNames
    else :
        if "channelNames" in jsonObject :
            cytokitConfigAcquisition[ "channel_names" ] = collect_attribute( [ "channelNamesArray" ], jsonObject[ "channelNames" ] )
        else :
            logger.error( "Cannot find data for channel_names field." )
            sys.exit()
    
    logger.info( "Acquisition section complete." )
    
    # Config "acquisition" section is now complete, add it to the main config dictionary.
    cytokitConfigMain[ "acquisition" ] = cytokitConfigAcquisition

    # environment: path_formats: <format> <-- e.g. "keyence_multi_cycle_v01".
    # Default to keyence_multi_cycle_v01 for now; sym-linked data directories
    # will be set up via a prior script.
    # All possible values for this field and their corresponding directory/file
    # naming patterns are available in the Cytokit github repo inside
    # python/pipeline/cytokit/io.py
    cytokitConfigMain[ "environment" ] = { "path_formats" : "keyence_multi_cycle_v01" }
    
    # Processor section.
    logger.info( "Populating processor section..." )
    # This section contains parameters for the preprocessing and segmentation
    # steps. Several of these parameters are taken from the Cytokit example
    # config as default values and may need to be optimised.
    # Assume we'll have two GPUs, switch on tile overlap cropping, preprocessed
    # tile generation, drift compensation, cytometry (segmentation), best focus
    # plane selection, and deconvolution.
    cytokitConfigProcessor = { 
        "args" : {
            "gpus" : [ 0, 1 ],
            "run_crop" : True,
            "run_tile_generator" : True,
            "run_drift_comp" : True,
            "run_cytometry" : True,
            "run_best_focus" : True,
            "run_deconvolution" : True
        }
    }

    # Default parameters from example config.
    cytokitConfigProcessor[ "deconvolution" ] = { "n_iter" : 25, "scale_factor" : .5 }
    cytokitConfigProcessor[ "tile_generator" ] = { "raw_file_type" : "keyence_mixed" }
    
    # Infer the nuclei channel name based on the channel names obtained earlier.
    nucleiChannelName = infer_nuclei_channel( 
        cytokitConfigMain[ "acquisition" ][ "channel_names" ], 
        cytokitConfigMain[ "acquisition" ][ "num_cycles" ]
    )

    cytokitConfigProcessor[ "best_focus" ] = { "channel" : nucleiChannelName }
    cytokitConfigProcessor[ "drift_compensation" ] = { "channel" : nucleiChannelName }
    
    # The target_shape needs to be worked out based on the metadata. See
    # comments on calculate_target_shape() function definition.
    targetShape = calculate_target_shape( 
        cytokitConfigAcquisition[ "magnification" ], 
        cytokitConfigAcquisition[ "tile_height" ], 
        cytokitConfigAcquisition[ "tile_width" ]
    )

    # Cytometry parameters.
    # Not including membrane channel name for now.
    cytokitConfigProcessor[ "cytometry" ] = {
        "target_shape" : targetShape,
        "nuclei_channel_name" : nucleiChannelName,
        "segmentation_params" : {
            "memb_min_dist" : 8,
            "memb_sigma" : 5,
            "memb_gamma" : .25,
            "marker_dilation" : 3
        },
        "quantification_params" : {
            "nucleus_intensity" : True,
            "cell_graph" : True
        }
    }

    logger.info( "Processor section complete." )

    # Add the processor section to the main config.
    cytokitConfigMain[ "processor" ] = cytokitConfigProcessor
        
    # Add analysis section.
    cytokitConfigMain[ "analysis" ] = [
        { 
            "aggregate_cytometry_statistics" : {
                "mode" : "best_z_plane"
            }
        }
    ]
    
    logger.info( "Writing Cytokit config to " + args.outfile )

    with open( args.outfile, 'w') as outFile:
        yaml.safe_dump( 
            cytokitConfigMain, 
            outFile,
            encoding = "utf-8",
            default_flow_style = None,
            indent = 2
        )

if __name__ == "__main__":
    main()

