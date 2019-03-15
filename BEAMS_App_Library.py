# Basics for Efficient Analysis of Muon Spin-Spectroscopy



from PyQt5 import QtWidgets, QtGui, QtCore



class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window,self).__init__()
        self.initUI()

    def initUI(self):
        print("initUI Function :: Window Class")
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
        print("Create_MenuBar Function :: Window Class")
        #MENUBAR ITEMS
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
        print("Create_FileManager Function :: Window Class")
        self.fileControl = FileManagerPanel(parent=self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.fileControl)

    def Create_GraphEditor(self):
        print("Create_GraphEditor Function :: Window Class")
        self.graphEditor = GraphEditorPanel(parent=self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.graphEditor)

    def Create_GraphArea(self):
        print("Create_GraphArea Function :: Window Class")
        self.graphArea = GraphAreaPanel(parent=self)
        self.setCentralWidget(self.graphArea)

    def Create_RunInfoPanel(self):
        print("Create_RunInfoPanel Function :: Window Class")
        self.runInfo = RunInfoPanel(parent=self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.runInfo)

    def Plot_Data(self,graph_num):
        print("Plot_Data Function :: Window Class")
        return



class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self,parent = None):
        print("init Function :: FileManagerPanel Class")
        super(FileManagerPanel,self).__init__()
        self.setParent(parent)
        self.setWindowTitle("File Manager")

        tempWidget = QtWidgets.QWidget()

        writeButton = QtWidgets.QPushButton()
        writeButton.setText("Write")
        writeButton.released.connect(lambda: self.Write_Button())

        addButton = QtWidgets.QPushButton()
        addButton.setText("+")
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
        print("Write_Button Function :: FileManagerPanel Class")

    def Add_Button(self):
        print("Add_Button Function :: FileManagerPanel Class")
        # FIXME Use getOpenFileNames to get multiple files at once.
        filename = QtWidgets.QFileDialog.getOpenFileName(self,'Add file','/home')
        file_item = QtWidgets.QListWidgetItem(filename[0],self.listWidget)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)

    def Plot_Button(self,parent):
        print("Plot_Button Function :: FileManagerPanel Class")
        parent.Plot_Data(1)
        



class GraphAreaPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        print("init Function :: GraphAreaPanel Class")
        super(GraphAreaPanel,self).__init__()
        self.setParent(parent)
        self.setWindowTitle("Graphing Area")
        self.setWidget(QtWidgets.QWidget())



class GraphEditorPanel(QtWidgets.QDockWidget):
    def __init__(self,parent = None):
        print("init Function :: GraphEditorPanel Class")
        super(GraphEditorPanel,self).__init__()
        self.setParent(parent)
        self.setWindowTitle("Graph Editor")

        slider_one_label = QtWidgets.QLabel()
        slider_one_label.setText("Time Bins (ns)")
        slider_two_label = QtWidgets.QLabel()
        slider_two_label.setText("Time Bins (ns)")

        self.slider_one = self.Create_Slider()
        self.slider_two = self.Create_Slider()

        self.slider_one.sliderReleased.connect(lambda: self.Slider_Changed(self.slider_one_text, self.slider_one.value(),1))
        self.slider_two.sliderReleased.connect(lambda: self.Slider_Changed(self.slider_two_text, self.slider_two.value(),2))
        
        self.slider_one_text = QtWidgets.QLineEdit()
        self.slider_one_text.setText(str(self.slider_one.value()))
        self.slider_one_text.setFixedWidth(50)
        self.slider_one_text.returnPressed.connect(lambda: self.Slider_Text_Changed(self.slider_one,self.slider_one_text.text(),1))

        self.slider_two_text = QtWidgets.QLineEdit()
        self.slider_two_text.setText(str(self.slider_two.value()))
        self.slider_two_text.setFixedWidth(50)
        self.slider_two_text.returnPressed.connect(lambda: self.Slider_Text_Changed(self.slider_two,self.slider_two_text.text(),2))

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
        print("Create_Slider Function :: GraphEditorPanel Class")
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setMinimum(1)
        slider.setMaximum(500)
        slider.setValue(150)
        slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        slider.setTickInterval(20)
        return slider

    def Create_Input_Boxes(self,box_value,graph_num):
        print("Create_Input_Boxes Function :: GraphEditorPanel Class")
        input_box = QtWidgets.QLineEdit()
        input_box.setText(box_value)
        input_box.setFixedWidth(50)
        input_box.returnPressed.connect(lambda: self.parent.Plot_Data(graph_num))
        return input_box

    def Create_Input_Box_Label(self,box_label):
        print("Create_Input_Box_Label Function :: GraphEditorPanel Class")
        input_box_label = QtWidgets.QLabel()
        input_box_label.setText(box_label)
        return input_box_label

    def Create_Layout(self, label_x_one, label_x_two, label_x_three, label_x_four, label_s_one, label_s_two):
        print("Create_Layout Function :: GraphEditorPanel Class")
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

    def Slider_Changed(self, slider, slider_value, graph_num):
        print("Slider_Changed Function :: GraphEditorPanel Class")

    def Slider_Text_Changed(self, slider, slider_text, graph_num):
        print("Slider_Text_Changed Function :: GraphEditorPanel Class")



class RunInfoPanel(QtWidgets.QDockWidget):
    def __init__(self,parent=None):
        print("init Function :: RunInfoPanel Class")
        super(RunInfoPanel,self).__init__()
        self.setParent(parent)
        self.setWindowTitle("Run Information")
        self.setWidget(QtWidgets.QWidget())


