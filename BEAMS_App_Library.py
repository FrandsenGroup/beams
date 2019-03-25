# Basic and Efficient Analysis for Muon Spin-Spectroscopy (BEAMS)

# PyQt5 Libraries cover the main structure and function of the application
from PyQt5 import QtWidgets, QtGui, QtCore

# Matplotlib covers the plotting of the data, with necessary PyQt5 crossover libraries
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Numpy for all our fun array shenanigans
import numpy as np

# Pandas for dealing with our biiiig arrays
import pandas as pd

# OS for dealing with files
import os

# sys for some debugging
import sys

# scipy for the fourier transform
from scipy.interpolate import spline
import scipy.fftpack as syfp
import scipy as sy


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        # CLASS OVERVIEW
        # Serves as the parent class that will hold all the panel objects you see on the left, bottom and
        # right sides. All of the panels are docking widgets so that the user can remove them if they want
        # to enlarge the plotting area.
        super(Window,self).__init__()
        self.initUI()

    def initUI(self):
        # FUNCTION OVERVIEW
        # First off, the reason why we want to inherit from the QtWidgets.QMainWindow 
        # class is so that we can utilize all of the GUI aspects that QT gives us 
        # out of the gate, but we still want to wind up creating our own class for 
        # customization.

        # We use super so that this window returns the parent object, so that it 
        # acts like a QT object.

        # Notice now that to reference various aspects, we use "self." Self 
        # references the current class, which, again, is a QT object, so this means 
        # with self. we can reference all of the methods that we've inherited from 
        # QtWidgets.QMainWindow, as well as any methods we write ourselves in this 
        # class.

        self.setGeometry(200, 100, 1500, 900)
        self.setWindowTitle("BEAMS | Basic and Effective Analysis for Muon Spin-Spectroscopy")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        self.Create_MenuBar()

        self.Create_FileManager()

        self.Create_GraphEditor()

        self.Create_GraphArea()

        self.Create_RunInfoPanel()

        self.show()

    def Create_MenuBar(self):
        # FUNCTION OVERVIEW
        # Initializes the menubar across the top of the main window, as well as the status
        # bar on the bottom of the window. Still need to add functionality to these items.

        #Exit Menu Item
        exitAct = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)        
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(QtWidgets.qApp.quit)

        #New Session Menu Item
        newSesAct = QtWidgets.QAction(QtGui.QIcon('newsession.png'), '&New Session', self) 
        newSesAct.setShortcut('Ctrl+N')
        newSesAct.setStatusTip('Create a new session')  
        #Load Session Menu Item
        openSesAct = QtWidgets.QAction(QtGui.QIcon('opensession.png'), '&Open Session', self) 
        openSesAct.setShortcut('Ctrl+O')
        openSesAct.setStatusTip('Open old session')
        #Save Session Menu Item
        saveSesAct = QtWidgets.QAction(QtGui.QIcon('savesession.png'), '&Save Session', self) 
        saveSesAct.setShortcut('Ctrl+S')
        saveSesAct.setStatusTip('Save current session')

        #Add Data Files
        addDataAct = QtWidgets.QAction(QtGui.QIcon('addDada.png'), '&Add Data File', self) 
        addDataAct.setStatusTip('Add a data file to current session')

        #Menubar layout setup
        self.statusBar()
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(newSesAct)
        fileMenu.addAction(openSesAct)
        fileMenu.addAction(saveSesAct)
        fileMenu.addSeparator()
        fileMenu.addAction(addDataAct)
        fileMenu.addSeparator()
        fileMenu.addAction(exitAct)
        fileMenu = menubar.addMenu('&Help')        

    def Create_FileManager(self):
        # FUNCTION OVERVIEW
        # Creates an object of the FileManagerPanel class (this is the panel that opens on the left side
        #  of the window). Assign the parent as self (Window) and dock on the left side.
        self.fileControl = FileManagerPanel(parent=self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.fileControl)

    def Create_GraphEditor(self):
        # FUNCTION OVERVIEW
        # Creates an object of the GraphEditorPanel class (this is the panel that opens on the bottom of 
        # the window). Assign the parent as self (Window) and dock on the bottom.
        self.graphEditor = GraphEditorPanel(parent=self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.graphEditor)

    def Create_GraphArea(self):
        # FUNCTION OVERVIEW
        # Creates an object of the GraphAreaPanel class (this is the panel takes up the center of the window
        # and holds the graphs). Assign the parent as self (Window) and set as central widget.
        self.graphArea = GraphAreaPanel(parent=self)
        self.setCentralWidget(self.graphArea)

    def Create_RunInfoPanel(self):
        # FUNCTION OVERVIEW
        # Creates an object of the RunInfoPanel class (this is the panel that opens on the right side of
        # the window). Assign the parent as self (Window) and dock on the right side.
        self.runInfo = RunInfoPanel(parent=self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.runInfo)


