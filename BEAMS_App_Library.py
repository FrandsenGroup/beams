# Basics for Efficient Analysis of Muon Spin-Spectroscopy

from PyQt5 import QtWidgets, QtGui, QtCore

class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window,self).__init__()
        self.initUI()

    def initUI(self):
        print("initUI in Window Class")
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

        self.show()

    def Create_MenuBar(self):
        print("Create_MenuBar in Window Class")
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
        print("Create_FileManager in Window Class")
        self.fileControl = FileManagerPanel(parent=self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.fileControl)

    def Plot_Data(self):
        print("Plot_Data in Window Class")
        return



class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self,parent = None):
        super(FileManagerPanel,self).__init__()
        self.setParent(parent)

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
        print("Write_Button in FileManagerPanel Class")

    def Add_Button(self):
        print("Add_Button in FileManagerPanel Class")

    def Plot_Button(self,parent):
        print("Plot_Button in FileManagerPanel Class")
        parent.Plot_Data()



class GraphAreaPanel():
    def __init__(self):
        super(GraphAreaPanel,self).__init__()



class GraphEditorPanel():
    def __init__(self):
        super(GraphEditorPanel,self).__init__()



class RunInfoPanel():
    def __init__(self):
        super(RunInfoPanel,self).__init__()


