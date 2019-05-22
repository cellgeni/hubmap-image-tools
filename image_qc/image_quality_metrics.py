#!/usr/bin/env python3

# Algorithms for calculating image sharpness metrics.
# Base on code from https://github.com/IDR/idr-notebooks/blob/master/CalculateSharpness.ipynb

class ImageQualityMetrics:

    # This algorithm is defined by De and Masilamani, 2013
    # (https://doi.org/10.1016/j.proeng.2013.09.086)
    def fourierBasedSharpnessMetric(self, plane):
        
        # Calculate Fourier Transform representation of image plane.
        fftimage = np.fft.fft2(plane)

        # Shift the origin of the Fourier Transform representation to centre.
        fftshift = np.fft.fftshift(fftimage)

        # Calculate the absolute values of the centred Fourier Transform.
        fftshift = np.absolute(fftshift)

        # Find M, the maximum value of the frequency component in the Fourier
        # Transform representation.
        M = np.amax(fftshift)

        # Calculate the total number of pixels whose value is greater than M/1000.
        Th = (fftshift > (M/float(1000))).sum()

        # Calculate the image quality measure (sharpness), Th divided by the image area.
        sharpness = Th/plane.size

        return sharpness
