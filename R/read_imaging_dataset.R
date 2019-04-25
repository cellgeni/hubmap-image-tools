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


# TODO: How will we know which files contain which data?
#   - Naming conventions?
#   - Metadata linking samples->assays->files?

# For now go by extension as it's the simplest way, but it's also the least
# reliable.

# Read the data into a list.
imageSet <- sapply(
    dataFiles,
    function( dataFile ) {

        # If we have a CSV file, assume it's a mass spec imaging expermient.
        if( grepl( "\\.csv$", dataFile, ignore.case = TRUE ) ) {

            create_msimagingexperiment_object( dataFile )
        }

        else if( grepl( "\\.tiff?$", dataFile, ignore.case = TRUE ) ) {

            read_tiff_metadata( dataFile )
        }
    }
)

cat( "\n-----------------\n" )
cat( "Image data report\n" )
cat( "-----------------\n" )

# Print some stats about the data we found.
invisible( sapply(
    names( imageSet ),
    function( imgName ) {
        
        cat( "------------------------\n" )
        cat( paste( imgName, "\n" ) )
        cat( "------------------------\n" )

        img <- imageSet[[ imgName ]]

        if( class( img ) == "ImageMetadata" ) {

            cat( "TIFF image\n" )
            
            cat( "Image dimensions (px): " )
            dimString <- paste( "x:", img$coreMetadata$sizeX, " y:", img$coreMetadata$sizeY )
            if( img$coreMetadata$sizeZ > 0 ) {
                dimString = paste( dimString, "z:", img$coreMetadata$sizeZ )
            }
            if( img$coreMetadata$sizeC > 0 ) {
                dimString = paste( dimString, "c:", img$coreMetadata$sizeC )
            }
            if( img$coreMetadata$sizeT > 0 ) {
                dimString = paste( dimString, "t:", img$coreMetadata$sizeT )
            }
            cat( paste( dimString, "\n" ) )

            cat( paste( "Dimension order:", img$coreMetadata$dimensionOrder ), "\n" )

            cat( paste( "Pixel type:", img$coreMetadata$pixelType ), "\n" )

            cat( paste( "Number of channels:", img$globalMetadata$NumberOfChannels ), "\n" )

            cat( "------------------------\n\n" )
        }

        else if( class( img ) == "MSImagingExperiment" ) {
            
            cat( "Mass spectrometry imaging data\n" )

            cat( "Image dimensions (px): " )

            cat( paste( "x:", max( coord( img )$x ), "y:", max( coord( img )$y ), "\n" ) )

            cat( paste( 
                "m/z range:", 
                min( mz( img ) ), 
                "to", 
                max( mz( img ) ), 
                " (",
                dim( iData( img ) )[ 1 ],
                " measurements)\n"
            ) )
            
            cat( "------------------------\n\n" )
        }
        else {

            cat( paste( "Image class (", class( img ), ") not supported.\n", sep="" ) )
        }
    }
) )


