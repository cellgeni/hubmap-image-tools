#!/usr/bin/env python3

import argparse
import json
import sys

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
def collect_attribute( fieldNames, jsonObject ):
    for fieldName in fieldNames:
        if fieldName in jsonObject:
            return jsonObject[ fieldName ]

    # If we're still here, it means we tried all the possible field names and
    # didn't find a match in the JSON, so we have to fail.
    fieldNameString = ", ".join( fieldNames )
    sys.exit( "ERROR - No match found for field name(s) in JSON file: %s" % fieldNameString )


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

    print( "Reading config from " + args.jsonFileName + "..." )

    if args.dir :
        print( "Will write YAML config to " + args.dir )

    # Open the JSON config.
    with open( args.jsonFileName, 'r' ) as jsonFile:
        jsonData = jsonFile.read()

    # Create dictionary from JSON config.
    jsonObject = json.loads( jsonData )

    # Empty dictionary to store Cytokit config.
    cytokitConfigDict = {}
    
    # Collect some values for the config. Sometimes we have to pass multiple
    # possible options (see comments above collect_attribute() function
    # definition).
    cytokitConfigDict[ "name" ] = collect_attribute( [ "name" ], jsonObject )
    cytokitConfigDict[ "date" ] = collect_attribute( [ "date", "dateProcessed" ], jsonObject )
    cytokitConfigDict[ "emission_wavelengths" ] = collect_attribute( [ "emission_wavelengths", "wavelengths" ], jsonObject )
    cytokitConfigDict[ "axial_resolution" ] = collect_attribute( [ "zPitch", "z_pitch" ], jsonObject )
    cytokitConfigDict[ "lateral_resolution" ] = collect_attribute( [ "xyResolution", "per_pixel_XY_resolution" ], jsonObject )
    cytokitConfigDict[ "magnification" ] = collect_attribute( [ "magnification" ], jsonObject )
    cytokitConfigDict[ "num_cycles" ] = collect_attribute( [ "num_cycles" ], jsonObject )
    cytokitConfigDict[ "num_z_planes" ] = collect_attribute( [ "num_z_planes" ], jsonObject )
    cytokitConfigDict[ "numerical_aperture" ] = collect_attribute( [ "aperture", "numerical_aperture" ], jsonObject )
    cytokitConfigDict[ "objective_type" ] = collect_attribute( [ "objectiveType" ], jsonObject )
    cytokitConfigDict[ "region_names" ] = collect_attribute( [ "region_names" ], jsonObject )
    cytokitConfigDict[ "region_height" ] = collect_attribute( [ "region_height" ], jsonObject )
    cytokitConfigDict[ "region_width" ] = collect_attribute( [ "region_width" ], jsonObject )
    cytokitConfigDict[ "tile_height" ] = collect_attribute( [ "tile_height" ], jsonObject )
    cytokitConfigDict[ "tile_width" ] = collect_attribute( [ "tile_width" ], jsonObject )
    cytokitConfigDict[ "tile_overlap_x" ] = collect_attribute( [ "tile_overlap_X" ], jsonObject )
    cytokitConfigDict[ "tile_overlap_y" ] = collect_attribute( [ "tile_overlap_Y" ], jsonObject )
    cytokitConfigDict[ "tiling_mode" ] = collect_attribute( [ "tiling_mode" ], jsonObject )



if __name__ == "__main__":
    main()
