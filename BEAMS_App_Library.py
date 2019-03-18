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

# Ctypes to deal with our delightful MUD functions from TRIUMF
# from ctypes import *

# Custom MUD function for reading in files
# import cython
# import BEAMS_C_Library


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window,self).__init__()
        self.initUI()

    def initUI(self):
        # print("initUI Function :: Window Class") # DEBUGGING HELP
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
        # print("Create_MenuBar Function :: Window Class")
        # Initializes the menubar across the top of the main window, still need to
        # add functionality to these items.

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
        addDataAct.triggered.connect(lambda: self.AddDataFile())

        #Menubar layout setup
        # self.statusBar()
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
        # print("Create_FileManager Function :: Window Class") # DEBUGGING HELP
        self.fileControl = FileManagerPanel(parent=self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.fileControl)

    def Create_GraphEditor(self):
        # print("Create_GraphEditor Function :: Window Class") # DEBUGGING HELP
        self.graphEditor = GraphEditorPanel(parent=self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.graphEditor)

    def Create_GraphArea(self):
        # print("Create_GraphArea Function :: Window Class") # DEBUGGING HELP
        self.graphArea = GraphAreaPanel(parent=self)
        self.setCentralWidget(self.graphArea)

    def Create_RunInfoPanel(self):
        # print("Create_RunInfoPanel Function :: Window Class") # DEBUGGING HELP
        self.runInfo = RunInfoPanel(parent=self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.runInfo)


class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        # print("init Function :: FileManagerPanel Class") # DEBUGGING HELP
        super(FileManagerPanel,self).__init__()
        # Set the Main Window as the parent class
        self.setParent(parent)
        # Create the array where the filenames will be stored
        self.filenames = []
        # Initialize UI for the file manager panel
        self.initUI(parent)

    def initUI(self,parent):
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
        print("Write_Button Function :: FileManagerPanel Class") # DEBUGGING HELP

    def Add_Button(self):
        # ADD_BUTTON Functionality : Prompt user for a file to import and add that file to
        # the self.filenames array for the FileManagerPanel Object
        # print("Add_Button Function :: FileManagerPanel Class") # DEBUGGING HELP 

        # Use getOpenFileNames to get multiple files at once. FIXME 
        # Open File-Dialog for user to select a file to import
        filename = QtWidgets.QFileDialog.getOpenFileName(self,'Add file','/home')

        # Using the OS Library break the file into the file_path, file_base, and file_ext
        # i.e. "C:/Users/kalec/Documents/" and "006515" and ".msr" respectively
        file_path, file_root = os.path.split(filename[0])
        file_base, file_ext = os.path.splitext(os.path.basename(file_root))
        # print(file_path," + ",file_base," + ",file_ext) # DEBUGGING HELP

        # If it is a MUD file it must be imported to a .dat file and then add file to object array
        if(file_ext == ".msr"):
            self.Import_MUD_File(filename[0])
        self.filenames.append(file_path+"/"+file_base+".dat")
        # print(self.filenames) # DEBUGGING HELP

        # Display the file_base in the file manager on the left side, with a check
        file_item = QtWidgets.QListWidgetItem(file_base,self.listWidget)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)

        # self.Import_MUD_File(filename[0]) # FIXME Eventually we will want to import the .msr
        # to .dat files. Once we get this silly c code to run from python.

    def Import_MUD_File(self, filename):
        print("Import_MUD_File Function :: FileManagerPanel Class") # DEBUGGING HELP
        # FIXME This function will take the date from .msr and create a .dat with the same name
        # then it will call Read_DatFile to read in the .dat file it just created. Some day.
        # mud_lib = ctypes.CDLL(BEAMS_MUDlib.so)
        # libMUD = CDLL(r"C:\Users\kalec\Documents\Research_Frandsen\Visualizing_uSR\BEAMS\mud\src\BEAMS_MUDlib.dll")

    def Plot_Button(self,parent):
        # print("Plot_Button Function :: FileManagerPanel Class") # DEBUGGING HELP
        # PLOT_BUTTON Functionality : This button will call the Read_Dat_Files on the RunInfoPanel
        # object to get the basic run info and initial asymmetry and time arrays.

        # Read in .dat files
        parent.runInfo.Read_Dat_Files(parent)
    
        # Update canvas one (the two axes on the left of the graphing area)
        parent.graphArea.canvas_one.Plot_Data(parent.graphEditor.xmin_one.text(), parent.graphEditor.xmax_one.text(),
            parent.graphEditor.slider_one.value(),1,"SLIDER_RELEASED", parent)
        
        # Update canvas two (the two axes on the right of the graphing area)
        parent.graphArea.canvas_one.Plot_Data(parent.graphEditor.xmin_two.text(), parent.graphEditor.xmax_two.text(),
            parent.graphEditor.slider_two.value(),2,"SLIDER_RELEASED", parent)



    def Get_Filenames(self):
        # GET_FILENAMES Functionality : ... do I really have to explain?
        return self.filenames

    def Get_Checked_Filenames(self):
        # GET_CHECKED_FILENAMES Functionality : run through the file list on the GUI and 
        # check which filenames are checked by the user. Those are the ones that will be
        # returned. 
        # print("Get_Filenames Function :: FileManagerPanel Class") # DEBUGGING HELP
        checked_items = []
        for index in range(self.listWidget.count()):
            # print("Checking item at ", index) # DEBUGGING HELP
            if self.listWidget.item(index).checkState() == QtCore.Qt.Checked:
                checked_items.append(self.filenames[index])
                # print(self.listWidget.item(index).text()) # DEBUGGING HELP
        return checked_items
        

class GraphAreaPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        # print("init Function :: GraphAreaPanel Class") # DEBUGGING HELP
        super(GraphAreaPanel,self).__init__()
        self.setParent(parent)
        self.initUI()
        plt.ion()

    def initUI(self):
        self.setWindowTitle("Graphing Area")
        tempWidget = QtWidgets.QWidget()

        self.canvas_one = self.Create_Canvas()
        self.canvas_two = self.Create_Canvas()

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.canvas_one)
        hbox.addWidget(self.canvas_two)
        tempWidget.setLayout(hbox)

        self.setWidget(tempWidget)

    def Create_Canvas(self):
        # print("Create_Canvas Function :: GraphAreaPanel Class") # DEBUGGING HELP
        canvas = PlotCanvas(parent=self)
        return canvas


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # print("init Function :: PlotCanvas Class") # DEBUGGING HELP
        fig = plt.figure(dpi=dpi)
        
        self.axes_time = fig.add_subplot(211,label="Time Domain")
        self.axes_freq = fig.add_subplot(212,label="Frequency Domain")
        FigureCanvas.__init__(self,fig)
        self.muSRData = np.array([])

        self.setParent(parent)

        self.axes_time.clear()
        self.axes_freq.clear()

    def Import_Data(self,parent):
        # print("Import_Data Function :: PlotCanvas Class") # DEBUGGING HELP
        checked_items = parent.fileControl.Get_Filenames()
        print(checked_items)
        for index in range(len(checked_items)):
            print(index)

    def Plot_Data(self, xmin, xmax, bin_size, graph_num, slider_state, parent):
        # print("Plot_Data Function :: PlotCanvas Class") # DEBUGGING HELP
        print(xmin, xmax, bin_size, graph_num, slider_state)
        self.axes_freq.clear()
        self.axes_time.clear()
        self.Update_Asymmetry_Bins(xmin, xmax, bin_size, graph_num, slider_state, parent)

    def Update_Asymmetry_Bins(self, xmin, xmax, bin_size, graph_num, slider_state, parent):
        # Retrieve the asymmetry and times from the RunData objects stored in RunInfoPanel object
        asymmetry = np.array([])
        asymmetry = parent.runInfo.data_array[0].asymmetry
        times = np.array([])
        times = parent.runInfo.data_array[0].times #FIXME TIMES ARE STILL IN NANO, MUST FIX!!!
        
        # Determine the start and end indexes based on xmin and xmax and num of indexes
        start_size = int(parent.runInfo.data_array[0].run_num_bins)
        start_index = int(np.floor((float(xmin)*1000/times[start_size-1])*start_size))
        end_index = int(np.floor((float(xmax)*1000/times[start_size-1])*start_size))

        # Split the array according to our start and end indexes found above FIXME Possibly not necessary
        # times = np.split(times,[start_index,end_index])[1]
        # asymmetry = np.split(asymmetry,[start_index,end_index])[1]

        time_sep = parent.runInfo.data_array[0].run_bin_size
        bin_size = float(bin_size)

        final_size = int(np.ceil((times[end_index] - times[start_index]) / bin_size))
        print(final_size)
        new_asymmetry = np.zeros(final_size)
        new_times = np.zeros(final_size)
        
        asym_sum, time_sum, n, i = 0,0,0,0
        for index in range(start_index,end_index,8):
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
            # print(asym_sum,time_sum,n,i,bin_size,index) # DEBUGGING HELP
            if(time_sum > bin_size):
                new_asymmetry[i] = asym_sum / n
                new_times[i] = times[index+7]
                asym_sum, time_sum, n = 0,0,0
                i += 1
        new_times /= 1000
        np.set_printoptions(threshold=sys.maxsize) # DEBUGGING HELP
        print(new_asymmetry, new_times) # DEBUGGING HELP

        self.axes_time.set_xlim(float(xmin),float(xmax))
        self.axes_time.set_ylim(-.2,.2)
        self.axes_time.plot(new_times,new_asymmetry,'ro')


