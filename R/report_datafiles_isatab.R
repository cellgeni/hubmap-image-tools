#!/usr/bin/env Rscript

args <- commandArgs( TRUE )
functionsFile <- args[ 1 ]
dataDir <- args[ 2 ]

suppressPackageStartupMessages( { 
    library( Risa ) 
    library( dplyr )
} )

options(stringsAsFactors = FALSE)

message( paste( "Loading functions from", functionsFile, "..." ) )

source( functionsFile )

message( "Functions loaded." )

message( paste( "Reading ISA-TAB files from", dataDir, "..." ) )

isatabData <- readISAtab( path = dataDir )

message( "Finished reading ISA-TAB files." )

# Get relationships between tissues and sample names.
sampleNameToTissue <- bind_rows( lapply(
    isatabData@study.files,
    function( studyFile ) {
        snameToTissue <- studyFile[ , c( "Sample Name", "Characteristics[organism part]" ) ]
        colnames( snameToTissue ) <-  c( "Sample Name", "Tissue" )
        snameToTissue
    }
) )


# Go through the assay files and create a data frame containing information
# about each tissue.
allAssaysInfo <- bind_rows( lapply( isatabData@assay.tabs, function( assayTab ) {

    assayNameType <- colnames( assayTab@assay.names )

    assayFileCols <- assayTab@assay.file[ , c( "Sample Name", assayNameType, "Raw Data File" ) ]

    assayTypeCol <- rep( assayTab@assay.technology.type, nrow( assayFileCols ) )

    assayFileColNames <- c( "Sample Name", "Assay Name", "Raw Data File", "Assay Type" )

    assayFileCols <- data.frame( assayFileCols, assayTypeCol )

    colnames( assayFileCols ) <- assayFileColNames

    merge( sampleNameToTissue, assayFileCols, by = "Sample Name" )
} ) )

tissues <- unique( allAssaysInfo[[ "Tissue" ]] )

cat( "------------------------\n" )
cat( paste( "Found", length( tissues ), "tissue(s).\n" ) )
cat( "------------------------\n" )

invisible( sapply( tissues, function( thisTissue ) {

    thisTissueAssayInfo <- allAssaysInfo[ which( allAssaysInfo[[ "Tissue" ]] == thisTissue ), ]

    cat( paste( 
        "Found", 
        length( unique( thisTissueAssayInfo[[ "Assay Name" ]] ) ),
        "assays on",
        thisTissue,
        ":\n"
    ) )

    assayTypes <- unique( thisTissueAssayInfo[[ "Assay Type" ]] )

    invisible( sapply( assayTypes, function( assayType ) {
        cat( paste( 
            length( which( thisTissueAssayInfo[[ "Assay Type" ]] == assayType ) ),
            "assays with type",
            assayType,
            "\n"
        ) )
    } ) )

    cat( "------------------------\n\n" )
    
    invisible( sapply( assayTypes, function( assayType ) {
        
        cat( "------------------------\n" )
    
        cat( paste(
            tools::toTitleCase( assayType ),
            "\n"
        ) )

        cat( "------------------------\n" )
    
        dataFiles <- file.path( 
            dataDir, 
            thisTissueAssayInfo[ which( thisTissueAssayInfo[[ "Assay Type" ]] == assayType ), "Raw Data File" ]
        )

        cat( paste( length( dataFiles ), "files found.\n" ) )

        imageSet <- create_image_data_list( dataFiles )   

        print_report( imageSet )

    } ) )
} ) )
