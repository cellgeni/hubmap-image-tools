#!/usr/bin/env Rscript

# Source required functions.
functionsFile <- file.path(
    Sys.getenv( "HUBMAP_GIT" ),
    "R",
    "image_data_functions.R"
)
source( functionsFile )

# Parse cmdline args
args <- commandArgs( TRUE )

# File containing all spectral intensities and coordinates in CSV format.
massSpecDataFile <- args[ 1 ]

# File containing metadata describing molecules represented in the data.
molecularMetadataFile <- args[ 2 ]

# Molecule to search with, as "Elemental composition" e.g. "C39H79N2O6P".
molecule <- args[ 3 ]

check_files( c( massSpecDataFile, molecularMetadataFile ) )

# Read in mass spec data files and build object.
msdata <- create_msimagingexperiment_object( massSpecDataFile, molecularMetadataFile )

colocalizedFeatures <- find_colocalized_features( msdata, molecule )

print( colocalizedFeatures )




check_files <- function( fileVector ) {

    for ( f in fileVector ) {
        
        if( !file.exists( f ) ) {
            
            stop(
                paste(
                    "Cannot find",
                    f,
                    " -- please check it exists and is readable."
                )
            )
        }
    }
}