class GraphEditorPanel(QtWidgets.QDockWidget):
    def __init__(self,parent = None):
        super(GraphEditorPanel,self).__init__()
        self.setParent(parent)
        self.initUI(parent)

    def initUI(self, parent):
        # print("init Function :: GraphEditorPanel Class") # DEBUGGING HELP
        
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
        self.xmax_one = self.Create_Input_Boxes("5",1)
        self.xmin_two = self.Create_Input_Boxes("0",2)
        self.xmax_two = self.Create_Input_Boxes("10",2)

        self.setWidget(self.Create_Layout(xmin_one_label,xmin_two_label,xmax_one_label,xmax_two_label,slider_one_label,slider_two_label))

    def Create_Slider(self):
        # print("Create_Slider Function :: GraphEditorPanel Class") # DEBUGGING HELP
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(500)
        slider.setValue(150)
        slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        slider.setTickInterval(20)
        return slider

    def Create_Input_Boxes(self,box_value,graph_num):
        # print("Create_Input_Boxes Function :: GraphEditorPanel Class") # DEBUGGING HELP
        input_box = QtWidgets.QLineEdit()
        input_box.setText(box_value)
        input_box.setFixedWidth(50)
        input_box.returnPressed.connect(lambda: self.parent.Plot_Data(graph_num))
        return input_box

    def Create_Input_Box_Label(self,box_label):
        # print("Create_Input_Box_Label Function :: GraphEditorPanel Class") # DEBUGGING HELP
        input_box_label = QtWidgets.QLabel()
        input_box_label.setText(box_label)
        return input_box_label

    def Create_Layout(self, label_x_one, label_x_two, label_x_three, label_x_four, label_s_one, label_s_two):
        # print("Create_Layout Function :: GraphEditorPanel Class") # DEBUGGING HELP
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
        print("Slider_Changed Function :: GraphEditorPanel Class")

        if(graph_num == 1):
            self.slider_one_text.setText(str(self.slider_one.value()))
            parent.graphArea.canvas_one.Plot_Data(self.xmin_one.text(), self.xmax_one.text(), self.slider_one.value(), 
                graph_num, "SLIDER_RELEASED", parent)
        else:
            self.slider_two_text.setText(str(self.slider_two.value()))
            parent.graphArea.canvas_two.Plot_Data(self.xmin_two.text(), self.xmax_two.text(), self.slider_two.value(), 
                graph_num, "SLIDER_RELEASED", parent)
        
    def Slider_Moving(self, parent, graph_num):
        print("Slider_Moving Function :: GraphEditorPanel Class")
        # Since it is computationally intensive to rebin the asymmetry we will only
        # do it while it is moving with every fifth tick. Then we will do it once it
        # is released.
        if(graph_num == 1):
            if(self.slider_one.value() % 5 == 0):
                parent.graphArea.canvas_one.Plot_Data(self.xmin_one.text(), self.xmax_one.text(), self.slider_one.value(), 
                    graph_num, "SLIDER_MOVING", parent)
        else:
            if(self.slider_two.value() % 5 == 0):
                parent.graphArea.canvas_two.Plot_Data(self.xmin_two.text(), self.xmax_two.text(), self.slider_two.value(), 
                graph_num, "SLIDER_MOVING", parent)

    def Slider_Text_Changed(self, parent, graph_num):
        print("Slider_Text_Changed Function :: GraphEditorPanel Class")
        
        if(graph_num == 1):
            self.slider_one.setValue(int(self.slider_one_text.text()))
            parent.graphArea.canvas_one.Plot_Data(self.xmin_one.text(), self.xmax_one.text(), self.slider_one.value(), 
                graph_num, "SLIDER_RELEASED", parent)
        else:
            self.slider_two.setValue(int(self.slider_two_text.text()))
            parent.graphArea.canvas_two.Plot_Data(self.xmin_two.text(), self.xmax_two.text(), self.slider_two.value(), 
                graph_num, "SLIDER_RELEASED", parent)


class RunInfoPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        # print("init Function :: RunInfoPanel Class") # DEBUGGING HELP
        super(RunInfoPanel,self).__init__()
        self.setParent(parent)
        self.setWindowTitle("Run Information")
        self.layout = QtWidgets.QVBoxLayout()
        self.tempWidget = QtWidgets.QWidget()
        self.tempWidget.setLayout(self.layout)
        self.setWidget(self.tempWidget)
        self.data_array = []
        
    def Read_Dat_Files(self,parent):
        # READ_DAT_FILE Functionality: Update the information on the panel and then read
        # in the histograms and create the initial asymmetry and time arrays

        # Call the Update_Run_Panel function to clear and update the panel on the right.
        filenames = self.Update_Run_Panel(parent)

        for index in range(len(filenames)):
            print("reading in file ", index)
            self.data_array.append(RunData(filename=filenames[index]))

    def Update_Run_Panel(self,parent):
        # UPDATE_RUN_PANEL Functionality : Loop through layout of RunInfoPanel and clear
        # all old widgets (old run info) then add the new. Returns filenames for creating the
        # RunData objects back in the Read_Dat_Files function.
        # print("Update_Run_Panel Function :: RunInfoPanel Class") # DEBUGGING HELP

        # Delete old data_array that held the old run info
        del self.data_array[:]

        # This loop goes through the old layout and removes old run info boxes
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        # Get all the currently checked filenames
        filenames = parent.fileControl.Get_Checked_Filenames()
        
        # Add all currently checked filenames and the relevant data to the run info panel.
        for index in range(len(filenames)):
            box_name = QtWidgets.QLabel(filenames[index])
            self.layout.addWidget(box_name)

        return filenames

        
class RunData:
    def __init__(self,parent=None,filename=None):
        # print("init Function :: RunData Class ::", filename) # DEBUGGING HELP
        # Create the datamembers
        self.initData(filename)

    def initData(self,filename):
        # INITDATA Functionality : First read in the header of the .dat file to get 
        # basic information about the run and assign to appropriate class members. Then
        # read in the histograms and generate the assymetry and time arrays. Does not 
        # permanently store the histograms.

        data_line = pd.read_csv(filename,nrows=1)

        self.run_expt_number = data_line.iloc[0]['ExptNumber']
        self.run_number = data_line.iloc[0]['RunNumber']
        self.run_elapsed_secs = data_line.iloc[0]['ElapsedSecs']
        self.run_time_begin = data_line.iloc[0]['TimeBegin']
        self.run_time_end = data_line.iloc[0]['TimeEnd']
        self.run_title = data_line.iloc[0]['Title']
        self.run_lab = data_line.iloc[0]['Lab']
        self.run_area = data_line.iloc[0]['Area']
        self.run_method = data_line.iloc[0]['Method']
        self.run_apparatus = data_line.iloc[0]['Apparatus']
        self.run_insert = data_line.iloc[0]['Insert']
        self.run_sample = data_line.iloc[0]['Sample']
        self.run_orientation = data_line.iloc[0]['Orient']
        self.run_das = data_line.iloc[0]['Das']
        self.run_experimenters = data_line.iloc[0]['Experimenters']
        self.run_temperature = data_line.iloc[0]['Temperature']
        self.run_field = data_line.iloc[0]['Field']
        self.run_num_hists = data_line.iloc[0]['NumHists']
        self.run_bin_size = data_line.iloc[0]['binsize']
        self.run_num_bins = data_line.iloc[0]['numBins']

        run_data = pd.read_csv(filename,skiprows=2)

        # FIXME This is only for generating front-back/front+back asymmetry, add functionality
        # for the obvious other situations. (Good enough for testing)
        run_data['asymmetry'] = (run_data['left'] - run_data['right'])/(run_data['left'] + run_data['right'])
        run_data['asymmetry'].fillna(0.0,inplace=True)
        self.asymmetry = np.array([])
        self.asymmetry = run_data['asymmetry'].values

        # Create a time array that is Num_Bins long with the actual time put in by multiplying
        # the range by the bin size (usually about .4 ns)
        self.times = np.arange(1,self.run_num_bins+1,dtype='float64')
        self.times *= self.run_bin_size



