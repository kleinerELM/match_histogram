# Background removal tools

This projects contains two tools which attempt to remove uneven lightning of a set of microscopic images which are subtiles of a larger image.
match_histogram.

The ImageJ macro mist_stitching_maps.ijm has to be changed according to the used computer. Record a macro in ImageJ, run MIST using CUDA to determine the neccessary settings!

## match_histogram.py
A script to match the histogram of a bunch of images which can be merged to a larger image

Select a reference image. The histogram of the other images in the same folder will be matched to the histogram of the reference image.

This script was programmed becaus of a brightness reduction within stiched SEM images of a MAPS project.

Start the script using the following command:

```bash
python ./match_histogram.py
```

To slice a sub tile in smaller tiles to get a better histogram correction based on the best fitting tile, add -x and -y followed by the amount of slices as options.

The script stitches the images automatically using MIST and ImageJ after the correction.

### help output:
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

## background_removal.py

This script calculates a polynomial fit as proposed in https://stackoverflow.com/questions/33964913/equivalent-of-polyfit-for-a-2d-polynomial-in-python by https://stackoverflow.com/users/12063126/paddy-harrison using a selected reference image.

The calculated background will then be substracted from all images.

The script stitches the images automatically using MIST and ImageJ after the correction.

start the script using the following command:

```bash
python ./background_removal.py
```

### help output
```
#########################################################
# A script to automatically remove a reoccuring shadow  #
# effect in a stack of microscopy images                #
#                                                       #
# © 2020 Florian Kleiner                                #
#   Bauhaus-Universität Weimar                          #
#   Finger-Institut für Baustoffkunde                   #
#                                                       #
#########################################################

usage: C:\Users\Florian Kleiner\Documents\Nextcloud\Uni\WdB\REM\Fiji Plugins & Macros\Selbstgeschrieben\match_histograms\background_removal.py [-h] [-i] [-r] [-d]
-h,                  : show this help
-i, --noImageJ       : skip ImageJ processing
-r,                  : interim result images will be deleted after stitching [on]
-d                   : show debug output
```