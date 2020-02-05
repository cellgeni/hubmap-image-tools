#!/usr/bin/env python3

import argparse
import json
import logging
import os
import re
import stat
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)-7s - %(message)s'
)
logger = logging.getLogger(__name__)

# Patterns for detecting raw data files are below. 
# We follow Cytokit's "keyence_multi_cycle_v01" naming convention defined in:
# https://github.com/hammerlab/cytokit/blob/master/python/pipeline/cytokit/io.py
# Pattern for the directories containing the raw data from each cycle-region
# pair. Different submitters use different naming conventions (e.g.
# cyc001_reg001_191209_123455 or Cyc1_reg1), so our regex has to allow for this.
rawDirNamingPattern = re.compile( r'^cyc0*(\d+)_reg0*(\d+).*', re.IGNORECASE )
# Pattern for raw data TIFF files. These should be named according to the following pattern:
# <region index>_<tile index>_Z<z-plane index>_CH<channel index>.tif
# All indices start at 1.
# Tile index is padded to three digits, e.g. 00025, 00001, etc.
# Z-plane index is padded to three digits, e.g. 025, 001, etc.
# Region and channel indices are one digit each.
rawFileNamingPattern = re.compile( r'^\d_\d{5}_Z\d{3}_CH\d\.tif$' )
# Pattern to match one single digit at the start of a string, used to replace
# incorrect region indices with the correct ones in some raw data TIFF files.
rawFileRegionPattern = re.compile( r'^\d' )


def create_analysis_subdir( targetDir, dirName ) :

    newDir = os.path.join( targetDir, dirName )

    try :
        os.mkdir( newDir )
    except OSError as err :
        logger.error( 
            "Could not create data directory " +
            newDir +
            " : " +
            err.strerror
        )
        sys.exit(1)
    else :
        logger.info( "Directory %s created." % newDir )


########
# MAIN #
########
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description = "Set up a directory in which to run Cytokit analysis. Populate directory with a \"data\" directory containing symlinks to the raw image data."
    )
    parser.add_argument(
        "manifestFilename",
        help = "Path to JSON manifest file containing path to raw CODEX data directory."
    )
    parser.add_argument(
        "targetDirectory",
        help = "Path to directory to be created. Will create a \"data\" directory inside this containing symlinks to the raw data."
    )

    args = parser.parse_args()

    ###################################################################
    # Inspect source directories and collect paths to raw data files. #
    ###################################################################
    
    logger.info( "Reading manifest file " + args.manifestFilename + "..." )

    with open( args.manifestFilename, 'r' ) as manifestFile :
        manifestJsonData = manifestFile.read()

    logger.info( "Finished reading manifest file." )

    manifestInfo = json.loads( manifestJsonData )
	
    rawDataLocation = manifestInfo[ "raw_data_location" ]

    # Ensure that source directory exists and is readable.
    st = os.stat( rawDataLocation )
    readable = bool( st.st_mode & stat.S_IRUSR )
    if not readable :
        logger.error(
            "Source directory " +
            rawDataLocation +
            " is not readable by the current user."
        )
        sys.exit(1)

    
    # Get list of contents of source directory. This should contain a set of
    # subdirectories, one for each cycle-region pair.
    sourceDirList = None
    try :
        sourceDirList = os.listdir( rawDataLocation )
    except OSError as err :
        logger.error(
            "Could not acquire list of contents for " +
            rawDataLocation +
            " : " +
            err.strerror
        )
        sys.exit(1)
   
    # Filter the contents list of the source directory for directories matching
    # the expected raw data directory naming pattern (cycle-region pairs).
    # Different submitters follow different naming conventions currently.
    sourceDataDirs = list( 
        filter( 
            rawDirNamingPattern.search,
            sourceDirList
        )
    )
    # If there were no matching directories found, exit.
    if len( sourceDataDirs ) is 0 :

        logger.error( 
            "No directories matching expected raw data directory naming pattern found in " +
            rawDataLocation 
        )
        sys.exit(1)
    
    
    # Go through the cycle-region directories and get a list of the contents of
    # each one. Each cycle-region directory should contain TIFF files,
    # following the raw data file naming convention defined above.
    # Collect raw data file names in a dictionary, indexed by directory name.
    sourceDataFiles = {}
    for sdir in sourceDataDirs :
       
        fileList = None

        try :
            fileList = os.listdir( os.path.join( rawDataLocation, sdir ) )
        except OSError as err :
            logger.error(
                "Could not acquire list of contents for " +
                sdir +
                " : " +
                err.strerror
            )
            sys.exit(1)
        
        # Validate naming pattern of raw data files according to pattern
        # defined above.
        fileList = list(
            filter(
                rawFileNamingPattern.search,
                fileList
            )
        )

        # Die if we didn't get any matching files.
        if len( fileList ) is 0 :
            logger.error(
                "No files found matching expected raw file naming pattern in " +
                sdir
            )
            sys.exit(1)
        
        # Otherwise, collect the list of matching file names in the dictionary.
        else :
            sourceDataFiles[ sdir ] = fileList

    

    ######################################
    # Start creating directories and links
    ######################################

    # Create target directory.
    # FIXME: what permissions should this have?
    try :
        os.mkdir( args.targetDirectory )
    except OSError as err :
        logger.error( 
            "Could not create Cytokit analysis directory " +
            args.targetDirectory +
            " : " +
            err.strerror
        )
        sys.exit(1)
    else :
        logger.info( "Cytokit analysis directory created at %s" % args.targetDirectory )

    # Create data directory under the target directory -- this is where the
    # symlinks to the raw data will go.
    for subDir in [ "data", "output" ] :
        create_analysis_subdir( args.targetDirectory, subDir )

    
    # Create cycle-region directories containing symlinks to files.
    logger.info( "Creating symlinks to raw data files..." )
    for sdir in sourceDataFiles :
        
        dirMatch = rawDirNamingPattern.match( sdir )

        cycle, region = dirMatch.group( 1, 2 )

        cycleRegionDir = os.path.join( dataDir, "Cyc" + cycle + "_reg" + region )
        
        try :
            os.mkdir( cycleRegionDir )
        except OSError as err :
            logger.error(
                "Could not create target directory " +
                cycleRegionDir +
                " : " +
                err.strerror
            )
            sys.exit(1)

        # Create symlinks for TIFF files.
        for tifFileName in sourceDataFiles[ sdir ] :
            
            # Replace the region number at the start because sometimes it's wrong.
            linkTifFileName = rawFileRegionPattern.sub( region, tifFileName )

            # Set up full path to symlink.
            linkTifFilePath = os.path.join( cycleRegionDir, linkTifFileName )
            
            # Full path to source raw data file.
            sourceTifFilePath = os.path.join( rawDataLocation, sdir, tifFileName )
            
            # Create the symlink.
            try :
                os.symlink( 
                    sourceTifFilePath,
                    linkTifFilePath
                )
            except OSError as err :
                logger.error(
                    "Count not create symbolic link: " +
                    err.strerror
                )
                sys.exit(1)

    logger.info( "Links created in directories under %s" % dataDir )
