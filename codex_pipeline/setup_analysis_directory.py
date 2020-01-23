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
    readable = bool( st.stat_mode & stat.S_IRUSR )
    if not readable :
        logger.error(
            "Source directory " +
            args.sourceDirectory +
            " is not readable by the current user."
        )
        sys.exit()

    # Get list of contents of source directory.
    sourceDirList = None
    
    try :
        sourceDirList = os.listdir( args.sourceDir )
    except OSError as err :
        logger.error(
            "Could not acquire list of contents for " +
            args.sourceDirectory +
            " : " +
            err.strerror
        )
        sys.exit()
    
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
        sys.exit()
    else :
        logger.info( "Cytokit analysis directory created at %s" % args.targetDirectory )

    # Create data directory under the target directory -- this is where the
    # symlinks to the raw data will go.
    dataDir = os.path.join( args.targetDir, "data" )

    try :
        os.mkdir( dataDir )
    except OSError as err :
        logger.error( 
            "Could not create data directory " +
            dataDir +
            " : " +
            err.strerror
        )
        sys.exit()
    else :
        logger.info( "Directory for data symlinks created at %s" % dataDir )

    
    # TODO: inspect list of source dir contents and create symlinks accordingly.
    # Some dirs are named like "cyc1_reg1_191205_225343" or "Cyc1_reg1".
    sourceDataDirs = list( 
        filter( 
            lambda item: re.search( r'^cyc\d+_reg\d+.*', item, re.IGNORECASE ),
            sourceDirList
        )
    )

    # TODO: For the uf data, we could simply create symlinks to the cycle
    # directories named according to pattern "Cyc{cycle:d}_reg{region:d}",
    # because the files inside are named according to the rest of the pattern
    # already. However for the other data, the cycle directories are named
    # according to the pattern but the files inside always have a "1" at the
    # start where the region number should be. Since there is more than one
    # region in this dataset, my expectation is that if the TIFFs begin with
    # "1" but the region number is not "1", Cytokit will complain. This needs
    # to be looked into though, maybe it will be OK.
