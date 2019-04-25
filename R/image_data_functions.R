#!/usr/bin/env Rscript

suppressPackageStartupMessages( { 
    library( tools )
    library( Cardinal )
    library( RBioFormats )
} )
   

# Read mass spectrometry imaging data from CSV file and build a Cardinal
# MSImagingExperiment object from it.
create_msimagingexperiment_object <- function( filename ) {
    
    message( paste( "Reading mass spectrometry imaging data from", filename, "..." ) )

    ims_full_data <- read.csv( filename, header = FALSE, stringsAsFactors = FALSE )

    message( "File read successfully. Building MSImagingExperiment object..." )

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
    exptMetadata <- list( experiment_name = exptName )

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


