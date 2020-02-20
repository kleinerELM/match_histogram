import os, sys, getopt, subprocess
import shutil
import numpy as np
import tkinter as tk
import cv2
from tkinter import filedialog
#remove root windows
root = tk.Tk()
root.withdraw()

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

#### directory definitions
home_dir = os.path.dirname( os.path.realpath(__file__) )

runImageJ_Script = True
showDebuggingOutput = False
make_black = False
correctionAttempt = False
delete_interim_results = True
col_count = 2
row_count = 2

#### process given command line arguments
def processArguments():
    global outputDirName
    global correctionAttempt
    global delete_interim_results
    global col_count
    global row_count
    global showDebuggingOutput
    global runImageJ_Script
    col_changed = False
    row_changed = False
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-c] [-i] [-x] [-y] [-r] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hicx:y:rd",["noImageJ="])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-i, --noImageJ       : skip ImageJ processing' )
            print( '-c,                  : attempt to correct holes [off]' )
            print( '-x,                  : amount of slices in x direction [' + str( col_count ) + ']' )
            print( '-y,                  : amount of slices in y direction [' + str( row_count ) + ']' )
            print( '-r,                  : interim result images will be deleted after stitching [on]' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-i", "-noImageJ"):
            runImageJ_Script = False
        elif opt in ("-c"):
            correctionAttempt = True
        elif opt in ("-x"):
            col_count = int( arg )
            col_changed = True
        elif opt in ("-y"):
            row_count = int( arg )
            row_changed = True
        elif opt in ("-r"):
            showDebuggingOutput = True
        elif opt in ("-d"):
            print( 'show debugging output' )
            showDebuggingOutput = True
    if correctionAttempt : 
        print( 'attempting to correct artifacts caused by holes through slicing the tile...' )
    # alway expecting the same values for row/col if not defined explicitly        
        if col_changed and not row_changed:
            row_count = col_count
        elif row_changed and not col_changed:
            col_count = row_count
        if row_changed or col_changed:
            print( 'Changed the amount of slices in x and y direction to ' + str( row_count ) + ' and ' + str( col_count ) )
    else: print( 'No correction attempt for artifacts due to medium sized holes...' )
    if runImageJ_Script:
        print( 'Tiles will be stitched after the process!' )
        if delete_interim_results: print( ' Interim result images will be deleted after stitching!' )
        else: print( ' Interim result images wont be deleted after stitching.' )
    else: print( 'Deactivating ImageJ processing!' )

    print( '' )

def cmdExists(cmd):
    return shutil.which(cmd) is not None

def imageJInPATH():
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
    elif ( showDebuggingOutput ) : print( "Fiji/ImageJ found!" )
    return True

def MIST_Stitching( directory, x_tile_count, y_tile_count ):
    global home_dir
    command = "ImageJ-win64.exe -macro \"" + home_dir +"\mist_stitching_maps.ijm\" \"" + directory + "|" + os.path.dirname(os.path.dirname(directory)) + "|" + os.path.basename(workingDirectory) + "|" + x_tile_count + "|" + y_tile_count + "|\""

    print( "  starting ImageJ Macro..." )
    if ( showDebuggingOutput ) : print( '  ' + command )
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print( "  Error" )
        pass

def equalize_histogram( source ):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    return clahe.apply(source)

ref_loaded = False
ref_values = False
ref_counts = False
ref_quantiles = False
ref_avg_color = 0
def load_reference( path ):
    global ref_values
    global ref_counts
    global ref_quantiles
    global ref_avg_color
    global correctionAttempt
    reference = cv2.imread( path, 0 )#, mode='RGB')
    ref_gauss = cv2.GaussianBlur(reference,(5,5),cv2.BORDER_DEFAULT)
    reference_normalized = equalize_histogram( reference )
    #reference_histogram = cv2.calcHist( ref_gauss,[0], None, [8], [0,256] )
    ref_values, t_counts = np.unique( reference_normalized.ravel(), return_counts=True )
    ref_quantiles = np.cumsum(t_counts).astype(np.float64)
    ref_quantiles /= ref_quantiles[-1]
    if correctionAttempt: ref_avg_color = get_avg_color( reference_normalized )

#https://stackoverflow.com/questions/32655686/histogram-matching-of-two-images-in-python-2-x
def hist_matching( source, cropped_images = None ):
    global ref_values
    global ref_counts
    global ref_quantiles
    global ref_avg_color
    global showDebuggingOutput
    ignore_until_color = 0
    # x_values: color values from 0-255 for 8 bit
    # x_counts: counts of these color values
    src_values, bin_idx, src_counts = np.unique( source.ravel(), return_inverse=True, return_counts=True )
    
    # searching for the best fitting cropped image in the given list and trying to fit this image to the given histogram instead of the full image.
    if not cropped_images == None:
        avg_color_list = []
        for i in range(len(cropped_images)):# cropped_image in cropped_images:
            avg_color_list.append( get_avg_color( equalize_histogram( cropped_images[i] ) ) )
        closest_to_ref = min( range(len(avg_color_list)), key=lambda i: abs(avg_color_list[i]-ref_avg_color))
        alt_source = cropped_images[ closest_to_ref ].ravel()
        src_values = src_values
        alt_src_values, alt_src_counts = np.unique( alt_source.ravel(), return_counts=True )
        for j in range( len( src_values ) ):
            if src_values[j] not in alt_src_values:
                src_counts[j] = 0
            else:
                index = np.where( alt_src_values == src_values[j] )
                src_counts[j] = alt_src_counts[ index ]
        if showDebuggingOutput: print( "  - choosing tile " + str( closest_to_ref + 1 ) + " for calculation (" + str( avg_color_list[closest_to_ref] ) + " | " + str( ref_avg_color ) + ")!" )

    src_quantiles = np.cumsum( src_counts ).astype( np.float64 ) # cumultative sum of the counts
    src_quantiles /= src_quantiles[-1] # sum of all counts is normed to  (last value of the list)

    #apply the created histogram table to the image and save it
    interp_ref_values = np.interp( src_quantiles, ref_quantiles, ref_values )
    interp_ref_values = interp_ref_values.astype( source.dtype )
    return interp_ref_values[bin_idx].reshape( source.shape )

def sliceImage( workingDirectory, filename ):
    global showDebuggingOutput
    global col_count
    global row_count
    namePrefix = filename.split( '.' )
    image = cv2.imread( workingDirectory + '/' + filename, 0 )#tiff.imread( workingDirectory + '/' + filename )
    height, width = image.shape[:2]

    #cropping
    crop_height = int(height/row_count)
    crop_width = int(width/col_count)
    cropped_images = []
    for i in range(row_count): # start at i = 0 to row_count-1
        for j in range(col_count): # start at j = 0 to col_count-1
            cropped = image[(i*crop_height):((i+1)*crop_height), j*crop_height:((j+1)*crop_width)]
            cropped_images.append(cropped)

    image=None
    cropped=None
    if showDebuggingOutput: print( "  - cropped image to " + str( len( cropped_images ) ) + " parts")
    return cropped_images

def get_avg_color( source ):
    avg_color = np.average(source.ravel(), axis=0)
    avg_color = round( avg_color,1 )
    #print( "  - avg_color: " + str( avg_color ) )
    return avg_color

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
brightness_margin = 20
def make_black( source ):
    global criteria
    src_gauss = cv2.GaussianBlur(source,(5,5),cv2.BORDER_DEFAULT)
    compactness,labels,centers = cv2.kmeans( np.float32( src_gauss.ravel() ), 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS )
    centers = sorted( centers, reverse=True )
    lowest_maxima = int( round( centers[-1][0],0)  )
    #ignore_until_color = int( round( centers[-1][0],0)  ) + brightness_margin # ignore all black and dark-grey areas for better histogram matching if large pores exist
    print( "  - lowest maxima " + str( lowest_maxima ) )
    print( compactness )
    return lowest_maxima

### actual program start
processArguments()
if ( showDebuggingOutput ) : print( "I am living in '" + home_dir + "'" )
print( "Please select a reference image from the image set.", end="\r" )
referenceFilePath = filedialog.askopenfilename(title='Please select the reference image',filetypes=[("Tiff images", "*.tif;*.tiff")])
print( "                                                   ", end="\r" )
workingDirectory = os.path.dirname( referenceFilePath )
if ( showDebuggingOutput ) : print( "Selected working directory: " + os.path.dirname( referenceFilePath ) )
if ( showDebuggingOutput ) : print( "Selected reference file: " + os.path.basename( referenceFilePath ) )
outputDirName = 'corrected'
count = 0
position = 0
## count files
if os.path.isdir( workingDirectory ) :
    targetDirectory = workingDirectory + '/' + outputDirName + '/'
    # create output directory if it does not exist
    if not os.path.exists( targetDirectory ):
        os.makedirs( targetDirectory )

    for file in os.listdir(workingDirectory):
        if ( file.endswith( ".tif" ) or file.endswith( ".TIF" ) ):
            count = count + 1
print( str( count ) + " Tiffs found!" )
# load reference image
load_reference( referenceFilePath )

ignore_until_color = 0
if os.path.isdir( workingDirectory ) :
    ## processing files
    #hist_difference_sum = 0
    last_image_name = ""
    for file in os.listdir( workingDirectory ):
        if ( file.endswith( ".tif" ) or file.endswith( ".TIF" ) ):
            filename = os.fsdecode(file)
            position = position + 1
            print( " Analysing " + filename + " (" + str(position) + "/" + str(count) + ")" )
            source = cv2.imread(workingDirectory + "/" + file, 0)#, mode='RGB')
            if correctionAttempt:
                src_avg_color = get_avg_color( equalize_histogram( source ) )
                if src_avg_color < ref_avg_color - 5 or src_avg_color > ref_avg_color + 5:
                    #if showDebuggingOutput : 
                    print( "  - the image seems to have a big deviation from the reference image ( " + str( src_avg_color ) + " vs. " + str( ref_avg_color ) + " )" )
                    cropped_images = sliceImage( workingDirectory, filename )
                    matched = hist_matching( source, cropped_images )
                else:
                    matched = hist_matching( source )
            else:
                matched = hist_matching( source )
            cv2.imwrite( targetDirectory + filename, matched )
            last_image_name = filename
    #if ( showDebuggingOutput ) : print( round( hist_difference_sum, 4) )
    if ( runImageJ_Script and imageJInPATH() ):
        # Tile_005-005-000000_0-000.tif
        dim = last_image_name.split("_")
        # ..., 005-005-000000, ...
        dim = dim[1].split("-")
        # 005, 005, ...
        MIST_Stitching( targetDirectory, dim[0].lstrip("0"), dim[1].lstrip("0") )
        if delete_interim_results :
            shutil.rmtree( targetDirectory )
    else:
        if ( showDebuggingOutput ) : print( "...doing nothing!" )

print( "Script DONE!" )