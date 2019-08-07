#!/usr/bin/env Rscript

suppressPackageStartupMessages( { 
    library( tools )
    library( Cardinal )
    library( RBioFormats )
} )
   

# Read mass spectrometry imaging data from CSV file and build a Cardinal
# MSImagingExperiment object from it.
create_msimagingexperiment_object <- function( filename, metadataFile ) {
    
    message( paste( "Reading mass spectrometry imaging data from", filename, "..." ) )

    ims_full_data <- read.csv( filename, header = FALSE, stringsAsFactors = FALSE )

    message( "File read successfully." )

    # Make sure the header only contains m/z values and not any letters.
    # The data are provided with m/z value plus molecule name but we require
    # that only the m/z values are present. We have a perl script to fix this.
    if( any( grepl( "[A-Za-z]", ims_full_data[ 1,3:ncol( ims_full_data ) ] ) ) ) {
        
        stop( "Letters found in m/z-value-only column headers. Please ensure that, aside from x and y in the first two columns, the headers contain m/z values ONLY. You may need to run the script perl/fix_ims_header.pl first." )
    
    }
    
    # Find x and y coordinate columns
    xcol_idx <- which( ims_full_data[ 1, ] == "x" )
    ycol_idx <- which( ims_full_data[ 1, ] == "y" )

    if( length( xcol_idx ) != 1 ) {
        stop( "Did not find a column to use as x coordinates." )
    }
    if( length( ycol_idx ) != 1 ) {
        stop( "Did not find a column to use as y coordinates." )
    }

    # Get the m/z values from the first row of the data frame.
    mz_values <- as.numeric( ims_full_data[ 1 , -c( xcol_idx, ycol_idx ) ] )

    # If there are any missing pixels, fill them with NA.
    max_x <- max( as.numeric( ims_full_data[ -1, xcol_idx ] ) )
    max_y <- max( as.numeric( ims_full_data[ -1, ycol_idx ] ) ) 

    if( ( nrow( ims_full_data ) -1 ) / max_x != max_y ) {

        ims_full_data <- merge(
            expand.grid(
                x = unique( as.numeric( ims_full_data[ -1, xcol_idx ] ) ),
                y = unique( as.numeric( ims_full_data[ -1, ycol_idx ] ) ),
                stringsAsFactors = FALSE
            ),
            data.frame(
                x = as.numeric( ims_full_data[ -1, xcol_idx ] ),
                y = as.numeric( ims_full_data[ -1, ycol_idx ] ),
                ims_full_data[ -1, -c( xcol_idx, ycol_idx ) ]
            ),
            all = TRUE
        )
    }

    # Columns come back as character type so convert them to numeric.
    ims_full_data <- as.data.frame( 
        sapply( ims_full_data, function( x ) as.numeric( x ) )
    )
    
    # Replace NAs with zeros, otherwise colocalization stats don't work.
    # FIXME: This means that we now don't know the difference between a real
    # zero and "missing" -- instead we could just do this substitution when we
    # need to?
    ims_full_data[ is.na( ims_full_data ) ] <- 0


    # Make sure that the x and y columns of type integer. If they are not it
    # can cause problems for writing to imzML format.
    ims_full_data$x <- as.integer( ims_full_data$x )
    ims_full_data$y <- as.integer( ims_full_data$y )

    # Ensure the data are ordered by x first and then y.
    ims_full_data <- ims_full_data[ order( ims_full_data$x, ims_full_data$y ), ]

    # Create a matrix containing the image data.
    # The data needs to be transposed so that the m/z values are the rows and the
    # coordinates are the columns.
    ims_image_matrix <- as.matrix( t( ims_full_data[ , -c( xcol_idx, ycol_idx ) ] ) )

    # Create a "run" column. This represents a sample (individual experimental
    # "run"). TODO: how should we use this? It is required.
    run <- factor( rep( "Run 1", nrow( ims_full_data ) ) )

    # Create the components of the Cardinal MSImagingExperiment object.
    pdata <- PositionDataFrame( 
        run = run, 
        coord = data.frame( x = ims_full_data$x, y = ims_full_data$y ) 
    )
    fdata <- MassDataFrame( mz = mz_values )
    idata <- ImageArrayList( list( ims_image_matrix ) )

    # TODO: should we have some sanity checks here to make sure dimensions match etc?

    # Name for the experiment, taken from the CSV filename; can be used to
    # write files etc.
    exptName <- basename( file_path_sans_ext( filename ) )

    # Create a list for the experimental metadata.
    # NB: access with "msiInfo( msdata )@metadata"
    exptMetadata <- list( experiment_name = exptName )

    # Read the metadata file, if there is one.
    if( !missing( metadataFile ) ) {
        
        metadataTable <- read.csv( metadataFile, header = FALSE, stringsAsFactors = FALSE )

        # Remove empty columns, if any.
        nonNAcols <- !sapply( metadataTable, function( x ) all( is.na( x ) ) )
        metadataTable <- metadataTable[ , nonNAcols ]

        # Add the table to the metadata list for the experiment object.
        exptMetadata$metadataTable <- metadataTable
    }

    # Create the object.
    msdata <- MSImagingExperiment( 
        imageData = idata, 
        featureData = fdata, 
        pixelData = pdata,
        metadata = exptMetadata
    )
    
    message( "MSImagingExperiment object created." )

    return( msdata )
}