class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        # CLASS OVERVIEW
        # The FileManagerPanel is a DockWidget, whos main component is a ListWidget and bar of buttons along
        # the top allowing the user to import files, and plot and export runs. The ListWidget holds a list of
        # checkboxes and run names.

        super(FileManagerPanel,self).__init__()
        self.setParent(parent)
        self.filenames = []
        self.initUI(parent)

    def initUI(self,parent):
        # FUNCTION OVERVIEW
        # Creates and brings together all the pieces that make up the panel. Note on Layout: QVBoxLayout 
        # and QHBoxLayout are used here and in the other classes to set up the grid for the panels and 
        # the widgets on them.
        self.setWindowTitle("File Manager")

        tempWidget = QtWidgets.QWidget()

        writeButton = QtWidgets.QPushButton()
        writeButton.setText("Write")
        writeButton.released.connect(lambda: self.Write_Button())

        addButton = QtWidgets.QPushButton()
        addButton.setText("Import")
        addButton.released.connect(lambda: self.Add_Button())

        plotButton = QtWidgets.QPushButton()
        plotButton.setText("Plot")
        plotButton.released.connect(lambda: self.Plot_Button(parent))

        hbox_one = QtWidgets.QHBoxLayout()
        hbox_one.addWidget(writeButton)
        hbox_one.addWidget(plotButton)
        hbox_one.addWidget(addButton)

        self.listWidget = QtWidgets.QListWidget()

        hbox_two = QtWidgets.QHBoxLayout()
        hbox_two.addWidget(self.listWidget)

        vbox_one = QtWidgets.QVBoxLayout()
        vbox_one.addLayout(hbox_one)
        vbox_one.addLayout(hbox_two)
        tempWidget.setLayout(vbox_one)

        self.setWidget(tempWidget)
        self.setFloating(False)

    def Write_Button(self):
        # FUNCTION OVERVIEW
        # This will allow you to export the calculated time, asymmetry, error and uncertainty arrays; once I 
        # figure out how to calculate those.
        return

    def Add_Button(self):
        # FUNCTION OVERVIEW 
        # Prompt user for files to import and add those files to the self.filenames array for the 
        # FileManagerPanel Object

        # Open File-Dialog for user to select files to import
        filename = QtWidgets.QFileDialog.getOpenFileNames(self,'Add file','/home')

        for file_index in range(len(filename[0])):
            # Using the OS Library break the file into the file_path, file_base, and file_ext
            # i.e. "C:/Users/kalec/Documents/" and "006515" and ".msr" respectively
            file_path, file_root = os.path.split(filename[0][file_index])
            file_base, file_ext = os.path.splitext(os.path.basename(file_root))

            # If it is a MUD file it must be imported to a .dat file and then add file to object array
            if(file_ext == ".msr"):
                self.Import_MUD_File(filename[0][file_index])
            self.filenames.append(file_path+"/"+file_base+".dat")

            # Display the file_base in the file manager on the left side, with a check
            file_item = QtWidgets.QListWidgetItem(file_base,self.listWidget)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

            # self.Import_MUD_File(filename[0]) # FIXME Eventually we will want to import the .msr
            # to .dat files. Once we get this silly c code to run from python.
            # FIXME Instead of showing the filename we should change it to show the run title.

    def Import_MUD_File(self, filename):
        # FUNCTION OVERVIEW
        # FIXME This function will take the date from .msr and create a .dat with the same name
        # then it will call Read_DatFile to read in the .dat file it just created. Some day.
        # mud_lib = ctypes.CDLL(BEAMS_MUDlib.so)
        # libMUD = CDLL(r"C:\Users\kalec\Documents\Research_Frandsen\Visualizing_uSR\BEAMS\mud\src\BEAMS_MUDlib.dll")
        return

    def Plot_Button(self,parent):
        # FUNCTION OVERVIEW 
        # This button will call the Read_Dat_Files on the RunInfoPanel object to get the basic run info 
        # and initial asymmetry and time arrays.

        # Read in .dat files (see Read_Dat_Files in the RuInfoPanel Class for more info)
        parent.runInfo.Read_Dat_Files(parent)
    
        # Update canvas one (the two axes on the left of the graphing area)
        parent.graphArea.canvas_one.Plot_Data(parent.graphEditor.xmin_one.text(), parent.graphEditor.xmax_one.text(),
            parent.graphEditor.slider_one.value(),"SLIDER_RELEASED", parent)
        
        # Update canvas two (the two axes on the right of the graphing area)
        parent.graphArea.canvas_two.Plot_Data(parent.graphEditor.xmin_two.text(), parent.graphEditor.xmax_two.text(),
            parent.graphEditor.slider_two.value(),"SLIDER_RELEASED", parent)

    def Get_Filenames(self):
        # FUNCTION OVERVIEW
        # See below ...
        return self.filenames

    def Get_Checked_Filenames(self):
        # FUNCTION OVERVIEW 
        # Run through the file list on the GUI and check which filenames are checked by the user. Those are 
        # the ones that will be returned. 
        checked_items = []
        for index in range(self.listWidget.count()):
            if self.listWidget.item(index).checkState() == QtCore.Qt.Checked:
                checked_items.append(self.filenames[index])
        return checked_items


class GraphAreaPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        # CLASS OVERVIEW 
        # This DockWidget holds all the the figures that the runs will be plotted on.
        super(GraphAreaPanel,self).__init__()
        self.setParent(parent)
        self.initUI()
        plt.ion() # Interative mode on so the figures can be updated.

    def initUI(self):
        # FUNCTION OVERVIEW
        # Creates the two figures (two axes each) that the runs will be plotted on and stores them on the 
        # main DockWidget.
        self.setWindowTitle("Graphing Area")
        tempWidget = QtWidgets.QWidget()

        self.canvas_one = PlotCanvas(parent=self)
        self.canvas_two = PlotCanvas(parent=self)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.canvas_one)
        hbox.addWidget(self.canvas_two)
        tempWidget.setLayout(hbox)

        self.setWidget(tempWidget)


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # CLASS OVERVIEW
        # There are two objects of the PlotCanvas class, each holds two axis (one from the time domain and one for the frequency domain
        # of the asymmetry) with the specified xmin and xmax and bin_size chosen by the user in the GraphEditorPanel
        fig = plt.figure(dpi=dpi)
        
        self.axes_time = fig.add_subplot(211,label="Time Domain")
        self.axes_freq = fig.add_subplot(212,label="Frequency Domain")

        self.axes_time.spines['right'].set_visible(False)
        self.axes_time.spines['top'].set_visible(False)
        self.axes_time.tick_params(bottom=False, left=False)
        self.axes_time.set_xlabel("Time ("+chr(956)+"s)")
        self.axes_time.set_ylabel("Asymmetry")

        self.axes_freq.spines['right'].set_visible(False)
        self.axes_freq.spines['top'].set_visible(False)
        self.axes_freq.tick_params(bottom=False, left=False)
        self.axes_freq.set_xlabel("Frequence (MHz)")
        self.axes_freq.set_ylabel("Magnitude")
        self.axes_freq.set_yticklabels([])
        
        FigureCanvas.__init__(self,fig)
        
        self.new_times = np.array([])
        self.new_asymmetry = np.array([])

        self.setParent(parent)

    def Import_Data(self,parent):
        # FUNCTION OVERVIEW
        # FIXME This function may be deleted, I was originally going to do the import from the .msr files from here but I may do that 
        # when the user adds the files instead.
        checked_items = parent.fileControl.Get_Filenames()
        print(checked_items)
        for index in range(len(checked_items)):
            print(index)

    def Plot_Data(self, xmin, xmax, bin_size, slider_state, parent):
        # FUNCTION OVERVIEW
        # This function clears the current plots from the graph, if any, and plots the currently selected files in the FileManagerPanel
        # on the axes. The fourier transform is not updated while the user is moving the slider for the bin size due to the lag, so it will
        # only be updated when the user releases the slider.
        self.axes_time.clear()
        self.axes_freq.clear()

        for graph_index in range(len(parent.runInfo.data_array)):
            self.Update_Asymmetry_Bins(xmin, xmax, bin_size, slider_state, parent, graph_index)
            graph_styles = parent.runInfo.data_array[graph_index].Get_Graphing_Styles()
            # Put an if else statement for whether or not the color is specified. (It should be initialized to none, so this goes down the usual path)
            self.axes_time.set_xlim(float(xmin),float(xmax))
            self.axes_time.plot(self.new_times,self.new_asymmetry,marker=graph_styles[1],mfc=graph_styles[0],mec=graph_styles[0],linestyle='None')
            # FIXME Need to figure out how to assign colors

            if(slider_state == "SLIDER_RELEASED"):
                self.Update_Fourier_Transform(float(bin_size), float(xmin), float(xmax))
                self.axes_freq.plot(self.x_smooth, self.y_smooth**3,marker=graph_styles[1],mfc=graph_styles[0],mec=graph_styles[0]) # Option to increase contrast?
                self.axes_freq.set_xlim(0,2.5)
                self.axes_freq.set_yticklabels([])
                self.axes_freq.set_xlabel("Frequence (MHz)")
                self.axes_freq.set_ylabel("Magnitude")

        self.axes_time.set_xlabel("Time ("+chr(956)+"s)")
        self.axes_time.set_ylabel("Asymmetry")

    def Update_Asymmetry_Bins(self, xmin, xmax, bin_size, slider_state, parent, graph_index):
        # FUNCTION OVERVIEW
        # This function takes the un-altered asymmetry for the stored runs and calculates the new asymmetry based on the user specified
        # bin size for the times.
        # FIXME We should be calling "Getter" functions to get data members from other classes, not accessing the class data members
        # themselves (good practice), I'll start doing that then come back and fix it everywhere else.
        
        # Retrieve the asymmetry and times from the RunData objects stored in RunInfoPanel object
        asymmetry = np.array([])
        asymmetry = parent.runInfo.data_array[graph_index].asymmetry
        times = np.array([])
        times = parent.runInfo.data_array[graph_index].times #FIXME TIMES ARE STILL IN NANO, MUST FIX!!!
        
        # Determine the start and end indexes based on xmin and xmax and num of indexes
        start_size = int(parent.runInfo.data_array[graph_index].Get_Single_Header_Data('numBins'))
        start_index = int(np.floor((float(xmin)/times[start_size-1])*start_size))
        end_index = int(np.floor((float(xmax)/times[start_size-1])*start_size))

        # Determine the initialial bin size and the new user specified bins size
        time_sep = parent.runInfo.data_array[graph_index].Get_Single_Header_Data('binsize')
        bin_size = float(bin_size)/1000

        # Based on the difference in time and binsize determine the size of the final asymmetry and time array
        final_size = int(np.ceil((times[end_index] - times[start_index]) / bin_size))
        self.new_asymmetry = np.zeros(final_size)
        self.new_times = np.zeros(final_size)
        
        # Initialize asym_sum and time_sum and n (the number of iterations between resetting the sum) and i (the
        # number of elements we have added to the new array)
        asym_sum, time_sum, n, i = 0,0,0,0
        for index in range(start_index,end_index,8):
            # We do eight at a time instead of iterating one at a time as this is much less computationaly intensive (the
            # conditions are checked every eighth time instead of every time, this is called "Loop Unrolling")
            asym_sum += asymmetry[index]
            asym_sum += asymmetry[index+1]
            asym_sum += asymmetry[index+2]
            asym_sum += asymmetry[index+3]
            asym_sum += asymmetry[index+4]
            asym_sum += asymmetry[index+5]
            asym_sum += asymmetry[index+6]
            asym_sum += asymmetry[index+7]
            n += 8
            time_sum += 8*time_sep
            if(time_sum > bin_size):
                self.new_asymmetry[i] = asym_sum / n
                self.new_times[i] = times[index+7]
                asym_sum, time_sum, n = 0,0,0
                i += 1
        self.new_times
        # np.set_printoptions(threshold=sys.maxsize) # DEBUGGING HELP
        # print(self.new_asymmetry, self.new_times) # DEBUGGING HELP

    def Update_Fourier_Transform(self, bin_size, xmin, xmax):
        # FUNCTION OVERVIEW
        # This function takes the newly calculated asymmetry and time arrays and calculates the fast fourier transform of that data, and 
        # then plots it on the lower axes. 
        # Calculate the new fft
        period_s = bin_size / 1000
        frequency_s = 1.0 / period_s
        n = len(self.new_asymmetry)
        k = np.arange(n)
        period = n / frequency_s
        frequencies = k / period
        frequencies = frequencies[range(int(n/2))]
        yValues = np.fft.fft([self.new_asymmetry,self.new_times]) / n
        yValues = abs(yValues[0, range(int(n/2))])
        yValues[0] = 0 # A bit hard coded but for some reason we get high frequencies at zero.
        yValues[1] = 0
        # FIXME Try to pad the frequency array, more values inbetween frequencies set at 0. Make the graph look a little better. Cubing works too..

        # length = len(self.new_asymmetry)
        # x = self.new_times
        # FFT = sy.fft(self.new_asymmetry)
        # FFT[0] = 0
        # FFT[1] = 0
        # freqs = syfp.fftfreq(self.new_asymmetry.size, d=(x[1]-x[0]))
        # self.axes_freq.plot(abs(freqs), abs(FFT))
        # print(freqs, '\n', abs(FFT))

        # Calculate the spline for the graph
        self.x_smooth = np.linspace(frequencies.min(), frequencies.max(), 300)
        np.insert(self.x_smooth,0,0)
        self.y_smooth = spline(frequencies, yValues, self.x_smooth)
        np.insert(self.y_smooth,0,0)

        # Plot! 
        # self.axes_freq.plot(self.x_smooth, self.y_smooth**3) # Option to increase contrast?
        # self.axes_freq.set_xlim(0,2.5)
        # self.axes_freq.set_yticklabels([])
        # self.axes_freq.set_xlabel("Frequence (MHz)")
        # self.axes_freq.set_ylabel("Magnitude")

    def Plot_Single_Run(self, graph_index, graph_variables, parent):
        # FUNCTION OVERVIEW
        # If the user presses the "Isolate" button, wishing to plot that run alone, this function will clear the axes and plot that run,
        # ignoring any other runs that are currently plotted or selected in the FileManagerPanel
        self.axes_time.clear()
        self.axes_freq.clear()
        graph_styles = parent.runInfo.data_array[graph_index].Get_Graphing_Styles()
        self.Update_Asymmetry_Bins(graph_variables[0], graph_variables[1], graph_variables[2], 
            "SLIDER_RELEASED", parent, graph_index)
        
        self.axes_time.set_xlim(float(graph_variables[0]),float(graph_variables[1]))
        self.axes_time.plot(self.new_times,self.new_asymmetry,marker=graph_styles[1],mfc=graph_styles[0],mec=graph_styles[0])
        self.axes_time.set_xlabel("Time ("+chr(956)+"s)")
        self.axes_time.set_ylabel("Asymmetry")

        self.Update_Fourier_Transform(float(graph_variables[2]), float(graph_variables[0]), float(graph_variables[1]))

        self.axes_freq.plot(self.x_smooth, self.y_smooth**3,marker=graph_styles[1],mfc=graph_styles[0],mec=graph_styles[0]) # Option to increase contrast?
        self.axes_freq.set_xlim(0,2.5)
        self.axes_freq.set_yticklabels([])
        self.axes_freq.set_xlabel("Frequence (MHz)")
        self.axes_freq.set_ylabel("Magnitude")


