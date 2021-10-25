
### Features

- Convert binary data files from multiple µSR facilities.
- Display and interact with multiple sets of data.
- Write your data to a common file type.
- Compatible with Linux, Mac and Windows

# BEAMS
> A simple interface for visualizing and analyzing µSR data.

**Table of Contents**

## Getting Started

### Prerequisites
- Python 3.6 or greater

### Installation
- Download or clone this repository.
- Open a terminal and navigate to the BEAMS folder.

#### Without Anaconda
- Run the following command to install the package requirements for BEAMS
```shell
$ python -m pip install -r python_requirements.txt
```
#### Anaconda
- Run the following command in the anaconda prompt to install requirements.
```shell
$ conda install -c anaconda --file conda_requirements.txt
```

Start BEAMS for either, once you have navigated to the directory with the following
```shell
$ python beams
```

## User Guide


### Loading Files
By clicking the + button in the top left corner you will launch a prompt with four options of adding files. 
From disk (your computer), and then three different facilities: Triumf, PSI and ISIS. 

When you download files from one of the three facilities, they need to be converted from their binary format
to a format that our program can work with. You can do this by 'checking' the box next to each file you want
to convert and pressing the 'convert' button. New files with the '.dat' extension will be created.

Once you have files in a format that our program can read you select the files you want to work with by checking
the boxes and clicking the 'load' button. This loads the data from these files into the program and you are now
ready to interact with the data. 

### Plotting Asymmetries
#### Plotting the Asymmetry
Once your files are loaded, if they are files that can be plotted then they will show up in the file tree below 
the plotting buttons. Depending on the type of file you loaded, checking the box next to the file and clicking 
'plot' may do one of three things. 

If it is a '.dat' file, a file which contains histograms, a prompt will appear which will ask you to select which 
histograms should be used to calculate the asymmetry for that particular file. If you intend to use the same histograms
for a large selection of files then you can press 'Apply All', otherwise you can press 'Apply' and specify for each file
individually.

If it is a '.asy' file, a file which contains an asymmetry, then the asymmetry will be plotted as no more
information is needed.

If it is a '.fit' file, a file which contains an experimental asymmetry and an asymmetry calculated from a fit then
the experimental asymmetry will be plotted with another plotted line for the calculated asymmetry.

#### Interacting with the Asymmetry
Once your asymmetry is plotted, you can now dynamically interact with it! You can experiment with this by moving 
the slider below each plot to adjust the binning of the asymmetry and adjust the x and y limits to focus in on different
areas. In the left side panel you will see the legend for the plots, as well as options for styling and adjusting
the alpha parameter for the asymmetry.

### Fitting Asymmetries
#### Choosing your Fit Expression


## File Formats

### External Supported File Formats
NOTE: Support for ISIS files is currently on the docket, but not yet supported.

File Extension | Description
-------------- | -----------
.msr | Histogram data from TRIUMF
.bin | Histogram data from PSI
.mdu | Histogram data from PSI

### BEAMS File Formats
File Extension | Description
-------------- | -----------
.dat | Histogram data for a single run.
.asy | Experimental asymmetry, uncertainty and time for a single run.
.fit | Experimental and calculated asymmetry, uncertainty and time for a single run.
.clc | A verbose summary of a fit
.beams | A saved beams session

## Troubleshooting
#### Can't install requirements on Mac (Apple Silicon)
For trouble installing requirements on Apple Silicon see the answer to this issue: https://github.com/scipy/scipy/issues/13409

#### Text in file trees is truncated
If the text is truncated or the items on the screen are misaligned slightly you most likely don't have PyQt5 installed (you can confirm this by running `pip freeze` in the terminal and you will probably see QtPy). Simply fix by using pip to install PyQt5.
 
```shell
$ pip install PyQt5
```

#### (PyQt5) ImportError: DLL load failed
Resolved in this issue #37\
Possible solution in the answer to this question on Stack Overflow: https://stackoverflow.com/questions/42863505/dll-load-failed-when-importing-pyqt5