# FIXME: Currently using the "Elemental Composition " column to look up the
# molecule input -- this would be better as the compound name or something? But
# would require some more powerful fancy search expansion stuff.
find_colocalized_features <- function( msdata, molecule ) {

    metadataTable <- msiInfo( msdata )@metadata$metadataTable

    # Die here if we didn't get a metadata table.
    if( is.null( metadataTable ) ) {
        stop( 
            paste( 
                "No metadata table found. Cannot locate m/z value for",
                molecule
            )
        )
    }

    mzCol <- metadataTable[ , metadataTable[ 1, ] == "Experimental m/z" ]

    moleculeCol <- metadataTable[ , metadataTable[ 1, ] == "Elemental Composition " ]
    
    moleculeMz <- mzCol[ which( moleculeCol == molecule ) ]

    # Default number of results is 10, can be changed using n= argument).
    colocalizedFeatures <- colocalized( msdata, mz = moleculeMz )

    molecules <- sapply(
        colocalizedFeatures$mz,
        function( mzVal ) {
            rowNum <- which( mzCol == mzVal )
            moleculeCol[ rowNum ]
        }
    )

    colocalizedFeatures <- cbind( colocalizedFeatures, ElementalComposition = molecules )

    return( colocalizedFeatures )
}


# Basic checks for file access.
check_files <- function( fileVector ) {

    for ( f in fileVector ) {
        
        # Check file exists.
        if( !file.exists( f ) ) {
            
            stop(
                paste(
                    "Cannot find file:",
                    f,
                    "Please check it exists and is readable.",
                    sep = "\n"
                )
            )
        }
        
        # Check file is readable.
        if( file.access( f, mode = 4 ) == -1 ) {

            stop(
                paste(
                    "Cannot read file:",
                    f,
                    "Please ensure it is readable by the current user."
                )
            )
        }
    }
}


apply_affine_transformation <- function( transformationMatrixFile, maskImage, msdata ) {

    transformationMatrix <- matrix(
        scan( transformationMatrixFile ),
        nrow = 3
    )
    
    if( ncol( transformationMatrix ) != 2 ) {
        stop( 
            paste( 
                "Affine transformation matrix has incorrect dimensions. Please check file",
                transformationMatrixFile
            )
        )
    }
                
    # TODO: Do this for all images in the IMS object instead of hard coding m/z value.
    
    # Load EBImage package if it's not already loaded. This package provides
    # the Image() and affine() functions.
    if( ! "package:EBImage" %in% search() ) {
        suppressMessages( library( EBImage ) )
    }
        
    # Convert the slice to an EBImage Image object.
    imsImage <- Image( slice( msdata, mz = 687.5453 ) )
    
    # Run affine transform.
    transformedImage <- affine( 
        imsImage, 
        transformationMatrix, 
        output.dim = c( dim( maskImage )[ 1 ], dim( maskImage )[ 2 ] )
    )
    
    # Return the transformed image; FIXME: this only returns one plane due to hard coded m/z value.
    return( transformedImage )

}


# Write an MSImagingExperiment object to current working dir, named to match
# the original data file.
write_imzml <- function( msdata ) {
    
    # exptName is used for the filename stem of the imzML files *.ibd and
    # *.imzml , and was taken from the name of the original CSV file when the
    # object was created.
    exptName <- metadata( msdata )$experiment_name
    
    # Use 32-bit float for intensity data (got an error with 64-bit).
    # Use current working dir for now.
    writeImzML(
        msdata,
        exptName,
        folder = ".",
        mz.type = "64-bit float",
        intensity.type = "32-bit float"
    )
}


# Read TIFF file metadata with RBioFormats package.
read_tiff_metadata <- function( filename ) {

    message( paste( "Reading TIFF metadata from file", filename, "..." ) )

    tiffMetadata <- read.metadata( filename )

    message( "TIFF metadata read successfully." )

    return( tiffMetadata )
}


write_ims_images <- function( msdata, targetDir ) {

    # FIXME: stopping at the first 10 images for now.
    for( mz in mz( msdata )[ 1:10 ] ) { 
            
        # Get the molecule name from the metadata.
        exptMetadata <- msiInfo( msdata )@metadata

        moleculeName <- exptMetadata$metadataTable[ , 7 ][ which( exptMetadata$metadataTable[ , 1 ] == mz ) ]
        
        # FIXME: here using PNG images, this can be changed to any other format.
        imgFile <- file.path( targetDir, paste( "mz_", mz, ".png", sep = "" ) )

        png( filename = imgFile )

        print( image( msdata, mz = mz, colorscale = magma, main = paste( "Molecule:", moleculeName, "\n" ) ) )

        dev.off()
    }
}


# Create a list containing representations of various image data types, given a
# vector of file names.
# TODO: How will we know which files contain which data?
#   - Naming conventions?
#   - Metadata linking samples->assays->files?

# For now go by extension as it's the simplest way, but it may not be very
# reliable.

create_image_data_list <- function( dataFiles ) {

    imageSet <- sapply(
        dataFiles,
        function( dataFile ) {

            # If we have a CSV file, assume it's a mass spec imaging expermient.
            if( grepl( "\\.csv$", dataFile, ignore.case = TRUE ) ) {

                create_msimagingexperiment_object( dataFile )
            }

            else if( grepl( "\\.tiff?$", dataFile, ignore.case = TRUE ) ) {

                list( read_tiff_metadata( dataFile ) )
            }
        }
    )
    
    return( imageSet )
}


# Print a little report about the image data representations.
print_report <- function( imageSet ) {

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
}

