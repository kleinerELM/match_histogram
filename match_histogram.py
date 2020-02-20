import os, sys, getopt
import numpy as np
import tkinter as tk
import cv2
from scipy.spatial import distance
import scipy.ndimage as ndimage
from tkinter import filedialog
#remove root windows
root = tk.Tk()
root.withdraw()

print("#########################################################")
print("# match histogram test                                  #")
print("#                                                       #")
print("# © 2020 Florian Kleiner                                #")
print("#   Bauhaus-Universität Weimar                          #")
print("#   Finger-Institut für Baustoffkunde                   #")
print("#                                                       #")
print("#########################################################")
print()

#### directory definitions
home_dir = os.path.dirname( os.path.realpath(__file__) )

showDebuggingOutput = False

#### process given command line arguments
def processArguments():
    global outputDirName
    global showDebuggingOutput
    col_changed = False
    row_changed = False
    argv = sys.argv[1:]
    usage = sys.argv[0] + " [-h] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hd",[])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-d"):
            print( 'show debugging output' )
            showDebuggingOutput = True
    print( '' )


ref_loaded = False
ref_values = False
ref_counts = False
ref_quantiles = False

#https://stackoverflow.com/questions/32655686/histogram-matching-of-two-images-in-python-2-x
def hist_matching(source, reference, subslice = -1 ):
    global ref_values
    global ref_counts
    global ref_quantiles
    global ref_loaded
    global showDebuggingOutput
    
    # x_values: color values from 0-255 for 8 bit
    # x_counts: counts of these color values
    src_values, bin_idx, src_counts = np.unique( source.ravel(), return_inverse=True, return_counts=True )
    src_quantiles = np.cumsum( src_counts ).astype( np.float64 ) # cumultative sum of the counts
    src_quantiles /= src_quantiles[-1] # sum of all counts is normed to  (last value of the list)

    if not ref_loaded:
        ref_values, t_counts = np.unique( reference.ravel(), return_counts=True )
        ref_quantiles = np.cumsum(t_counts).astype(np.float64)
        ref_quantiles /= ref_quantiles[-1] 
        #if ( showDebuggingOutput ) : print( ref_quantiles )
        ref_loaded = True

    interp_ref_values = np.interp( src_quantiles, ref_quantiles, ref_values )
    #if ( showDebuggingOutput ) : print( interp_ref_values )
    interp_ref_values = interp_ref_values.astype( source.dtype )

    return interp_ref_values[bin_idx].reshape( source.shape )

""" def sliceImage( workingDirectory, filename ):
    col_count = 3
    row_count = 3
    outputDirName = "tmp"
    global showDebuggingOutput
    namePrefix = filename.split( '.' )
    image = tiff.imread( workingDirectory + '/' + filename )
    height, width = image.shape[:2]

    #cropping
    crop_height = int(height/row_count)
    crop_width = int(width/col_count)
    targetDirectory = workingDirectory + '/' + outputDirName + '/'
    for i in range(row_count): # start at i = 0 to row_count-1
        for j in range(col_count): # start at j = 0 to col_count-1
            targetDirectory = workingDirectory + '/' + outputDirName + '/' + namePrefix[0] + '/'
            ## create output directory if it does not exist
            if not os.path.exists( targetDirectory ):
                os.makedirs( targetDirectory )

            fileij = namePrefix[0] + "_" + str( i ) + "_" + str( j ) + ".tif"
            print( "   - " + fileij + ":" )
            cropped = image[(i*crop_height):((i+1)*crop_height), j*crop_height:((j+1)*crop_width)]
            cropped_filename = targetDirectory + fileij
            tiff.imwrite( cropped_filename, cropped ) #, photometric='rgb'
    image=None
    cropped=None """

### actual program start
processArguments()
if ( showDebuggingOutput ) : print( "I am living in '" + home_dir + "'" )
referenceFilePath = filedialog.askopenfilename(title='Please select the reference image',filetypes=[("Tiff images", "*.tif;*.tiff")])
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
reference = cv2.imread(referenceFilePath, 0)#, mode='RGB')
ref_gauss = cv2.GaussianBlur(reference,(5,5),cv2.BORDER_DEFAULT)
#reference_normalized = cv2.equalizeHist(reference)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
reference_normalized = clahe.apply(reference)
#reference_histogram = cv2.calcHist( ref_gauss,[0], None, [8], [0,256] )
## run actual code
if os.path.isdir( workingDirectory ) :
    ## processing files
    #hist_difference_sum = 0
    for file in os.listdir( workingDirectory ):
        if ( file.endswith( ".tif" ) or file.endswith( ".TIF" ) ):
            filename = os.fsdecode(file)
            position = position + 1
            print( " Analysing " + filename + " (" + str(position) + "/" + str(count) + ") :" )
            #sliceImage( workingDirectory, filename )
            source = cv2.imread(workingDirectory + "/" + file, 0)#, mode='RGB')
            """ 
            src_gauss = cv2.GaussianBlur(source,(5,5),cv2.BORDER_DEFAULT)
            source_histogram = cv2.calcHist( src_gauss,[0], None, [8], [0,256] )
            if ( showDebuggingOutput ) : print( "    - comparison: ", end="" )
            if ( showDebuggingOutput ) : print( round( cv2.compareHist( reference_histogram, source_histogram, cv2.HISTCMP_CORREL ), 3), end=", " )
            if ( showDebuggingOutput ) : print( round( cv2.compareHist( reference_histogram, source_histogram, cv2.HISTCMP_CHISQR ), 2), end=", " )
            if ( showDebuggingOutput ) : print( round( cv2.compareHist( reference_histogram, source_histogram, cv2.HISTCMP_INTERSECT ), 0), end=", " )
            if ( showDebuggingOutput ) : print( round( cv2.compareHist( reference_histogram, source_histogram, cv2.HISTCMP_BHATTACHARYYA ), 4) )
            """
            #print( reference_normalized.ravel() )
            #if ( showDebuggingOutput ) : print( round( , 4) )
            #hist_difference = distance.chebyshev( cv2.normalize(reference_histogram, reference_histogram).flatten(), cv2.normalize(source_histogram, source_histogram).flatten() )
            #hist_difference_sum += hist_difference
            #if ( showDebuggingOutput ) : print( round( hist_difference, 4) )
            matched = hist_matching( source, reference_normalized )
            cv2.imwrite( targetDirectory + filename, matched )
    #if ( showDebuggingOutput ) : print( round( hist_difference_sum, 4) )

print( "Script DONE!" )