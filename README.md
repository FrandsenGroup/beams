> First go at the the README (not complete but a start), haven't proofread or anything and still have more to add. The gifs and images are temporary of course since we still have a lot left to do with the program but they are good placeholders and give an idea of what I am thinking of doing.

### Features

- Convert binary data files from multiple µSR facilities.
- Display and interact with multiple sets of data.
- Write your data to a common file type.
- Compatible with Linux, Mac and Windows

#### Todo
- Converting nexus files
- Redesign user interface

# BEAMS
> A simple interface for visualizing and analyzing µSR data.

**Table of Contents**

## Getting Started

#### Prerequisites
- You only need to have Python 3 installed on your computer.

#### Installation
- Download or clone this repository.
- Open a terminal and navigate to the BEAMS folder.
- Run the following command to install the package requirements for BEAMS
```shell
$ pip install -r requirements.txt
```
- Start BEAMS with the following
```shell
$ python beams
```

## Usage

### Adding, Converting and Plotting Files
![animation for adding converting and plotting](https://github.com/aPeter1/BEAMS/blob/assets/addingconvertingplotting.gif)
- **Adding**: Simply use the '+' button and choose to either add from disk or, alternatively download from musr.ca (see below)
- **Converting**: Currently the program supports files from the ISIS and TRIUMF beam facilities.
- **Plotting**: Once converted, you can click plot which will prompt you to select two histograms from each file to use to create the asymmetry.

#### Downloading from musr.ca
> Currently the program can download data gathered at the TRUMF beam facility with just a little information.
![animation for downloading files from musr.ca](https://github.com/aPeter1/BEAMS/blob/assets/downloadingfrommusrca.gif)
- **Search**: If you do not have all required inputs you can search based on incomplete information.
- **Download**: This will download it to the current directory, or the directory specified. 

### Interacting with the Data
#### Using the plot options
![animation for using plot options](https://github.com/aPeter1/BEAMS/blob/assets/usingplotoptions.gif)
- **Toolbar**: The Matplotlib toolbar allows for a dynamic zooming in and out on certain areas of the data
- **Slider**: Sliding this while change the binning size of the data dynamically.
- **X and Y Limits**: These can be set here, or you can use the automatic settings.

#### Using the run display options
![picture of run display, numbered](https://github.com/aPeter1/BEAMS/blob/assets/rundisplaynumbered.PNG)
- **1. File Path**: File path of the current selected run.
- **2. Isolate**: This will isolate all currenlty selected runs on the plots
- **3. Color and Marker**: You can use the next two dropdown boxes to select the color and marker for the selected run.
- **4. See File**: This will open up a textbox with all the contents of the selected file.
- **5. See Hist**: A display of the selected histogram (specified by the dropdown box to the right), more detail given below.
- **6. Header Data**: The dropdown box and display will show the header data for given file
- **7. Current Runs**: All runs current read into the program.
- **8. Alpha Correction**: Apply the given alpha correction to the selected runs.
- **9. Integration**: Integrate the selected runs relative to temperature or magnetic field.
- **10. Plot All, Clear All**: Will plot all runs currently read in, or clear all runs from the program. 
- **11. Misc**: Additional visual options for the plots.

#### Using the histogram display
![animation for using histogram display](https://github.com/aPeter1/BEAMS/blob/assets/usinghistogramdisplay.gif)
- **Toolbar**: Navigate around the selected histogram.
- **Background Start, End and T0**: Set the new bin values for the section of the histogram to be used to calculate the background as well as the new T0.