class GraphEditorPanel(QtWidgets.QDockWidget):
    def __init__(self,parent = None):
        # CLASS OVERVIEW
        # This is the panel that opens on the bottom of the window, it contains LineEdit and Slider objects that allow the user to alter
        # the graphs appearance (the max and min times for each axes as well as how the asymmetry is binned timewise)
        super(GraphEditorPanel,self).__init__()
        self.setParent(parent)
        self.initUI(parent)

    def initUI(self, parent):
        # FUNCTION OVERVIEW
        # Lots of setup in this function but it is simple code. We create all the user input objects and determine how they will be 
        # placed physically on the actual GraphEditorPanel object.
        
        self.setWindowTitle("Graph Editor")

        slider_one_label = QtWidgets.QLabel()
        slider_one_label.setText("Time Bins (ns)")
        slider_two_label = QtWidgets.QLabel()
        slider_two_label.setText("Time Bins (ns)")

        self.slider_one = self.Create_Slider()
        self.slider_two = self.Create_Slider()

        self.slider_one.sliderReleased.connect(lambda: self.Slider_Released(parent, 1))
        self.slider_two.sliderReleased.connect(lambda: self.Slider_Released(parent, 2))
        self.slider_one.sliderMoved.connect(lambda: self.Slider_Moving(parent, 1))
        self.slider_two.sliderMoved.connect(lambda: self.Slider_Moving(parent, 2))

        self.slider_one_text = QtWidgets.QLineEdit()
        self.slider_one_text.setText(str(self.slider_one.value()))
        self.slider_one_text.setFixedWidth(50)
        self.slider_one_text.returnPressed.connect(lambda: self.Slider_Text_Changed(parent, 1))

        self.slider_two_text = QtWidgets.QLineEdit()
        self.slider_two_text.setText(str(self.slider_two.value()))
        self.slider_two_text.setFixedWidth(50)
        self.slider_two_text.returnPressed.connect(lambda: self.Slider_Text_Changed(parent, 2))

        xmin_one_label = self.Create_Input_Box_Label("Plot 1 - XMin ("+chr(956)+"s)")
        xmax_one_label = self.Create_Input_Box_Label("XMax ("+chr(956)+"s)")
        xmin_two_label = self.Create_Input_Box_Label("Plot 2 - XMin ("+chr(956)+"s)")
        xmax_two_label = self.Create_Input_Box_Label("XMax ("+chr(956)+"s)")

        self.xmin_one = self.Create_Input_Boxes("0",1)
        self.xmin_one.returnPressed.connect(lambda: self.Slider_Released(parent, 1))
        self.xmax_one = self.Create_Input_Boxes("5",1)
        self.xmax_one.returnPressed.connect(lambda: self.Slider_Released(parent, 1))
        self.xmin_two = self.Create_Input_Boxes("0",2)
        self.xmin_two.returnPressed.connect(lambda: self.Slider_Released(parent, 2))
        self.xmax_two = self.Create_Input_Boxes("10",2)
        self.xmax_two.returnPressed.connect(lambda: self.Slider_Released(parent, 2))

        self.setWidget(self.Create_Layout(xmin_one_label,xmin_two_label,xmax_one_label,xmax_two_label,slider_one_label,slider_two_label))

    def Create_Slider(self):
        # FUNCTION OVERVIEW
        # Creates one of sliders used to determine the bin size for time. 
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(500)
        slider.setValue(150)
        slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        slider.setTickInterval(20)
        return slider

    def Create_Input_Boxes(self,box_value,graph_num):
        # FUNCTION OVERVIEW
        # Creates one of the input boxes (so we don't have to repeat this code 6 times)
        input_box = QtWidgets.QLineEdit()
        input_box.setText(box_value)
        input_box.setFixedWidth(50)
        return input_box

    def Create_Input_Box_Label(self,box_label):
        # FUNCTION OVERVIEW
        # Creates one of the labels for the input boxes (so we don't have to repeat this code 6 times)
        input_box_label = QtWidgets.QLabel()
        input_box_label.setText(box_label)
        return input_box_label

    def Create_Layout(self, label_x_one, label_x_two, label_x_three, label_x_four, label_s_one, label_s_two):
        # FUNCTION OVERVIEW
        # Takes all the objects we created and organizes them on a widget, which it returns to be set as the central widget.
        tempWidget = QtWidgets.QWidget()
        vbox_one = QtWidgets.QVBoxLayout()
        vbox_one.addWidget(self.xmin_one)
        vbox_one.addWidget(self.xmin_two)
        vbox_two = QtWidgets.QVBoxLayout()
        vbox_two.addWidget(self.xmax_one)
        vbox_two.addWidget(self.xmax_two)
        vbox_three = QtWidgets.QVBoxLayout()
        vbox_three.addWidget(self.slider_one)
        vbox_three.addWidget(self.slider_two)
        vbox_four = QtWidgets.QVBoxLayout()
        vbox_four.addWidget(label_x_one)
        vbox_four.addWidget(label_x_two)
        vbox_five = QtWidgets.QVBoxLayout()
        vbox_five.addWidget(label_x_three)
        vbox_five.addWidget(label_x_four)
        vbox_six = QtWidgets.QVBoxLayout()
        vbox_six.addWidget(label_s_one)
        vbox_six.addWidget(label_s_two)
        vbox_seven = QtWidgets.QVBoxLayout()
        vbox_seven.addWidget(self.slider_one_text)
        vbox_seven.addWidget(self.slider_two_text)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(vbox_four)
        hbox.addLayout(vbox_one)
        hbox.addLayout(vbox_five)
        hbox.addLayout(vbox_two)
        hbox.addLayout(vbox_six)
        hbox.addLayout(vbox_seven)
        hbox.addLayout(vbox_three)
        tempWidget.setLayout(hbox)
        return tempWidget

    def Slider_Released(self, parent, graph_num):
        # FUNCTION OVERVIEW
        # FIXME Combine this with Slider_Moving, just include an if-else branch.

        if(graph_num == 1):
            self.slider_one_text.setText(str(self.slider_one.value()))
            parent.graphArea.canvas_one.Plot_Data(self.xmin_one.text(), self.xmax_one.text(), self.slider_one.value(), 
                "SLIDER_RELEASED", parent)
        else:
            self.slider_two_text.setText(str(self.slider_two.value()))
            parent.graphArea.canvas_two.Plot_Data(self.xmin_two.text(), self.xmax_two.text(), self.slider_two.value(), 
                "SLIDER_RELEASED", parent)
        
    def Slider_Moving(self, parent, graph_num):
        # FUNCTION OVERVIEW
        # FIXME Combine this with Slider_Released, just include an if-else branch.
        # Since it is computationally intensive to rebin the asymmetry we will only
        # do it while it is moving with every fifth tick. Then we will do it once it
        # is released.
        if(graph_num == 1):
            if(self.slider_one.value() % 5 == 0):
                parent.graphArea.canvas_one.Plot_Data(self.xmin_one.text(), self.xmax_one.text(), self.slider_one.value(), 
                    "SLIDER_MOVING", parent)
        else:
            if(self.slider_two.value() % 5 == 0):
                parent.graphArea.canvas_two.Plot_Data(self.xmin_two.text(), self.xmax_two.text(), self.slider_two.value(), 
                "SLIDER_MOVING", parent)

    def Slider_Text_Changed(self, parent, graph_num):
        # FUNCTION OVERVIEW
        # When the input box for the bin size is changed this will call the plot function as well as move the slider to the
        # appropriate position
        if(graph_num == 1):
            self.slider_one.setValue(int(self.slider_one_text.text()))
            parent.graphArea.canvas_one.Plot_Data(self.xmin_one.text(), self.xmax_one.text(), self.slider_one.value(), 
                "SLIDER_RELEASED", parent)
        else:
            self.slider_two.setValue(int(self.slider_two_text.text()))
            parent.graphArea.canvas_two.Plot_Data(self.xmin_two.text(), self.xmax_two.text(), self.slider_two.value(), 
                "SLIDER_RELEASED", parent)

    def Get_Graphing_Variables(self):
        # FUNCTION OVERVIEW
        # Returns all the user-changeable graphing variables stored in this class
        graphing_variables = {
            'xmin_one' : float(self.xmin_one.text()),
            'xmax_one' : float(self.xmax_one.text()),
            'slider_one' : self.slider_one.value(),
            'xmin_two' : float(self.xmin_two.text()),
            'xmax_two' : float(self.xmax_two.text()),
            'slider_two' : self.slider_two.value()
        }
        return graphing_variables


class RunInfoPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        # CLASS OVERVIEW
        # This is the panel that opens on the right side, it will hold a RunBox (see below) for each run that is currently selected and 
        # plotted by the user. The RunBox holds extra information on that run and allows the user to isolate a single run when multiple
        # are plotted or inspect invdividual histograms as well. Holds an array of RunData objects to access this information.
        super(RunInfoPanel,self).__init__()
        self.setParent(parent)
        self.setWindowTitle("Run Information")
        self.layout = QtWidgets.QVBoxLayout()
        self.tempWidget = QtWidgets.QWidget()
        self.tempWidget.setLayout(self.layout)
        self.setWidget(self.tempWidget)
        self.data_array = []
        self.layout.addStretch()
        # self.marker_colors = {
        #     "Blue" : "b",
        #     "Green" : "g",
        #     "Red" : "r",
        #     "Cyan" : "c",
        #     "Magenta" : "m",
        #     "Yellow" : "y",
        #     "Black" : "k",
        # }
        
    def Read_Dat_Files(self,parent):
        # FUNTION OVERVIEW
        # Calls Update_Run_Panel to delete old run boxes (even if some would normally be kept) and then creates a box for all
        # currently selected runs.
        filenames = self.Update_Run_Panel(parent)
        index = 0
        for index in range(len(filenames)):
            self.data_array.append(RunData(filename=filenames[index]))
            run_data_box = self.Create_Run_Box(self.data_array[index].Get_Single_Header_Data("Title"), index, parent)
            self.layout.insertWidget(index, run_data_box)       

        plot_all_button = QtWidgets.QPushButton()
        plot_all_button.setText("Plot All")
        plot_all_button.pressed.connect(lambda: self.Plot_All(parent))

        self.layout.insertWidget(index + 1, plot_all_button) 

    def Update_Run_Panel(self, parent):
        # FUNCTION OVERVIEW
        # Loop through layout of RunInfoPanel and clear all old widgets (old run info) then add the new. Returns filenames for 
        # creating the RunData objects back in the Read_Dat_Files function.
        del self.data_array[:]

        # This loop goes through the old layout and removes old run info boxes
        # FIXME add an if statement so it only does this if there are already runs in the plot. Otherwise 
        # we get an error. Not sure how to get rid of the plot button yet; when in doubt, call it a feature.
        for i in reversed(range(self.layout.count()-1)):
            self.layout.itemAt(i).widget().setParent(None)

        # Get all the currently checked filenames # FIXME Just move this up Read_Dat_Files 
        filenames = parent.fileControl.Get_Checked_Filenames()
        return filenames

    def Create_Run_Box(self, title, data_num, parent):
        # FUNCTION OVERVIEW
        # The RunBoxes for each run contain a lot of Widgets for user input, this function creates them and lays them out appropriately.
        # One box is returned with each function call.
        run_box = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        hbox_one = QtWidgets.QHBoxLayout()
        hbox_two = QtWidgets.QHBoxLayout()
        hbox_three = QtWidgets.QHBoxLayout()

        color_options = QtWidgets.QComboBox()
        color_options.currentIndexChanged.connect(lambda: self.Color_Changed(color_options.currentText(), 
            data_num, parent))
        color_options.setFixedWidth(75)
        color_options.addItem("blue")
        color_options.addItem("orange")
        color_options.addItem("green")
        color_options.addItem("red")
        color_options.addItem("purple")
        color_options.addItem("brown")
        color_options.addItem("pink")
        color_options.addItem("gray")
        color_options.addItem("olive")
        color_options.addItem("cyan")
        color_options.addItem("custom") # Not supported yet.
        color_options.setCurrentText(color_options.itemText(data_num))

        hist_options = QtWidgets.QComboBox()
        hist_options.setFixedWidth(50)
        hist_options.addItem("front")
        hist_options.addItem("back")
        hist_options.addItem("left")
        hist_options.addItem("right")

        hist_label = QtWidgets.QLabel("Histogram  ")

        inspect_button = QtWidgets.QPushButton()
        inspect_button.setText("Inspect")
        inspect_button.pressed.connect(lambda: self.Inspect_Histogram(hist_options.currentText(), data_num, parent))

        isolate_button = QtWidgets.QPushButton()
        isolate_button.setText("Isolate")
        isolate_button.pressed.connect(lambda: self.Isolate_Plot(data_num, parent))

        box_title = QtWidgets.QLabel(title)

        data_options_label = QtWidgets.QLabel("Other Data")

        data_display = QtWidgets.QLineEdit("None Selected")
        data_display.setDisabled(True)

        data_options_box = QtWidgets.QComboBox()
        data_options_box.currentIndexChanged.connect(lambda: self.Run_Data_Query(data_options_box.currentText(), data_display, data_num, parent))
        data_options_box.setFixedWidth(100)
        header_data = self.data_array[data_num].Get_Header_Data()
        for data_title in header_data:
            data_options_box.addItem(data_title)        

        hbox_one.addWidget(color_options)
        hbox_one.addWidget(isolate_button)
        hbox_one.addWidget(box_title)
        hbox_one.addStretch()
        
        hbox_two.addWidget(data_options_label)
        hbox_two.addWidget(data_options_box)
        hbox_two.addWidget(data_display)
    
        hbox_three.addWidget(hist_label)
        hbox_three.addWidget(hist_options)
        hbox_three.addWidget(inspect_button)
        hbox_three.addStretch()

        vbox.addLayout(hbox_one)
        vbox.addLayout(hbox_two)
        vbox.addLayout(hbox_three)

        run_box.setLayout(vbox)

        return run_box

    def Inspect_Histogram(self, histogram, graph_num, parent):
        # FUNCTION OVERVIEW
        # Function call for the "Inspect" button, see Inspect_Histogram in RunData class for more information.
        self.data_array[graph_num].Inspect_Histogram(histogram)

    def Isolate_Plot(self, graph_num, parent):
        # FUNCTION OVERVIEW
        # Function call for the "Isolate" button, gets the graphing variables the GraphEditorPanel and calls the Plot_Single_Run 
        # function from the PlotCanvas class.
        graphing_variables = parent.graphEditor.Get_Graphing_Variables()
        parent.graphArea.canvas_one.Plot_Single_Run(graph_num, [graphing_variables['xmin_one'], graphing_variables['xmax_one'],
            graphing_variables['slider_one']], parent)
        parent.graphArea.canvas_two.Plot_Single_Run(graph_num, [graphing_variables['xmin_two'], graphing_variables['xmax_two'],
            graphing_variables['slider_two']], parent)

    def Color_Changed(self, color, graph_num, parent):
        # FUNCTION OVERVIEW
        # Will allow the user to change the color of any individual run on the plot.
        graphing_variables = parent.graphEditor.Get_Graphing_Variables()
        parent.runInfo.data_array[graph_num].Set_Graphing_Styles(color=color)
        parent.graphArea.canvas_one.Plot_Data(graphing_variables['xmin_one'], graphing_variables['xmax_one'], graphing_variables['slider_one'], 
            "SLIDER_RELEASED", parent) 
        parent.graphArea.canvas_two.Plot_Data(graphing_variables['xmin_two'], graphing_variables['xmax_two'], graphing_variables['slider_two'], 
            "SLIDER_RELEASED", parent)    

    def Run_Data_Query(self, data_member, line_edit, graph_num, parent):
        # FUNCTION OVERVIEW
        # This is linked to the ComboBox where the user can choose other header titles and retrieve the appropriate data for that run.
        line_edit.setText(str(parent.runInfo.data_array[graph_num].Get_Single_Header_Data(data_member)))       

    def Plot_All(self, parent):
        # FUNCTION OVERVIEW
        # Function call for the "Plot All" button, does exactly what it says. Gets the graphing variables then calls the Plot_Data
        # function in the PlotCanvas class to replot all the runs currently shown in the RunInfoPanel.
        graphing_variables = parent.graphEditor.Get_Graphing_Variables()
        parent.graphArea.canvas_one.Plot_Data(graphing_variables['xmin_one'], graphing_variables['xmax_one'],
            graphing_variables['slider_one'], "SLIDER_RELEASED", parent)
        parent.graphArea.canvas_two.Plot_Data(graphing_variables['xmin_two'], graphing_variables['xmax_two'],
            graphing_variables['slider_two'], "SLIDER_RELEASED", parent)


