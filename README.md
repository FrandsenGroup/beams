![beams logo](beams/app/resources/icons/logo.png)
[![Release](https://img.shields.io/github/release/FrandsenGroup/beams.svg?style=plastic&colorB=68B7EB)]()
###  Features

- Convert binary data files from multiple µSR facilities.
- Display and interact with multiple sets of data.
- Write data to a common file type.
- Compatible with Linux, Mac and Windows

# BEAMS
> A simple interface for visualizing and analyzing µSR data.

## Table of Contents
- [Getting Started](#getting-started)
- [User Guide](#user-guide)
  - [Loading Files](#loading-files)
  - [Plotting Asymmetries](#plotting-asymmetries)
    - [Plotting the Asymmetry](#plotting-the-asymmetry)
    - [Interacting with the Asymmetry](#interacting-with-the-asymmetry)
    - [Integrating the Asymmetry](#integrating-the-asymmetry)
    - [Exporting Data](#exporting-asymmetry-data)
  - [Fitting Asymmetries](#fitting-asymmetries)
    - [Choosing your Fit Expression](#choosing-your-fit-expression)
    - [Specifying your Fit Parameters](#specifying-your-fit-parameters)
    - [Parameter Table](#config)
      - [Config](#config)
      - [Batch](#batch)
      - [Output](#output)
    - [Exporting Data](#exporting-fit-data)
  - [Interacting with Histograms](#interacting-with-histograms)
    - [Navigation Bar](#navigation-bar)
    - [Adjusting Values](#adjusting-values)
  - [Other Features](#other-features)
    - [Save and Load Session](#save-and-load-session)
    - [Change Appearance](#change-appearance)
- [File Formats](#file-formats)
  - [External File Formats](#external-supported-file-formats)
  - [BEAMS File Formats](#beams-file-formats)
- [Troubleshooting](#troubleshooting)

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
By clicking the [+] button in the top left corner you will launch a prompt with four options of adding files. 
From disk (your computer), and then three different facilities: Triumf, PSI and ISIS. Clicking the [-] button will remove
all the the files currently checked.

<img src="https://github.com/aPeter1/BEAMS/blob/assets/file_panel_example.png" width="400" />

When you download files onto your computer from one of the three facilities, they need to be converted from their binary format
to a format that our program can work with. You can do this by 'checking' the box next to each file you want
to convert and pressing the 'convert' button. New files with the '.dat' extension will be created.

Once you have files in a format that our program can read you select the files you want to work with by checking
the boxes and clicking the 'load' button. This loads the data from these files into the program, and you are now
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

![choosing your histograms for asymmetry](https://github.com/aPeter1/BEAMS/blob/assets/histogram_choice_dialog.png)

If it is a '.asy' file, a file which contains an asymmetry, then the asymmetry will be plotted as no more
information is needed.

If it is a '.fit' file, a file which contains an experimental asymmetry, and an asymmetry calculated from a fit then
the experimental asymmetry will be plotted with another plotted line for the calculated asymmetry.

#### Interacting with the Asymmetry
Once your asymmetry is plotted, you can now dynamically interact with it! You can experiment with this by moving 
the slider below each plot to adjust the binning of the asymmetry and adjust the x and y limits to focus on different
areas. On the left side panel you will see the legend for the plots, as well as options for styling and adjusting
the alpha parameter for the asymmetry.

![choosing your histograms for asymmetry](https://github.com/aPeter1/BEAMS/blob/assets/plot_interaction.png)

<br>

## Interacting with Histograms
When you navigate to the histogram tab, you will be able to see the histograms for each loaded run and adjust meta values associated with them.

<img src="https://github.com/aPeter1/BEAMS/blob/assets/left_panel_example.png" width="400" />

Upon first opening the tab, you will see this window on the left side panel. From here you can expand a specific run and click on the histogram you want to work with. You should see the histogram displayed on the screen.

Above the panel where you select histograms, you will see three buttons. Descriptions provided below.

###### See File
This will open up a small window displaying the contents of the file the run was loaded from. You cannot save changes from this prompt, it is purely for reference.

###### Reset
This will undo all changes you have made in this tab to the values of histograms that are CURRENTLY SELECTED in the panel below. If you  have clicked save, those changes that were saved can not be undone (aside from setting the old values and saving again).

###### Save
This will save all changes you have made in this tab to the values of histograms that are CURRENTLY SELECTED. Once you save, all affected asymmetries will be recalculated, and you should see the changes shown appropriately in the plotting tab.

### Navigation Bar

Depending on your purpose and the histogram, this may be a bit unwieldy to work with which is why a navigation bar is provided across the top of the tab. 

![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/navigation_bar_example.png)

There are six buttons provided. They are described below in the order they appear on the bar.

###### Home
Pressing this button will undo all the changes (zooming and panning) that have visually been done to the display below. Useful if you've lost your spot panning around or zoomed in on the wrong area.

###### Undo
This will undo the last action you made (zooming or panning).

###### Redo
This will redo the last action that was undone.

###### Pan
This will allow you to move around the plotted histogram.
- Note - Once you have pressed this button, you need to press it again to unselect the action.

###### Zoom
This will allow you to zoom in on specific portions of the plot (you can still see the whole plot if you pan around).
- Note - Once you have pressed this button, you need to press it again to unselect the action.

###### Save
This will allow you to save what is currently displayed as an image file. 

![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/zoom_and_pan_example.gif)

### Adjusting Values
Like other features in BEAMS, we try to make this adjusting values as intuitive and dynamic as possible. Below the navigation toolbar you will see a box with some (by default) disabled areas. As stated in the instructions, you will need to 'Check' the box to the left of the disabled options in order to enable them. 

This is because, as seen in the image below, you can either specify the values for each in the input boxes OR use your mouse to select on the plot where you want those values to be. This can be an issue if, at the same time for example, you have the zoom feature also selected and are trying to navigate around the plot. 

![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/adjusting_values_example.gif)

There are five values you can adjust for each histogram. In order to move those values across the plot with your mouse, you need to have the radio button next to that value selected.

###### Background Start/End
These values define the section of the histogram which will be used to calculate the background radiation of the run.

###### T0
This value defines the start time of the run. 

###### Good Bin Start/End
These values define the section of the histogram which will be used to calculate the asymmetry.

<br>

### Fitting Asymmetries
#### Choosing your Fit Expression
![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/expression_input.png)

Near the top of the fitting tab you can see an area where you can provide the fitting expression as a function of 't'. Operations must be typed out explicitly (i.e. use '5*x' rather then '5x'). If the expression you provide is invalid, the box will be highlighted in red.

<br>

![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/saved_expressions.png)

Above the input for the expression you will see two boxes. The box on the left (Predefined Functions) contains some common function definitions that come loaded with the program. You can select the template you want to use and press 'Insert'. This will insert the function into the expression input box below (wherever your cursor is at in the box or at the end of the input if your cursor is not in it).

The box on the right (User Defined Functions) allows you to create a new function definition (with a specified name) and save it for future use. You can select from previously saved definitions and press 'Insert' to achieve the same behavior as described above.

<br>


Reserved Symbols | + | - | * | / | ^ | i | e | π | pi
--- | --- | --- | --- | --- | --- | --- | --- | --- | ---

Functions - f(...) | sin | cos | tan | sinh | cosh | tanh | exp
--- | --- | --- | --- | --- | --- | --- | ---



<br>

#### Specifying your Fit Parameters
When you provide a valid fit expression you will see the table of parameters, and the plot display below the input box update as you type. Below is an example of valid input.

![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/example_fit_expression.png)

As you can see, the fit expression has two free variables (λ and β) and a third variable 'α' (this is a reserved symbol for the alpha value of the asymmetry). All three of these are accounted for in the parameter table.

The parameter table also has three separate sections you can interact with; Config, Batch and Output. Each of the three will be explained in depth. 

###### Config

This is the first section of the parameter table shown above. There will be a row for each parameter and an additional row for α. For each parameter you can adjust the initial value used in the fit, the lower and upper bounds for that parameter, and whether or not that parameter should be fixed to the value provided.

- Note - Adjusting a free variable will be reflected in the fit lines in the plot display. Adjusting alpha will be reflected in the asymmetry being plotted.

###### Batch

In the second section of the parameter table, you will once again see rows for each parameter with two new columns for each; 
Global and Run-Specific. For each parameter, you can only have ONE box checked (checking one will make the other box uncheckable).

<img src="https://github.com/aPeter1/BEAMS/blob/assets/example_batch.png" width="400" />

By checking global, you are indicating that you want the parameter to be fit across all datasets - not individually for each.

By checking run-specific, you are indicating that you want to be able to specify every column in the config section 
(even the fixed column) individually for each run for that particular parameter. For example, you set the initial value for λ for one run to 
2.0 and for another run to 3.0. By default, when you set the value that will be the initial value for every single run.

- In order to assign values to individual runs, you select the runs (as shown below) and while they are selected you adjust the values in the config table. You will then find as you click through each run that the values have been applied and remembered.


- If you select multiple runs that have conflicting values in one column or another for a parameter marked as run-specific, you will see a ' * ' in that cell or, if it is the fixed column, you will see a partial checkmark. If you adjust that cell then all conflicting values will be overwritten, otherwise if you don't edit it then they will remain unchanged.

<img src="https://github.com/aPeter1/BEAMS/blob/assets/example_run_list.png" width="400" />

###### Output

In the third section of the parameter table, you will see rows for each parameter and two new columns; Value and Uncertainty. These columns are only filled out after you have run a fit. When you select a fit on the left hand side panel, the value and uncertainty of the calculated parameters will be displayed here. If you select multiple fits at one time, a ' * ' will be placed in cells where there are conflicting values. 

<img src="https://github.com/aPeter1/BEAMS/blob/assets/example_output.png" width="400" />


#### Specifying the Range and Bin-Size to Use
Similar to the settings in the tab where we plot the asymmetries, in this tab there are options directly below the display where you can adjust the range and bin-size of the asymmetry to be used in the fit. These setting will be applied to all runs used in the fit.

#### Fitting
Once you have your fit expression and parameters set you need to check the box next to each run that you want to be part of the fit. Once they are all checked, you can click [Fit] and a loading popup will come up until the fit is finished.

#### Fit Results
##### Viewing Results
Once your fit is complete, it will appear in the left-side panel (reference the image below). You will see a parent node (with the current timestamp as the name, you can right-click -> rename to change this) with a child node for each run you 
chose to include in the fit. If you select one of the children nodes, you will see the asymmetry and the fit line for that particular run shown in the display. If you select the parent node, you will see the asymmetries and fit lines for every
run included in the fit. Additionally, you can ctrl-click or shift-click to select a custom range of fits to display.

Every run currently being displayed will have the color in the display shown to the left of the name of the run.

![beams logo](https://github.com/aPeter1/BEAMS/blob/assets/fitting-runs-example.gif)

##### Saving Results
If you right-click on a single fit, a range of fits or a parent node in the left-side panel you will see the option to 'save' these fits. If you click it, you will see a prompt which will offer several choices.

![dialog for writing fit data](https://github.com/aPeter1/BEAMS/blob/assets/write-fit-dialog.png)

The 


## File Formats

### External Supported File Formats

| File Extension | Description                |
|----------------|----------------------------|
| .msr           | Histogram data from TRIUMF |
| .bin           | Histogram data from PSI    |
| .mdu           | Histogram data from PSI    |
| .nxs_v2        | Histogram data from ISIS   |

### BEAMS File Formats
| File Extension | Description                                                                   |
|----------------|-------------------------------------------------------------------------------|
| [.dat](https://github.com/aPeter1/BEAMS/blob/assets/histogram_example.dat)            | Histogram data for a single run.                                              |
| [.asy](https://github.com/aPeter1/BEAMS/blob/assets/asymmetry_example.asy)            | Experimental asymmetry, uncertainty and time for a single run.                |
| [.fit](https://github.com/aPeter1/BEAMS/blob/assets/summary_example.fit)            | Experimental and calculated asymmetry, uncertainty and time for a single run. |
| [.calc](https://github.com/aPeter1/BEAMS/blob/assets/fit_example.calc)         | A verbose summary of a fit                                                    |
| .beams          | A saved beams session                                                         |

## Troubleshooting
#### Can't install requirements on Mac (Apple Silicon)
For trouble installing requirements on Apple Silicon see the answer to this [issue](https://github.com/scipy/scipy/issues/13409).

```shell
$ brew install openblas
$ pip install cython pybind11 pythran numpy
$ OPENBLAS=$(brew --prefix openblas) CFLAGS="-falign-functions=8 ${CFLAGS}" pip install --no-use-pep517 scipy
```

#### Text in file trees is truncated
If the text is truncated or the items on the screen are misaligned slightly you most likely don't have PyQt5 installed (you can confirm this by running `pip freeze` in the terminal and you will probably see QtPy). Simply fix by using pip to install PyQt5.
 
```shell
$ pip install PyQt5
```

#### (PyQt5) ImportError: DLL load failed
Resolved in this [Issue 37](../../issues/37)

Possible solution in the answer to this question on Stack Overflow: https://stackoverflow.com/questions/42863505/dll-load-failed-when-importing-pyqt5

#### Histogram navigation toolbar is not loading
There is an open issue for this ([Issue 97](../../issues/97)). As of right now we do not have a solution. Consider uninstalling and reinstalling the python library 'matplotlib' and 'PyQt5'. 

#### My files from TRIUMF, PSI, or ISIS aren't being converted
Please open up an issue if this happens as it means we need to update the executables.
