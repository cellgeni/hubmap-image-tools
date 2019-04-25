#!/usr/bin/env Rscript

args <- commandArgs( TRUE )
functionsFile <- args[ 1 ]
dataDir <- args[ 2 ]

suppressMessages( library( Risa ) )

message( paste( "Loading functions from", functionsFile, "..." ) )

source( functionsFile )

message( "Functions loaded." )

message( paste( "Reading ISA-TAB files from", dataDir, "..." ) )

isatabData <- readISAtab( path = dataDir )

message( "Finished reading ISA-TAB files." )

dataFiles <- file.path( dataDir, unlist( isatabData@data.filenames, use.names = FALSE ) )

message( paste( length( dataFiles ), "files found." ) )

imageSet <- create_image_data_list( dataFiles )

print_report( imageSet )
