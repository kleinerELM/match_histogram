# match_histogram
A script to match the histogram of a bunch of images which can be merged to a larger image

Select a reference image. The histogram of the other images in the same folder will be matched to the histogram of the reference image.

This script was programmed becaus of a brightness reduction within stiched SEM images of a MAPS project.

start the script using ./match_histogram.py and add -d for debugging output.

To slice a sub tile in smaller tiles to get a better histogram correction based on the best fitting tile, add -x and -y followed by the amount of slices as options.

The script stitches the images automatically using MIST and ImageJ after the correction.

help output:
```
#########################################################
# A script to automatically match the histogram of an   #
# image set created by MAPS (FEI/thermo scientific) to  #
# a selected image of the set.                          #
# The stitching at the end is optional.                 #
#                                                       #
# © 2020 Florian Kleiner                                #
#   Bauhaus-Universität Weimar                          #
#   Finger-Institut für Baustoffkunde                   #
#                                                       #
#########################################################

usage: D:\Nextcloud\Uni\WdB\REM\Fiji Plugins & Macros\Selbstgeschrieben\match_histograms\match_histogram.py [-h] [-f] [-c] [-i] [-x] [-y] [-r] [-d]
-h,                  : show this help
-i, --noImageJ       : skip ImageJ processing
-f,                  : force to correct holes for all tiles [off]
-c,                  : attempt to correct holes [off]
-x,                  : amount of slices in x direction [2]
-y,                  : amount of slices in y direction [2]
-r,                  : interim result images will be deleted after stitching [on]
-d                   : show debug output
```