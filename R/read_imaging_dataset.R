#!/usr/bin/env Rscript

args <- commandArgs( TRUE )
functionsFile <- args[ 1 ]
dataDir <- args[ 2 ]

message( paste( "Loading functions from", functionsFile, "..." ) )

source( functionsFile )

message( "Functions loaded." )


message( paste( "Locating files in", dataDir, "..." ) )

dataFiles <- dir( dataDir, full.names = TRUE )

message( paste( length( dataFiles ), "files found." ) )

# Read the data into a list.
imageSet <- create_image_data_list( dataFiles )

# Print some stats about the data.
print_report( imageSet )

