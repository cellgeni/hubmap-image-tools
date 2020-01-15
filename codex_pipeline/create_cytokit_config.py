#!/usr/bin/env python3

import argparse
import json
import sys
import re
import yaml

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
    sys.exit( "ERROR - No match found for field name(s) in JSON file: %s" % fieldNameString )


# infer_nuclei_channel
# Try to infer the name of the channel used as the nucleus marker. This is done
# in a very naive way, based on two assumptions:
#   1: The nucleus channel is probably "channel 1" in each cycle.
#   2: The nucleus channel is either called "DAPI" or "HOECHST".
def infer_nuclei_channel( channelNames, numCycles ) :
    
    nucleiMarkers = {
        "dapi" : 1,
        "hoechst" : 1
    }

    totalAssays = len( channelNames )

    if totalAssays % numCycles :
        sys.exit( "ERROR - total number of assays does not produce a whole number when divided by number of cycles." )

    channelsPerCycle = int( totalAssays / numCycles )

    # Collect the names of the first channel in each cycle, in a dictionary.
    firstChannelNames = {}
    cycleIndex, channelIndex = 0, 0
    while cycleIndex < numCycles :
        firstChannelNames[ channelNames[ channelIndex ] ] = 1
        cycleIndex += 1
        channelIndex += channelsPerCycle

    # So far, the first channel is always the same, and is always the nucleus channel.
    if len( firstChannelNames ) is 1 :
        firstChannel = next(iter(firstChannelNames.keys()))
        pattern = re.compile( "^" + firstChannel + "$", re.IGNORECASE )
        for marker in nucleiMarkers:
            match = pattern.match( marker )
            if match :
                return firstChannel
        
        # If we haven't returned, then the channel name didn't match any of the
        # known nuclei markers, so we have to fail for now.
        sys.exit( "ERROR - " + firstChannel + " is not a known nuclei marker. Add it to the list if it should be and try again." )
    
    else :
        # If we had more than one marker in channel position "1" when looking
        # at all the cycles, we can't currently decide which one to use, so we
        # have to fail for now.
        sys.exit( "ERROR - More than one marker used in \"channel 1\", don't know where to look for nuclei marker.")

# main
def main():
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
        "-d",
        "--dir",
        help = "path to directory to write Cytokit YAML config."
    )
    args = parser.parse_args()

    if args.dir :
        print( "Will write YAML config to " + args.dir )

    if not args.channel_names :
        print( "No channel names file passed. Will look for channel names in JSON config." )

    print( "Reading config from " + args.jsonFileName + "..." )
    # Open the JSON config.
    with open( args.jsonFileName, 'r' ) as jsonFile:
        jsonData = jsonFile.read()
    print( "Read file." )

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

    cytokitConfigAcquisition[ "emission_wavelengths" ] = collect_attribute( [ "emission_wavelengths", "wavelengths" ], jsonObject )
    cytokitConfigAcquisition[ "axial_resolution" ] = collect_attribute( [ "zPitch", "z_pitch" ], jsonObject )
    cytokitConfigAcquisition[ "lateral_resolution" ] = collect_attribute( [ "xyResolution", "per_pixel_XY_resolution" ], jsonObject )
    cytokitConfigAcquisition[ "magnification" ] = collect_attribute( [ "magnification" ], jsonObject )
    cytokitConfigAcquisition[ "num_cycles" ] = collect_attribute( [ "num_cycles" ], jsonObject )
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
    
    if args.channel_names :
        with open( args.channel_names, 'r' ) as channelNamesFile :
            channelNames = channelNamesFile.read().splitLines()
        cytokitConfigAquisition[ "channel_names" ] = channelNames
    else :
        if "channelNames" in jsonObject :
            cytokitConfigAcquisition[ "channel_names" ] = collect_attribute( [ "channelNamesArray" ], jsonObject[ "channelNames" ] )
        else :
            sys.exit( "ERROR - Cannot find data for channel_names field." )

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
    # This section contains parameters for the preprocessing and segmentation
    # steps. Several of these parameters are taken from the Cytokit example
    # config as default values and may need to be optimised.
    # Assume we'll have two GPUs, switch on tile overlap cropping, preprocessed
    # tile generation, drift compensation, cytometry (segmentation), best focus
    # plane selection, and deconvolution.
    cytokitConfigProcessor = { 
        "args" : {
            "gpus" : [ 0, 1 ],
            "run_crop" : "true",
            "run_tile_generator" : "true",
            "run_drift_comp" : "true",
            "run_cytometry" : "true",
            "run_best_focus" : "true",
            "run_deconvolution" : "true"
        }
    }

    # Default parameters from example config.
    cytokitConfigProcessor[ "deconvolution" ] = { "n_iter" : 25, "scale_factor" : .5 }
    cytokitConfigProcessor[ "tile_generator" ] = { "raw_file_type" : "keyence_mixed" }
    
    # TODO: infer the nuclei channel name based on the channel names obtained earlier.
    nucleiChannelName = infer_nuclei_channel( 
        cytokitConfigMain[ "acquisition" ][ "channel_names" ], 
        cytokitConfigMain[ "acquisition" ][ "num_cycles" ]
    )

    cytokitConfigProcessor[ "best_focus" ] = { "channel" : nucleiChannelName }
    cytokitConfigProcessor[ "drift_compensation" ] = { "channel" : nucleiChannelName }

    # Cytometry parameters.
    # TODO: target_shape and nuclei channel name need to be worked out based on the metadata.
    # Not including membrane channel name for now.
    cytokitConfigProcessor[ "cytometry" ] = {
        #"target_shape" = [ x, y ],
        "nuclei_channel_name" : nucleiChannelName,
        "segmentation_params" : {
            "memb_min_dist" : 8,
            "memb_sigma" : 5,
            "memb_gamma" : .25,
            "marker_dilation" : 3
        },
        "quantification_params" : {
            "nucleus_intensity" : "true",
            "cell_graph" : "true"
        }
    }

    cytokitConfigMain[ "processor" ] = cytokitConfigProcessor
    


if __name__ == "__main__":
    main()























