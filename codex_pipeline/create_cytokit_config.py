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
# In some cases, the config file contains both versions of the field name, but
# only one of them has valid content. For example, some files have:
#   - "aperture": 0.75
#   - "numerical_aperture": 0.0
# So in this case we would only want the contents of the "aperture" field.
# In other cases, the "aperture" field doesn't exist, and only the
# "numerical_aperture" field is present, with valid content.
def collect_attribute( fieldNames, configDict ) :
    
    for fieldName in fieldNames:
        if fieldName in configDict:
            return configDict[ fieldName ]
    
    # If we're still here, it means we tried all the possible field names and
    # didn't find a match in the config, so we have to fail.
    fieldNameString = ", ".join( fieldNames )
    logger.error( "No match found for field name(s) in config: %s" % fieldNameString )
    sys.exit()

def infer_channel_name_from_index( cycleIndex, channelIndex, channelNames ) :
    
    # FIXME: Assuming 4 channels per cycle. Could pass len( channels_per_cycle ) instead.
    cycleLastChannelIdx = cycleIndex * 4

    cycleChannelIndices = range( cycleLastChannelIdx - 4, cycleLastChannelIdx - 1 )

    channelNameIdx = cycleChannelIndices[ channelIndex - 1 ]

    return channelNames[ channelNameIdx ]


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
        "exptJsonFileName",
        help = "path to experiment.json file from CODEX Toolkit pipeline."
    )
    parser.add_argument(
        "--segm-json",
        help = "path to JSON file containing segmentation parameters (including nuclearStainChannel and nuclearStainCycle)."
    )
    parser.add_argument(
        "--segm-text",
        help = "path to text file containing segmentation parameters (including nuclearStainChannel and nuclearStainCycle)."
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

    if not args.segm_json and not args.segm_text :
        logger.error( "Segmentation parameters file name not provided. Cannot continue." )
        sys.exit()
    
    if args.segm_json and args.segm_text :
        logger.warning( 
            "Segmentation parameter files " +
            args.segm_json +
            " and " +
            args.segm_text +
            " provided. Will only use " +
            args.segm_json
        )

    if not args.outfile :
        args.outfile = "TEST_experiment.yaml"

    logger.info( "Output filename: " + args.outfile )

    if not args.channel_names :
        logger.info( "No channel names file passed. Will look for channel names in experiment JSON config." )

    logger.info( "Reading config from " + args.exptJsonFileName + "..." )
    

    # Read in the experiment JSON config.
    with open( args.exptJsonFileName, 'r' ) as exptJsonFile :
        exptJsonData = exptJsonFile.read()
    logger.info( "Read file " + args.exptJsonFileName )

    # Create dictionary from experiment JSON config.
    exptConfigDict = json.loads( exptJsonData )
    
    # Read in the segmentation parameters. If we have a JSON file, use that.
    if args.segm_json :
        with open( args.segm_json, 'r' ) as segmJsonFile :
            segmJsonData = segmJsonFile.read()
        segmParams = json.loads( segmJsonData )
    else :

        with open( args.segm_text, 'r' ) as segmTextFile :
            fileLines = segmTextFile.read().splitlines()
            segmParams = {}
            for line in fileLines :
                fieldName, fieldContents = line.split( "=" )
                numPattern = re.compile( "^[0-9]+$" )
                numMatch = numPattern.match( fieldContents )
                if numMatch :
                    fieldContents = int( fieldContents )
                segmParams[ fieldName ] = fieldContents

    # Empty dictionaries to store sections of Cytokit config.
    cytokitConfigMain = {}
    cytokitConfigAcquisition = {}
    
    # Collect some initial values for the config. Sometimes we have to pass multiple
    # possible options (see comments above collect_attribute() function
    # definition).
    cytokitConfigMain[ "name" ] = collect_attribute( [ "name" ], exptConfigDict )
    cytokitConfigMain[ "date" ] = collect_attribute( [ "date", "dateProcessed" ], exptConfigDict )
    
    logger.info( "Populating acquisition section..." )

    cytokitConfigAcquisition[ "emission_wavelengths" ] = collect_attribute( [ "emission_wavelengths", "wavelengths" ], exptConfigDict )
    cytokitConfigAcquisition[ "axial_resolution" ] = collect_attribute( [ "zPitch", "z_pitch" ], exptConfigDict )
    cytokitConfigAcquisition[ "lateral_resolution" ] = collect_attribute( [ "xyResolution", "per_pixel_XY_resolution" ], exptConfigDict )
    cytokitConfigAcquisition[ "magnification" ] = collect_attribute( [ "magnification" ], exptConfigDict )
    cytokitConfigAcquisition[ "num_z_planes" ] = collect_attribute( [ "num_z_planes" ], exptConfigDict )
    cytokitConfigAcquisition[ "numerical_aperture" ] = collect_attribute( [ "aperture", "numerical_aperture" ], exptConfigDict )
    cytokitConfigAcquisition[ "objective_type" ] = collect_attribute( [ "objectiveType" ], exptConfigDict )
    cytokitConfigAcquisition[ "region_names" ] = collect_attribute( [ "region_names" ], exptConfigDict )
    cytokitConfigAcquisition[ "region_height" ] = collect_attribute( [ "region_height" ], exptConfigDict )
    cytokitConfigAcquisition[ "region_width" ] = collect_attribute( [ "region_width" ], exptConfigDict )
    cytokitConfigAcquisition[ "tile_height" ] = collect_attribute( [ "tile_height" ], exptConfigDict )
    cytokitConfigAcquisition[ "tile_width" ] = collect_attribute( [ "tile_width" ], exptConfigDict )
    cytokitConfigAcquisition[ "tile_overlap_x" ] = collect_attribute( [ "tile_overlap_X" ], exptConfigDict )
    cytokitConfigAcquisition[ "tile_overlap_y" ] = collect_attribute( [ "tile_overlap_Y" ], exptConfigDict )
    cytokitConfigAcquisition[ "tiling_mode" ] = collect_attribute( [ "tiling_mode" ], exptConfigDict )
    cytokitConfigAcquisition[ "per_cycle_channel_names" ] = collect_attribute( [ "channel_names" ], exptConfigDict )
    cytokitConfigAcquisition[ "num_cycles" ] = collect_attribute( [ "num_cycles" ], exptConfigDict )
    
    if args.channel_names :
        with open( args.channel_names, 'r' ) as channelNamesFile :
            channelNames = channelNamesFile.read().splitlines()
        cytokitConfigAcquisition[ "channel_names" ] = channelNames
    else :
        if "channelNames" in exptConfigDict :
            cytokitConfigAcquisition[ "channel_names" ] = collect_attribute( [ "channelNamesArray" ], exptConfigDict[ "channelNames" ] )
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
    
    bestFocusChannel = collect_attribute( [ "bestFocusReferenceChannel", "best_focus_channel" ], exptConfigDict )
    bestFocusCycle = collect_attribute( [ "bestFocusReferenceCycle" ], exptConfigDict )
    bestFocusChannelName = infer_channel_name_from_index( 
        bestFocusCycle, 
        bestFocusChannel, 
        cytokitConfigAcquisition[ "channel_names" ] 
    )

    driftCompChannel = collect_attribute( [ "driftCompReferenceChannel", "drift_comp_channel" ], exptConfigDict )
    driftCompCycle = collect_attribute( [ "driftCompReferenceCycle" ], exptConfigDict )
    driftCompChannelName = infer_channel_name_from_index( 
        driftCompCycle, 
        driftCompChannel, 
        cytokitConfigAcquisition[ "channel_names" ] 
    )

    cytokitConfigProcessor[ "best_focus" ] = { "channel" : bestFocusChannelName }
    cytokitConfigProcessor[ "drift_compensation" ] = { "channel" : driftCompChannelName }
    
    nucleiChannel = collect_attribute( [ "nuclearStainChannel" ], segmParams )
    nucleiCycle = collect_attribute( [ "nuclearStainCycle" ], segmParams )
    nucleiChannelName = infer_channel_name_from_index( 
        nucleiCycle, 
        nucleiChannel, 
        cytokitConfigAcquisition[ "channel_names" ]
    )

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

