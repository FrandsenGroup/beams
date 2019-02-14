
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import numpy as np
import time

class Example(QMainWindow):
    
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.initUI()
        
        
    def initUI(self):  
        self.setGeometry(200, 100, 1500, 900)
        self.setWindowTitle('muSR Visualization')

        #FILE NAVIGATOR SETUP
        self.filecontrol = QDockWidget("File Manager",self)

        tempWidget = QWidget()
        
        writeButton = QPushButton()
        writeButton.setText("Write")
        writeButton.released.connect(lambda: self.WriteCurrentData())
        addButton = QPushButton()
        addButton.setText("+")
        addButton.released.connect(lambda: self.AddDataFile())
        plotButton = QPushButton()
        plotButton.setText("Plot")
        plotButton.released.connect(lambda: self.plotButton())

        hbox1 = QHBoxLayout()
        hbox1.addWidget(writeButton)
        hbox1.addWidget(plotButton)
        hbox1.addWidget(addButton)
        
        self.listWidget = QListWidget()
        
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.listWidget)
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        tempWidget.setLayout(vbox)

        self.filecontrol.setWidget(tempWidget)
        self.filecontrol.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.filecontrol) 

        #BOTTOM OPTIONS WINDOW FOR PLOTTING
        self.optionswindow = QDockWidget("Plot Options", self)

        #Slider to control the left and right plots time bins
        slider1label = QLabel()
        slider1label.setText("Time Bins (ns)")
        slider2label = QLabel()
        slider2label.setText("Time Bins (ns)")
        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.setMinimum(1)
        self.slider1.setMaximum(500)
        self.slider1.setValue(150)
        self.slider1.setTickPosition(QSlider.TicksBothSides)
        self.slider1.setTickInterval(20)
        self.slider1.sliderReleased.connect(lambda: self.SliderChanged(self.slider1text, self.slider1.value(),1))
        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setMinimum(1)
        self.slider2.setMaximum(500)
        self.slider2.setValue(150)
        self.slider2.setTickPosition(QSlider.TicksBothSides)
        self.slider2.setTickInterval(20)
        self.slider2.sliderReleased.connect(lambda: self.SliderChanged(self.slider2text, self.slider2.value(),2))

        #Input boxes for time bins, change when slider is changed.
        self.slider1text = QLineEdit()
        self.slider1text.setText(str(self.slider1.value()))
        self.slider1text.setFixedWidth(50)
        self.slider1text.returnPressed.connect(lambda: self.SliderTextChanged(self.slider1,self.slider1text.text(),1))
        self.slider2text = QLineEdit()
        self.slider2text.setText(str(self.slider2.value()))
        self.slider2text.setFixedWidth(50)
        self.slider2text.returnPressed.connect(lambda: self.SliderTextChanged(self.slider2,self.slider2text.text(),2))

        #Input boxes for xmin and xmax for the left and right plots
        xmin1label = QLabel()
        xmin1label.setText("Plot 1 - XMin ("+chr(956)+"s)")
        self.xmin1 = QLineEdit()
        self.xmin1.setText("0")
        self.xmin1.setFixedWidth(50)
        self.xmin1.returnPressed.connect(lambda: self.PlotData(self.dataImport,1))
        xmax1label = QLabel()
        xmax1label.setText("XMax ("+chr(956)+"s)")
        self.xmax1 = QLineEdit()
        self.xmax1.setText("5")
        self.xmax1.setFixedWidth(50)
        self.xmax1.returnPressed.connect(lambda: self.PlotData(self.dataImport,1))
        xmin2label = QLabel()
        xmin2label.setText("Plot 2 - XMin ("+chr(956)+"s)")
        self.xmin2 = QLineEdit()
        self.xmin2.setText("0")
        self.xmin2.setFixedWidth(50)
        self.xmin2.returnPressed.connect(lambda: self.PlotData(self.dataImport,2))
        xmax2label = QLabel()
        xmax2label.setText("XMax ("+chr(956)+"s)")
        self.xmax2 = QLineEdit()
        self.xmax2.setText("10")
        self.xmax2.setFixedWidth(50)
        self.xmax2.returnPressed.connect(lambda: self.PlotData(self.dataImport,2))
    
        #Format layout for the bottom window options.
        tempwindow = QWidget()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.xmin1)
        vbox1.addWidget(self.xmin2)
        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.xmax1)
        vbox2.addWidget(self.xmax2)
        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.slider1)
        vbox3.addWidget(self.slider2)
        vbox4 = QVBoxLayout()
        vbox4.addWidget(xmin1label)
        vbox4.addWidget(xmin2label)
        vbox5 = QVBoxLayout()
        vbox5.addWidget(xmax1label)
        vbox5.addWidget(xmax2label)
        vbox6 = QVBoxLayout()
        vbox6.addWidget(slider1label)
        vbox6.addWidget(slider2label)
        vbox7 = QVBoxLayout()
        vbox7.addWidget(self.slider1text)
        vbox7.addWidget(self.slider2text)
        hbox = QHBoxLayout()
        hbox.addLayout(vbox4)
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox5)
        hbox.addLayout(vbox2)
        hbox.addLayout(vbox6)
        hbox.addLayout(vbox7)
        hbox.addLayout(vbox3)
        tempwindow.setLayout(hbox)

        #Set Widget to bottom docking position
        self.optionswindow.setWidget(tempwindow)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.optionswindow) 

        #INITIAL CENTRAL WINDOW SETUP
        self.dataImport = "Load"
        self.selfilename = None
        self.PlotData(self.dataImport,3)
        self.setCentralWidget(self.newwindow)

        #MENUBAR ITEMS
        #Exit Menu Item
        exitAct = QAction(QIcon('exit.png'), '&Exit', self)        
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        #New Session Menu Item
        newSesAct = QAction(QIcon('newsession.png'), '&New Session', self) 
        newSesAct.setShortcut('Ctrl+N')
        newSesAct.setStatusTip('Create a new session')  
        #Load Session Menu Item
        openSesAct = QAction(QIcon('opensession.png'), '&Open Session', self) 
        openSesAct.setShortcut('Ctrl+O')
        openSesAct.setStatusTip('Open old session')
        #Save Session Menu Item
        saveSesAct = QAction(QIcon('savesession.png'), '&Save Session', self) 
        saveSesAct.setShortcut('Ctrl+S')
        saveSesAct.setStatusTip('Save current session')

        #Add Data Files
        addDataAct = QAction(QIcon('addDada.png'), '&Add Data File', self) 
        addDataAct.setStatusTip('Add a data file to current session')
        addDataAct.triggered.connect(lambda: self.AddDataFile())

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

        self.show()

    #Function for writing data to an outfile
    def WriteCurrentData(self):
        np.savetxt('test.txt',[self.canvas1.timeArray,self.canvas1.dataArray,self.canvas1.errArray])

    #Function for plotting data when the slide changes
    def SliderChanged(self,sliderText,value,graph):
        sliderText.setText(str(value))
        self.PlotData(self.dataImport, graph)
    
    #Function for plotting data when slider text is changed
    def SliderTextChanged(self,slider,valueStr,graph):
        slider.setValue(float(valueStr))
        self.PlotData(self.dataImport, graph)

    #Function for the plot button
    def plotButton(self):
        self.PlotData(self.dataImport,1)
        self.PlotData(self.dataImport,2)

    #Function for adding a data file
    def AddDataFile(self):
        filename = QFileDialog.getOpenFileName(self,'Add file','/home')
        itemN = QListWidgetItem(filename[0],self.listWidget)
        itemN.setFlags(itemN.flags() | Qt.ItemIsUserCheckable)
        itemN.setCheckState(Qt.Unchecked)


    #RECREATE THE PLOTS
    def PlotData(self,dataImport,graph):
        self.newwindow = QWidget()
        self.selfilename = ""
        self.checked_items = []
        for index in range(self.listWidget.count()):
            print("Checking item at ", index) 
            if self.listWidget.item(index).checkState() == Qt.Checked:
                self.checked_items.append(self.listWidget.item(index).text())
                print(self.listWidget.item(index).text())

        print("Plotting data...")
        if dataImport == "Load":
            print("After Load")
            t0 = time.time()
            self.canvas1 = Canvas(self, bins=self.slider1.value(), xmin=float(self.xmin1.text()), xmax=float(self.xmax1.text()), filename=self.checked_items, graphtype="t1", data=dataImport)
            self.canvas2 = Canvas(self, bins=self.slider2.value(), xmin=float(self.xmin2.text()), xmax=float(self.xmax2.text()), filename=self.checked_items, graphtype="t2", data=dataImport)
            self.dataImport = "Current"
        else:
            t0 = time.time()
            print("After Else,",  self.checked_items)
            if graph == 1:
                print("Updating Plot 1")
                self.canvas1.axes1.clear()
                self.canvas1.axes2.clear()
                for index in range(len(self.checked_items)):
                    self.canvas1.plotNewData(self.slider1.value(), xmin=float(self.xmin1.text()), xmax=float(self.xmax1.text()),fileList=self.checked_items)
            elif graph == 2:
                print("Updating Plot 2")
                self.canvas2.axes1.clear()
                self.canvas2.axes2.clear()
                for index in range(len(self.checked_items)):
                    self.canvas2.plotNewData(self.slider2.value(), xmin=float(self.xmin2.text()), xmax=float(self.xmax2.text()),fileList=self.checked_items)
            print("Processing time to update Canvases: ", time.time() - t0,"\n")

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.canvas1)
        hbox1.addWidget(self.canvas2)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        self.newwindow.setLayout(vbox)

        self.setCentralWidget(self.newwindow)
        
       

