
fourierBasedSharpnessMetric <- function( fftshiftFunctionsFile, plane ) {

    source( fftshiftFunctionsFile )
    
    fftimage <- fft( plane )

    shifted <- fftshift( fftimage )

    shiftedAbs <- abs( shifted )

    M <- max( shiftedAbs )

    Th <- sum( shiftedAbs > ( M/1000 ) )

    sharpness <- Th/prod( dim( plane ) )

    return( sharpness )
