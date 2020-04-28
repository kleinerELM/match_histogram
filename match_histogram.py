import os, sys, getopt, subprocess
import shutil
import numpy as np
import tkinter as tk
import cv2
from tkinter import filedialog
import multiprocessing

# import shared libary
import shared_functions as sf

def programInfo():
    print("#########################################################")
    print("# A script to automatically match the histogram of an   #")
    print("# image set created by MAPS (FEI/thermo scientific) to  #")
    print("# a selected image of the set.                          #")
    print("# The stitching at the end is optional.                 #")
    print("#                                                       #")
    print("# © 2020 Florian Kleiner                                #")
    print("#   Bauhaus-Universität Weimar                          #")
    print("#   Finger-Institut für Baustoffkunde                   #")
    print("#                                                       #")
    print("#########################################################")
    print()

#### process given command line arguments
def processArguments( settings ):
    col_changed = False
    row_changed = False
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-f] [-c] [-i] [-x] [-y] [-r] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hicfx:y:rd",["noImageJ="])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-i, --noImageJ       : skip ImageJ processing' )
            print( '-f,                  : force to correct holes for all tiles [off]' )
            print( '-c,                  : attempt to correct holes [off]' )
            print( '-x,                  : amount of slices in x direction [' + str( settings["col_count"] ) + ']' )
            print( '-y,                  : amount of slices in y direction [' + str( settings["row_count"] ) + ']' )
            print( '-r,                  : interim result images will be deleted after stitching [on]' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-i", "-noImageJ"):
            settings["runImageJ_Script"] = False
        elif opt in ("-f"):
            settings["forceCorrectionAttempt"] = True
            settings["correctionAttempt"] = True
        elif opt in ("-c"):
            settings["correctionAttempt"] = True
        elif opt in ("-x"):
            settings["col_count"] = int( arg )
            col_changed = True
        elif opt in ("-y"):
            settings["row_count"] = int( arg )
            row_changed = True
        elif opt in ("-r"):
            settings["delete_interim_results"] = True
        elif opt in ("-d"):
            print( 'show debugging output' )
            settings["showDebuggingOutput"] = True
    if settings["correctionAttempt"] : 
        print( 'attempting to correct artifacts caused by holes through slicing the tile...' )
    # alway expecting the same values for row/col if not defined explicitly        
        if col_changed and not row_changed:
            settings["row_count"] = settings["col_count"]
        elif row_changed and not col_changed:
            settings["col_count"] = settings["row_count"]
        if row_changed or col_changed:
            print( 'Changed the amount of slices in x and y direction to ' + str( settings["row_count"] ) + ' and ' + str( settings["col_count"] ) )
    else: print( 'No correction attempt for artifacts due to medium sized holes...' )
    if settings["runImageJ_Script"]:
        print( 'Tiles will be stitched after the process!' )
        if settings["delete_interim_results"]: print( ' Interim result images will be deleted after stitching!' )
        else: print( ' Interim result images wont be deleted after stitching.' )
    else: print( 'Deactivating ImageJ processing!' )

    print( '' )
    return settings

# load reference image and populate all relevant variables,
# so they have to be calculated and loaded only once
refImg = {
    "values"    : False,
    "counts"    : False,
    "quantiles" : False,
    "avg_color" : 0
}

def load_reference( settings ):
    print( " calculating background of reference image" )
    
    reference = cv2.imread( settings["referenceFilePath"], 0 )#, mode='RGB')
    ref_gauss = cv2.GaussianBlur(reference,(5,5),cv2.BORDER_DEFAULT)
    reference_normalized = sf.equalize_histogram( reference )
    #reference_histogram = cv2.calcHist( ref_gauss,[0], None, [8], [0,256] )
    refImg["values"], refImg["counts"] = np.unique( reference_normalized.ravel(), return_counts=True )
    refImg["quantiles"] = np.cumsum(refImg["counts"]).astype(np.float64)
    refImg["quantiles"] /= refImg["quantiles"][-1]
    if settings["correctionAttempt"]: refImg["avg_color"] = get_avg_color( reference_normalized )

# the actual histogram matching, modified from this source:
# https://stackoverflow.com/questions/32655686/histogram-matching-of-two-images-in-python-2-x
def hist_matching( source, refImg, settings, position, cropped_images = None ):
    ignore_until_color = 0
    # _values: color values from 0-255 for 8 bit
    # _counts: counts of these color values
    src_values, bin_idx, src_counts = np.unique( source.ravel(), return_inverse=True, return_counts=True )
    # searching for the best fitting cropped image in the given list and trying to fit this image to the given histogram instead of the full image.
    if not cropped_images == None:
        avg_color_list = []
        for i in range(len(cropped_images)):# cropped_image in cropped_images:
            avg_color_list.append( get_avg_color( sf.equalize_histogram( cropped_images[i] ) ) )
        closest_to_ref = min( range(len(avg_color_list)), key=lambda i: abs(avg_color_list[i] - refImg["avg_color"]))
        alt_source = cropped_images[ closest_to_ref ].ravel()
        #src_values = src_values
        alt_src_values, alt_src_counts = np.unique( alt_source.ravel(), return_counts=True )
        for j in range( len( src_values ) ):
            if src_values[j] not in alt_src_values:
                src_counts[j] = 0
            else:
                index = np.where( alt_src_values == src_values[j] )
                src_counts[j] = alt_src_counts[ index ]
        if settings["showDebuggingOutput"]: print( "  " + str( position ) + ": choosing tile " + str( closest_to_ref + 1 ) + " for calculation (" + str( avg_color_list[closest_to_ref] ) + " | " + str( refImg["avg_color"] ) + ")!" )

    src_quantiles = np.cumsum( src_counts ).astype( np.float64 ) # cumultative sum of the counts
    src_quantiles /= src_quantiles[-1] # sum of all counts is normed to  (last value of the list)

    #apply the created histogram table to the image and save it
    interp_ref_values = np.interp( src_quantiles, refImg["quantiles"], refImg["values"] )
    interp_ref_values = interp_ref_values.astype( source.dtype )
    return interp_ref_values[bin_idx].reshape( source.shape )

# cut an image to subtiles
# return the cropped images in an array/list
def sliceImage( filename, settings, position ):
    image = cv2.imread( settings["workingDirectory"] + '/' + filename, 0 )
    height, width = image.shape[:2]
    #cropping
    crop_height = int( height / settings["row_count"] )
    crop_width = int( width / settings["col_count"] )
    cropped_images = []
    for i in range( settings["row_count"] ): # start at i = 0 to row_count-1
        for j in range( settings["col_count"] ): # start at j = 0 to col_count-1
            # create the subimage and append it to the list of cropped subimages
            cropped_images.append( image[(i*crop_height):((i+1)*crop_height), j*crop_height:((j+1)*crop_width)] )
    image=None
    if settings["showDebuggingOutput"] : print( "  " + str( position ) + ": cropped image to " + str( len( cropped_images ) ) + " parts")
    return cropped_images

# return the average color / brightness of an image
def get_avg_color( source ):
    avg_color = np.average(source.ravel(), axis=0)
    return round( avg_color,1 )

def startProcess( file, settings, refImg, position ):
    allowed_brightness_difference = 5
    filename = os.fsdecode(file)
    print( " Analysing " + filename + " (" + str( position ) + "/" + str( settings["count"]) + ")." )
    source = cv2.imread( settings["workingDirectory"] + "/" + file, 0)
    # check if correction attempt is necessary 
    if settings["correctionAttempt"] or settings["forceCorrectionAttempt"]:
        # if the average color of an image is higher than "allowed_brightness_difference", do a correction attempt
        src_avg_color = get_avg_color( sf.equalize_histogram( source ) )
        if ( (src_avg_color < refImg["avg_color"] - allowed_brightness_difference) or (src_avg_color > refImg["avg_color"] + allowed_brightness_difference) or settings["forceCorrectionAttempt"] ):
            # crop the images and run histogram matching using the cropped images instead
            if settings["showDebuggingOutput"]:
                if settings["forceCorrectionAttempt"] : 
                    print( "  " + str( position ) + ": forced correction ( " + str( src_avg_color ) + " vs. " + str( refImg["avg_color"] ) + " )" )
                else: 
                    print( "  " + str( position ) + ": the image seems to have a big deviation from the reference image ( " + str( src_avg_color ) + " vs. " + str( refImg["avg_color"] ) + " )" )
            cropped_images = sliceImage( filename, settings, position )
            matched = hist_matching( source, refImg, settings, position, cropped_images )
        else:
            if settings["showDebuggingOutput"] : print( "  " + str( position ) + ": the image seems to have a small deviation from the reference image ( " + str( src_avg_color ) + " vs. " + str( settings["avg_color"] ) + " )" )
            matched = hist_matching( source, refImg, settings, position  )
    else:
        matched = hist_matching( source, refImg, settings, position )
    # save the tile
    cv2.imwrite( settings["targetDirectory"] + filename, matched )
    print( " Done analysing " + filename + " (" + str( position ) + "/" + str( settings["count"] ) + ")." )

if __name__ == '__main__':
    #remove root windows
    root = tk.Tk()
    root.withdraw()
    coreCount = multiprocessing.cpu_count()
    settings = {
        "runImageJ_Script" : True,
        "showDebuggingOutput" : False,
        "correctionAttempt" : False,
        "forceCorrectionAttempt" : False,
        "delete_interim_results" : True,
        "col_count" : 2,
        "row_count" : 2,
        "home_dir" : os.path.dirname(os.path.realpath(__file__)),
        "workingDirectory" : "",
        "targetDirectory"  : "",
        "referenceFilePath" : "",
        "last_image_name" : "",
        "outputDirName" : "corrected",
        "count" : 0,
        "coreCount" : coreCount,
        "processCount" : (coreCount - 1) if coreCount > 1 else 1
    }
    position = 0

    ### actual program start
    programInfo()
    settings = processArguments( settings )
    print( "Please select a reference image from the image set.", end="\r" )
    settings["referenceFilePath"] = filedialog.askopenfilename(title='Please select the reference image',filetypes=[("Tiff images", "*.tif;*.tiff")])
    print( "                                                   ", end="\r" )
    settings["workingDirectory"] = os.path.dirname( settings["referenceFilePath"] )

    if ( settings["showDebuggingOutput"] ) : 
        print( 'Found ' + str( coreCount ) + ' CPU cores. Using max. ' + str( settings["processCount"] ) + ' processes at once.' )
        print( "I am living in '" + settings["home_dir"] + "'" )
        print( "Selected working directory: " + settings["workingDirectory"], end='\n\n' )
        print( "Selected reference file: " + os.path.basename( settings["referenceFilePath"] ) )

    ## count files
    fileList = []
    if os.path.isdir( settings["workingDirectory"] ) :
        settings["targetDirectory"] = settings["workingDirectory"] + '/' + settings["outputDirName"] + '/'
        # create output directory if it does not exist
        if not os.path.exists( settings["targetDirectory"] ):
            os.makedirs( settings["targetDirectory"] )

        for file in os.listdir(settings["workingDirectory"]):
            if ( file.endswith( ".tif" ) or file.endswith( ".TIF" ) ):
                fileList.append( file )
                settings["count"] += 1

        print( str( settings["count"] ) + " Tiffs found!" )
        settings["last_image_name"] = os.fsdecode( fileList[-1] )

        # load reference image
        load_reference( settings )

        # processing files
        pool = multiprocessing.Pool( settings["processCount"] )
        for file in fileList:
            position += 1
            #startProcess( file, workingDirectory, targetDirectory, position, count )
            pool.apply_async(startProcess, args=( file, settings, refImg, position ) )

        pool.close()
        pool.join()

        # stitch using MIST
        sf.stitch( settings )
    else:
        print( "directory not found!" )

    print( "Script DONE!" )