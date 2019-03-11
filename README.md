# fs19-optical-illusions
Neural Systems Project

# Conda
There is an environment file. use it with:

```
conda env install -f environment.yml
conda env update -f environment.yml
```

# Meeting
Friday: 11:00 at INI

# Goals

## Week 1
* Summary of illusionary Thinks
* Prepare Repository
* Commit papers to git


# Math
# Gabor Parameter
ksize is the size of the Gabor kernel. If ksize = (a, b), we then have a Gabor kernel of size a x b pixels. As with many other convolution kernels, ksize is preferably odd and the kernel is a square (just for the sake of uniformity).

sigma is the standard deviation of the Gaussian function used in the Gabor filter.

theta is the orientation of the normal to the parallel stripes of the Gabor function.

lambda is the wavelength of the sinusoidal factor in the above equation.

gamma is the spatial aspect ratio.

psi is the phase offset.

ktype indicates the type and range of values that each pixel in the Gabor kernel can hold.