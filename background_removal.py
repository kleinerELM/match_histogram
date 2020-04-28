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
    print("# A script to automatically remove a reoccuring shadow  #")
    print("# effect in a stack of microscopy images                #")
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
    usage = sys.argv[0] + " [-h] [-i] [-r] [-d]"
    try:
        opts, args = getopt.getopt(argv,"hird",["noImageJ="])
    except getopt.GetoptError:
        print( usage )
    for opt, arg in opts:
        if opt == '-h':
            print( 'usage: ' + usage )
            print( '-h,                  : show this help' )
            print( '-i, --noImageJ       : skip ImageJ processing' )
            print( '-r,                  : interim result images will be deleted after stitching [on]' )
            print( '-d                   : show debug output' )
            print( '' )
            sys.exit()
        elif opt in ("-i", "-noImageJ"):
            settings["runImageJ_Script"] = False
        elif opt in ("-r"):
            settings["delete_interim_results"] = True
        elif opt in ("-d"):
            print( 'show debugging output' )
            settings["showDebuggingOutput"] = True
    if settings["runImageJ_Script"]:
        print( 'Tiles will be stitched after the process!' )
        if settings["delete_interim_results"]: print( ' Interim result images will be deleted after stitching!' )
        else: print( ' Interim result images wont be deleted after stitching.' )
    else: 
        print( 'Deactivating ImageJ processing!' )
    print( '' )
    return settings

#https://stackoverflow.com/questions/33964913/equivalent-of-polyfit-for-a-2d-polynomial-in-python
def polyfit2d(x, y, z, kx=3, ky=3, order=None):
    # grid coords
    x, y = np.meshgrid(x, y)

    # coefficient array, up to x^kx, y^ky
    coeffs = np.ones((kx+1, ky+1))

    # solve array
    a = np.zeros((coeffs.size, x.size))

    # for each coefficient produce array x^i, y^j
    for index, (j, i) in enumerate(np.ndindex(coeffs.shape)):
        # do not include powers greater than order
        if order is not None and i + j > order:
            arr = np.zeros_like(x)
        else:
            arr = coeffs[i, j] * x**i * y**j
        a[index] = arr.flatten()

    # do leastsq fitting and return leastsq result
    return np.linalg.lstsq(a.T, np.ravel(z), rcond=None)

def calculateBackground( file, settings ):
    print( " calculating background of reference image" )
    
    kx = 1
    ky = 1
    #nWidth = 800
    image = cv2.imread( file, 0 )
    height, width = image.shape[:2]
    #print( "  " + str( width ) + " x " + str( height ) )
    #if ( width > nWidth ):
    #    height = int( round(nWidth/width*height,0) )
    #    width = nWidth
        #print( "  " + str( width ) + " x " + str( height ) )
    #    image = cv2.resize(image, (width, height))
        #height, width = image.shape[:2]
        #print( "  " + str( width ) + " x " + str( height ) )
    x = []
    y = []
    for i in range( height ):
        x.append(i)
    for i in range( width ):
        y.append(i)
    soln = polyfit2d( x, y, image, kx, ky )
    #print( soln )
    ImageFit = np.polynomial.polynomial.polygrid2d(x, y, soln[0].reshape((kx+1, ky+1))).astype(int)
    ImageFit = (ImageFit - 255) * (-1)
    minVal = min(ImageFit.ravel())
    #maxVal = max(ImageFit.ravel())
    #ImageFit = [j - minVal for j in ImageFit]
    return ImageFit- minVal

#fitted_surf = np.polynomial.polynomial.polyval2d(x, y, soln.reshape((kx+1,ky+1)))
#plt.matshow(fitted_surf)

def startProcess( file, settings, referenceBackground, position ):
    filename = os.fsdecode(file)
    print( " Analysing " + filename + " (" + str(position) + "/" + str( settings["count"] ) + ")" )
    
    image = cv2.imread( settings["workingDirectory"] + '/' + filename, 0 )
    #print( "1" )
    resultImage = referenceBackground + image
    #print( "2" )
    cv2.imwrite( settings["targetDirectory"] + filename, resultImage )
    #print( "3" )

### actual program start
if __name__ == '__main__':
    #remove root windows
    root = tk.Tk()
    root.withdraw()
    coreCount = multiprocessing.cpu_count()
    settings = {
        "runImageJ_Script" : True,
        "showDebuggingOutput" : False,
        "delete_interim_results" : True,
        "home_dir" : os.path.dirname(os.path.realpath(__file__)),
        "workingDirectory" : "",
        "targetDirectory"  : "",
        "referenceFilePath" : "",
        "last_image_name": "",
        "outputDirName" : "corrected",
        "count" : 0,
        "coreCount" : coreCount,
        "processCount" : (coreCount - 1) if coreCount > 1 else 1
    }

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
        referenceBackground = calculateBackground( settings["referenceFilePath"], settings )

        position = 0
        # processing files                
        pool = multiprocessing.Pool( settings["processCount"] )
        for file in fileList:
            position += 1
            #startProcess( file, workingDirectory, targetDirectory, position, count )
            pool.apply_async(startProcess, args=( file, settings, referenceBackground, position ) )

        pool.close()
        pool.join()

        # stitch using MIST
        sf.stitch( settings )
    else:
        print( "directory not found!" )

    print( "Script DONE!" )