// Macro for ImageJ 1.52d for Windows
// written by Florian Kleiner 2019
// run from command line as follows
// ImageJ-win64.exe -macro "C:\path\to\mist_stitching_maps.ijm" "D:\path\to\data\|outputFolder"

// NOTICE!
// the following parameters depend on you computer and setup
// to determine the correct parameters, start macro recording and then init a MIST stitching using your machine with activated CUDA
numcputhreads = 12;
cudadevice0id = 0;
cudadevice0name = "GeForce GTX 1060 6GB";
cudadevice0major = 6;
cudadevice0minor = 1;

// End of device depending variables

macro "mist_stitching_maps" {
	// check if an external argument is given or define the options
	arg = getArgument();
	if ( arg == "" ) {
		folder = getDirectory("Choose a Directory");
		//define number of slices for uniformity analysis
		outputDirName	 = "result";
		outputFolder = folder + "/" + outputDirName+ "/";
		outputPrefix = "result-";
		tilesX = 5;
		tilesY = 5;
	} else {
		print("arguments found");
		arg_split = split(getArgument(),"|");
		folder			= arg_split[0];
		outputFolder	= arg_split[1];
		outputPrefix	= arg_split[2];
		tilesX			= arg_split[3];
		tilesY			= arg_split[4];
	}
	print("Starting process using the following arguments...");
	print("  Directory: " + folder);
	print("  Output Folder: " + outputFolder);
	print("  Tiles in x direction: " + tilesX);
	print("  Tiles in y direction: " + tilesY);
	print("------------");
	
	//directory handling
	File.makeDirectory(outputFolder);
	//list = getFileList(folder);
	fijiPath = getDirectory("imagej");
	print( fijiPath );
	pattern = "Tile_0{rr}-0{cc}-000000_0-000.tif";
	overlap = "10.5";
	run("MIST", "gridwidth=5 gridheight=5 starttilerow=1 starttilecol=1 imagedir=["+ folder +"] filenamepattern="+pattern+" filenamepatterntype=ROWCOL gridorigin=UL assemblefrommetadata=false globalpositionsfile=[] numberingpattern=HORIZONTALCOMBING startrow=0 startcol=0 extentwidth=" + tilesX + " extentheight=" + tilesY + " timeslices=0 istimeslicesenabled=false outputpath=["+outputFolder+"] displaystitching=true outputfullimage=true outputmeta=false outputimgpyramid=false blendingmode=LINEAR blendingalpha=NaN outfileprefix=[" + outputPrefix +" ] programtype=CUDA numcputhreads=" + numcputhreads + " loadfftwplan=true savefftwplan=true fftwplantype=MEASURE fftwlibraryname=libfftw3 fftwlibraryfilename=libfftw3.dll planpath=[" + fijiPath + "\lib\fftw\fftPlans] fftwlibrarypath=[" + fijiPath + "lib\fftw] stagerepeatability=200 horizontaloverlap=" + overlap + " verticaloverlap=" + overlap + " numfftpeaks=0 overlapuncertainty=NaN isusedoubleprecision=true isusebioformats=false issuppressmodelwarningdialog=false isenablecudaexceptions=false translationrefinementmethod=SINGLE_HILL_CLIMB numtranslationrefinementstartpoints=16 headless=false cudadevice0id=" + cudadevice0id + " cudadevice0name=[" + cudadevice0name + "] cudadevice0major=" + cudadevice0major + " cudadevice0minor=" + cudadevice0minor + " loglevel=MANDATORY debuglevel=NONE");
	//selectWindow(outputPrefix+" Full_Stitching_Image");
	//run("Enhance Contrast...", "saturated=0.3 normalize");
	//saveAs("Tiff", outputFolder + cutName );
	
	// exit script
	print("Done!");
	if ( arg != "" ) {
		//run("Quit");
	}
}