class RunData:
    def __init__(self,parent=None,filename=None):
        # CLASS OVERVIEW
        # Stores the required data for each run. All the data in the header is stored permanently in the object, the histograms are only
        # stored temporarily to create the Asymmetry and Time arrays which are stored permanently.
        self.initData(filename)

    def initData(self,filename):
        # FUNCTION OVERVIEW
        # First read in the header of the .dat file to get basic information about the run and assign to appropriate class members. Then
        # read in the histograms and generate the assymetry and time arrays. Does not permanently store the histograms.
        self.filename = filename

        data_line = pd.read_csv(filename,nrows=1)

        self.header_data = {}
        header_titles = data_line.columns
        for title in header_titles:
            self.header_data[title] = data_line.iloc[0][title]
        
        self.header_data['binsize'] = float(self.header_data['binsize'])/1000 # ns to µs
        self.marker_style = '.'
        self.marker_color = 'blue'

        run_data = pd.read_csv(filename,skiprows=2)

        # FIXME This is only for generating front-back/front+back asymmetry, add functionality
        # for the obvious other situations. (Good enough for testing).
        # FIXME We need to figure out which is front,back,left,right because the dang MUD functions don't tell us.
        # run_data['asymmetry'] = (run_data['left'] - run_data['right'])/(run_data['left'] + run_data['right'])
        # run_data['asymmetry'] = (run_data['back'] - run_data['front'])/(run_data['front'] + run_data['back'])
        # run_data['asymmetry'] = (run_data['front'] - run_data['left'])/(run_data['front'] + run_data['left'])
        run_data['asymmetry'] = (run_data['back'] - run_data['right'])/(run_data['back'] + run_data['right'])

        run_data['asymmetry'].fillna(0.0,inplace=True)
        self.asymmetry = np.array([])
        self.asymmetry = run_data['asymmetry'].values

        # Create a time array that is Num_Bins long with the actual time put in by multiplying
        # the range by the bin size (usually about .4 ns)
        self.times = np.arange(1,self.header_data['numBins']+1,dtype='float64')
        self.times *= self.header_data['binsize']
    
    def Get_Single_Header_Data(self, title):
        # FUNCTION OVERVIEW
        # Returns specific value from the header for the run
        return self.header_data[title]

    def Get_Header_Data(self):
        # FUNCTION OVERVIEW
        # Returns all the header data for the run
        return self.header_data

    def Get_Asymmetry(self):
        # FUNCTION OVERVIEW
        # Returns the asymmetry for the run
        return self.asymmetry

    def Get_Times(self):
        # FUNCTION OVERVIEW
        # Returns the initital times for the run
        return self.times

    def Get_Graphing_Styles(self):
        # FUNCTION OVERVIEW
        # Returns the marking styles for the run
        return [self.marker_color, self.marker_style]

    def Set_Graphing_Styles(self,color='na',style='na'):
        # FUNCTION OVERVIEW
        # Set the marking styles for this run
        if(color != 'na'):
            self.marker_color = color
        if(style != 'na'):
            self.marker_style = style

    def Inspect_Histogram(self, histogram):
        # FUNCTION OVERVIEW FIXME FIXME FIXME FIXME FIXME FIXME (hint, this function is broke, very sensitive -- not pretty)
        # Plots the user-specified histogram for this run and shows it in a pop-up window. Built-in MatPlotLib functionality
        # allows the user to zoom in on specified sections as well so we don't need to add that ourselves. This function takes
        # advantage of loop unrolling to create a smaller histogram (the plot had trouble plotting the whole histogram). We'll
        # have to figure out how to dynamically allow the user to see the whole histogram. # FIXME
        run_data = pd.read_csv(self.filename,skiprows=2)
        histogram_data = run_data[histogram].values      
        
        new_bins = int(np.floor(len(histogram_data)/20))
        new_hist = np.zeros(new_bins)
        new_times = np.arange(new_bins)

        i = 0
        sum = 0
        n = 0
        for i in range(0,new_bins*20,20):
            sum += histogram_data[i]
            sum += histogram_data[i+1]
            sum += histogram_data[i+2]
            sum += histogram_data[i+3]
            sum += histogram_data[i+4]
            sum += histogram_data[i+5]
            sum += histogram_data[i+6]
            sum += histogram_data[i+7]
            sum += histogram_data[i+8]
            sum += histogram_data[i+9]
            sum += histogram_data[i+10]
            sum += histogram_data[i+11]
            sum += histogram_data[i+12]
            sum += histogram_data[i+13]
            sum += histogram_data[i+14]
            sum += histogram_data[i+15]
            sum += histogram_data[i+16]
            sum += histogram_data[i+17]
            sum += histogram_data[i+18]
            sum += histogram_data[i+19]
            new_hist[n] = sum / 20
            n += 1
            sum = 0

        fig = plt.figure()
        plt.bar(new_times,new_hist)
        # FIXME Figure out dynamic way to set y limits
