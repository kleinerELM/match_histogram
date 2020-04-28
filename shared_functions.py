import os, sys, getopt, subprocess
import shutil
import numpy as np
import cv2

def cmdExists(cmd):
    return shutil.which(cmd) is not None

# seach for ImageJ
def imageJInPATH( settings ):
    if ( not cmdExists( "ImageJ-win64.exe" ) ):
        if os.name == 'nt':
            print( "make sure you have Fiji/ImageJ installed and added the program path to the PATH variable" )
            command = "rundll32 sysdm.cpl,EditEnvironmentVariables"
            try:
                subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                print( "Error" )
                pass
            print( "make sure you have Fiji/ImageJ installed and added the program path to the PATH variable" )
        else:
            print( "make sure Fiji/ImageJ is accessible from command line" )
        return False
    elif settings["showDebuggingOutput"] : print( "Fiji/ImageJ found!" )
    return True

# start imageJ, running the MIST stitching script.
# The script has to be modified to work with another machine!
def MIST_Stitching( settings, x_tile_count, y_tile_count ):
    pattern = ''
    pattern_old = "Tile_0{rr}-0{cc}-000000_0-000.tif"
    pattern_new = "Tile_0{rr}-0{cc}-000000_0-000.s0001_e00.tif"
    if ( os.path.isfile( settings["targetDirectory"] + "Tile_001-001-000000_0-000.tif" ) ):
        pattern = pattern_old
    elif ( os.path.isfile( settings["targetDirectory"] + "Tile_001-001-000000_0-000.s0001_e00.tif" ) ):
        pattern = pattern_new
    if ( pattern != '' ):
        command = "ImageJ-win64.exe -macro \"" + settings["home_dir"] +"\mist_stitching_maps.ijm\" "
        command += "\"" + settings["targetDirectory"] + "|" + os.path.dirname(settings["workingDirectory"]) + "|" 
        command += os.path.basename(settings["referenceFilePath"]) + "|" + x_tile_count + "|" + y_tile_count + "|" + str( settings["processCount"] ) + "|" + pattern + "\""

        print( "  starting ImageJ Macro..." )
        if settings["showDebuggingOutput"] : print( '  ' + command )
        try:
            subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print( "  Error" )
            pass
    else:
        print( 'filename pattern seems to have changed! fix function MIST_Stitching()' )

def equalize_histogram( source ):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    return clahe.apply(source)

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

# stitch using MIST
def stitch( settings ):
    if ( settings["runImageJ_Script"] and imageJInPATH( settings ) ):
        # get dimensions from last file name: Tile_005-005-000000_0-000.tif
        dim = settings["last_image_name"].split("_")# ..., 005-005-000000, ...
        dim = dim[1].split("-")# 005, 005, ...
        
        MIST_Stitching( settings, dim[1].lstrip("0"), dim[0].lstrip("0") )
        #remove directory wit corrected tiles
        if settings["delete_interim_results"] :
            shutil.rmtree( settings["targetDirectory"] )
    else:
        if settings["showDebuggingOutput"] : print( "...doing nothing!" )