#!/usr/bin/env python3

import argparse
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

rawDirNamingPattern = re.compile( r'^cyc0*(\d+)_reg0*(\d+).*', re.IGNORECASE )
rawFileNamingPattern = re.compile( r'^\d_\d{5}_Z\d{3}_CH\d\.tif$' )
rawFileRegionPattern = re.compile( r'^\d' )


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description = "Set up a directory in which to run Cytokit analysis. Populate directory with a \"data\" directory containing symlinks to the raw image data."
    )
    parser.add_argument(
        "sourceDirectory",
        help = "Path to directory containing raw CODEX data directories."
    )
    parser.add_argument(
        "targetDirectory",
        help = "Path to directory to be created. Will create a \"data\" directory inside this containing symlinks to the raw data."
    )

    args = parser.parse_args()

    # Ensure that source directory exists and is readable.
    st = os.stat( args.sourceDirectory )
    readable = bool( st.st_mode & stat.S_IRUSR )
    if not readable :
        logger.error(
            "Source directory " +
            args.sourceDirectory +
            " is not readable by the current user."
        )
        sys.exit(1)

    # Get list of contents of source directory.
    sourceDirList = None
    
    try :
        sourceDirList = os.listdir( args.sourceDirectory )
    except OSError as err :
        logger.error(
            "Could not acquire list of contents for " +
            args.sourceDirectory +
            " : " +
            err.strerror
        )
        sys.exit(1)
   
    
    # Look for directories matching the expected raw data directory naming pattern.
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
            args.sourceDirectory 
        )
        sys.exit(1)
    

    # TODO: inspect list of source dir contents and create symlinks accordingly.
    # Some dirs are named like "cyc1_reg1_191205_225343" or "Cyc1_reg1".
    # TODO: For the uf data, we could simply create symlinks to the cycle
    # directories named according to pattern "Cyc{cycle:d}_reg{region:d}",
    # because the files inside are named according to the rest of the pattern
    # already. However for the other data, the cycle directories are named
    # according to the pattern but the files inside always have a "1" at the
    # start where the region number should be. Since there is more than one
    # region in this dataset, my expectation is that if the TIFFs begin with
    # "1" but the region number is not "1", Cytokit will complain. This needs
    # to be looked into though, maybe it will be OK.
    # However, doing different things depending on the source directory and
    # file naming unnecessarily complicates the code. We may as well just
    # create individual links for the files, rather than sometimes creating links
    # for directories and other times creating links for files.
    
    sourceDataFiles = {}

    for sdir in sourceDataDirs :
       
        fileList = None

        try :
            fileList = os.listdir( os.path.join( args.sourceDirectory, sdir ) )
        except OSError as err :
            logger.error(
                "Could not acquire list of contents for " +
                sdir +
                " : " +
                err.strerror
            )
            sys.exit(1)
        
        # Validate naming pattern of raw data files. This should follow this
        # pattern:
        # <region index>_<tile index>_Z<z-plane index>_CH<channel index>.tif
        # All indices start at 1.
        # Tile index is padded to three digits, e.g. 00025, 00001, etc.
        # Z-plane index is padded to three digits, e.g. 025, 001, etc.
        # Region and channel indices are one digit each.
        fileList = list(
            filter(
                rawFileNamingPattern.search,
                fileList
            )
        )
        if len( fileList ) is 0 :
            logger.error(
                "No files found matching expected raw file naming pattern in " +
                sdir
            )
            sys.exit(1)
        
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
    dataDir = os.path.join( args.targetDirectory, "data" )

    try :
        os.mkdir( dataDir )
    except OSError as err :
        logger.error( 
            "Could not create data directory " +
            dataDir +
            " : " +
            err.strerror
        )
        sys.exit(1)
    else :
        logger.info( "Directory for data symlinks created at %s" % dataDir )

    
    # Create cycle-region directories containing symlinks to files.
    for sdir in sourceDataFiles :
        
        #dirPattern = re.compile( rawDirNamingPattern, re.IGNORECASE )
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
        for tifFilename in sourceDataFiles[ sdir ] :
            
            # Replace the region number at the start because sometimes it's wrong.
            tifFilename = rawFileRegionPattern.sub( region, tifFilename )
            
            #try :
            #    os.symlink( )
