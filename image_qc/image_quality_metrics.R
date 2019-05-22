
# Algorithms for calculating image quality metrics.

# This algorithm is defined by De and Masilamani, 2013
# (https://doi.org/10.1016/j.proeng.2013.09.086).
fourierBasedSharpnessMetric <- function( fftshiftFunctionsFile, plane ) {
    
    # Load functions for shifting origin of FT representation to centre.
    source( fftshiftFunctionsFile )
    
    # Calculate Fourier Transform representation of image plane.
    fftimage <- fft( plane )

    # Shift the origin of the FT representation to centre.
    shifted <- fftshift( fftimage )

    # Calculate the absolute values of the centred FT.
    shiftedAbs <- abs( shifted )
    
    # Find M, the maximum value of the frequency component in the FT representation.
    M <- max( shiftedAbs )

    # Calculate the total number of pixels whose value is greater than M/1000.
    Th <- sum( shiftedAbs > ( M/1000 ) )

    # Calculate the image quality measure (sharpness), Th divided by the image area.
    sharpness <- Th/prod( dim( plane ) )

    return( sharpness )