class Canvas(FigureCanvas):
    def __init__(self, parent = None, xmin=0, xmax=10, bins = 10, filename = [], dpi = 100, graphtype = "n", data = "Load"):
    #CREATE FIGURE CANVAS TO PUT GRAPH ON
        fig = plt.figure(dpi=dpi)
        self.axes1 = fig.add_subplot(211,label="Time Domain")
        self.axes2 = fig.add_subplot(212,label="Frequency Domain")
        FigureCanvas.__init__(self, fig)
            
        self.setParent(parent)
        self.axes1.clear()
        self.axes2.clear()

            
    def plotNewData(self, bins, xmin, xmax, fileList):
        self.result = []
        print(fileList)
        for index in range(len(fileList)):
            t1, a1, yerr = np.loadtxt(fileList[index], dtype=float,comments="%",delimiter=",",unpack=True, usecols=(0,1,2))
            self.result = (list(zip(t1,a1,yerr)))
            self.plotAsymmetry(bins,xmin,xmax)
            self.plotFourier(bins,xmin,xmax)
            

    def plotAsymmetry(self, time_bins, xmin, xmax):
        # Plot the Asymmetry vs Time
        self.binChange(time_bins*.001,xmin,xmax)
        self.axes1.set_xlim(xmin,xmax)
        self.axes1.errorbar(self.timeArray, self.dataArray, self.errArray, marker='o',linestyle='none')
        self.axes1.set_xlabel("Time ("+chr(956)+"s)")
        self.axes1.set_ylabel("Asymmetry")
        

    def plotFourier(self, time_bins, xmin, xmax):
        # Calculate the fast fourier transform of the above data
        Ts = time_bins*.001
        Fs = 1.0/Ts
        n = len(self.dataArray)
        k = np.arange(n)
        T = n/Fs
        frq = k/T
        frq = frq[range(int(n/2))]
        Y = np.fft.fft([self.dataArray,self.timeArray])/n
        Y = Y[0,range(int(n/2))]

        # Plot the fourier transform
        self.axes2.plot(frq,abs(Y),'r')
        self.axes2.set_ylabel("Amplitude")
        self.axes2.set_xlabel("Frequency (MHz)")
        self.axes2.set_xlim(0,None)


    def binChange(self, time_bin, xmin, xmax):
        # Use new time bin to re-bin the data
        count = 1
        binSum,errSum = 0,0
        timeMax = time_bin
        self.timeArray,self.dataArray,self.errArray = [[],[],[]]
        for x in self.result:
            if x[0] > xmax:
                break
            elif x[0] < xmin:
                continue
            if timeMax > x[0]:
                binSum += x[1]
                errSum += (x[2]**2)
                count += 1
            else:
                self.timeArray.append(timeMax)
                self.dataArray.append(binSum/count)
                self.errArray.append(((errSum/count)**.5)/count**.5)
                count = 1
                binSum,errSum = 0,0
                timeMax += time_bin
            

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())