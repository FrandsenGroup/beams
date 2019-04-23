# View for BEAMS Application

# PyQt5 Libraries cover the main structure and function of the application
from PyQt5 import QtWidgets, QtGui, QtCore

# Matplotlib covers the plotting of the data, with necessary PyQt5 crossover libraries
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class MainGUIWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainGUIWindow,self).__init__()
        self.init_UI()

    def init_UI(self):
        self.init_menu_bar()
        self.init_panels()

    def init_panels(self):
        self.setGeometry(100,100,1700,900)
        self.setWindowTitle("BEAMS | Basic and Effective Analysis for Muon Spin-Spectroscopy")
        self.statusBar()
                
        self.file_manager = FileManagerPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.file_manager)
        
        self.plot_editor = PlotEditorPanel()
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.plot_editor)
        
        self.run_display = RunDisplayPanel()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.run_display)
        
        self.plot_panel = PlotPanel()
        self.setCentralWidget(self.plot_panel)

    def init_menu_bar(self):
        self.menu_bar = self.menuBar()

        self.exit_act = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)        
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.setStatusTip('Exit application')

        self.add_data_act = QtWidgets.QAction(QtGui.QIcon('addDada.png'), '&Add Data File', self) 
        self.add_data_act.setStatusTip('Add a data file to current session')

        self.format_act = QtWidgets.QAction(QtGui.QIcon(None),'&Format',self)
        self.format_act.setShortcut('Ctrl+F')
        self.format_act.setStatusTip('Specify format of unfamiliar files')

        file_menu = self.menu_bar.addMenu('&File')
        file_menu.addAction(self.add_data_act)
        file_menu.addAction(self.format_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)
        self.menu_bar.addMenu('&Help')


class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(FileManagerPanel,self).__init__()
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("File Manager")

        tempWidget = QtWidgets.QWidget()

        self.write_button = QtWidgets.QPushButton("Write")
        self.import_button = QtWidgets.QPushButton("Import")
        self.plot_button = QtWidgets.QPushButton("Plot")

        hbox_one = QtWidgets.QHBoxLayout()
        hbox_one.addWidget(self.write_button)
        hbox_one.addWidget(self.plot_button)
        hbox_one.addWidget(self.import_button)

        self.file_list = QtWidgets.QListWidget()

        hbox_two = QtWidgets.QHBoxLayout()
        hbox_two.addWidget(self.file_list)

        vbox_one = QtWidgets.QVBoxLayout()
        vbox_one.addLayout(hbox_one)
        vbox_one.addLayout(hbox_two)
        tempWidget.setLayout(vbox_one)

        self.setWidget(tempWidget)
        self.setFloating(False)


class PlotEditorPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(PlotEditorPanel,self).__init__()
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Graph Editor")
        self.init_sliders()
        self.init_input_boxes()
        self.setWidget(self.layout_UI())

    def init_sliders(self):
        self.slider_one = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_one.setMinimum(5)
        self.slider_one.setMaximum(500)
        self.slider_one.setValue(150)
        self.slider_one.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider_one.setTickInterval(20)

        self.slider_two = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_two.setMinimum(5)
        self.slider_two.setMaximum(500)
        self.slider_two.setValue(150)
        self.slider_two.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider_two.setTickInterval(20)

        self.input_slider_one = QtWidgets.QLineEdit()
        self.input_slider_two = QtWidgets.QLineEdit()
        self.input_slider_one.setFixedWidth(50)
        self.input_slider_two.setFixedWidth(50)
        self.input_slider_one.setText(str(self.slider_one.value()))
        self.input_slider_two.setText(str(self.slider_two.value()))

    def init_input_boxes(self):
        self.input_xmin_one = QtWidgets.QLineEdit()
        self.input_xmin_two = QtWidgets.QLineEdit()
        self.input_xmax_one = QtWidgets.QLineEdit()
        self.input_xmax_two = QtWidgets.QLineEdit()
        self.input_xmin_one.setFixedWidth(50)
        self.input_xmax_one.setFixedWidth(50)
        self.input_xmin_two.setFixedWidth(50)
        self.input_xmax_two.setFixedWidth(50)

        self.input_xmin_one.setText("1")
        self.input_xmin_two.setText("1")
        self.input_xmax_one.setText("4")
        self.input_xmax_two.setText("8")

    def layout_UI(self):
        label_xmin_one = QtWidgets.QLabel()
        label_xmin_two = QtWidgets.QLabel()
        label_xmax_one = QtWidgets.QLabel()
        label_xmax_two = QtWidgets.QLabel()
        label_xmin_one.setText("Plot 1 - XMin ("+chr(956)+"s)")
        label_xmax_one.setText("XMax ("+chr(956)+"s)")
        label_xmin_two.setText("Plot 2 - XMin ("+chr(956)+"s)")
        label_xmax_two.setText("XMax ("+chr(956)+"s)")
        slider_label_one = QtWidgets.QLabel()
        slider_label_one.setText("Time Bins (ns)")
        slider_label_two = QtWidgets.QLabel()
        slider_label_two.setText("Time Bins (ns)")

        temp_widget = QtWidgets.QWidget()
        row_one = QtWidgets.QHBoxLayout()
        row_two = QtWidgets.QHBoxLayout()

        row_one.addWidget(label_xmin_one)
        row_one.addWidget(self.input_xmin_one)
        row_one.addWidget(label_xmax_one)
        row_one.addWidget(self.input_xmax_one)
        row_one.addWidget(slider_label_one)
        row_one.addWidget(self.input_slider_one)
        row_one.addWidget(self.slider_one)

        row_two.addWidget(label_xmin_two)
        row_two.addWidget(self.input_xmin_two)
        row_two.addWidget(label_xmax_two)
        row_two.addWidget(self.input_xmax_two)
        row_two.addWidget(slider_label_two)
        row_two.addWidget(self.input_slider_two)
        row_two.addWidget(self.slider_two)

        col_one = QtWidgets.QVBoxLayout()
        col_one.addLayout(row_one)
        col_one.addLayout(row_two)

        temp_widget.setLayout(col_one)
        return temp_widget


class RunDisplayPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(RunDisplayPanel,self).__init__()
        self.init_UI()

    def init_UI(self):
        self.run_titles = QtWidgets.QComboBox()
        self.color_choices = QtWidgets.QComboBox()
        self.isolate_button = QtWidgets.QPushButton()
        self.current_run_title = QtWidgets.QLabel()
        self.header_data = QtWidgets.QComboBox()
        self.histograms = QtWidgets.QComboBox()
        self.inspect_button = QtWidgets.QPushButton()
        self.plot_all_button = QtWidgets.QPushButton()
        header_data_label = QtWidgets.QLabel()
        histogram_label = QtWidgets.QLabel()


class PlotPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(PlotPanel,self).__init__()
        self. init_UI()
        plt.ion()

    def init_UI(self):
        self.setWindowTitle("Graphing Area")
        tempWidget = QtWidgets.QWidget()

        self.canvas_one = RunPlot(parent=self)
        self.canvas_two = RunPlot(parent=self)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.canvas_one)
        hbox.addWidget(self.canvas_two)
        tempWidget.setLayout(hbox)

        self.setWidget(tempWidget)


class RunPlot(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):        
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


class FileFormatterUI(QtWidgets.QDialog):
        def __init__(self,filenames=None):
            super(FileFormatterUI,self).__init__()
            self.filenames = filenames
            self.initUI()

        def initUI(self):
            self.create_widgets()
            self.layout_widgets()
        
        def create_widgets(self):
            self.file_list = QtWidgets.QComboBox()
            self.file_list.addItems(self.filenames)

            self.apply_all_button = QtWidgets.QPushButton("Apply to All")
            self.apply_button = QtWidgets.QPushButton("Apply")
            self.done_button = QtWidgets.QPushButton("Done")
            self.advanced_button = QtWidgets.QPushButton("Advanced")
            self.file_display = QtWidgets.QPlainTextEdit()
            self.file_display.setWordWrapMode(False)
            self.input_other = QtWidgets.QLineEdit()

            self.label_info = QtWidgets.QLabel("Some of the files you wanted to plot were in an unrecognized format, specify the proper format in this app and press 'Apply'")
            self.label_header = QtWidgets.QLabel("Header Data (# Rows)")
            self.label_fhist = QtWidgets.QLabel("Front Histogram")
            self.label_bhist = QtWidgets.QLabel("Back Histogram ")
            self.label_rhist = QtWidgets.QLabel("Right Histogram")
            self.label_lhist = QtWidgets.QLabel("Left Histogram  ")
            self.label_asym = QtWidgets.QLabel("Asymmetry        ")
            self.label_time = QtWidgets.QLabel("Time                  ")
            self.label_uncertain = QtWidgets.QLabel("Uncertainty   ")
            self.label_error = QtWidgets.QLabel("Error          ")
            self.label_other = QtWidgets.QLabel("Other          ")
            self.label_checks = QtWidgets.QLabel("  |    Check Data in File")
            self.label_spins = QtWidgets.QLabel("Column")

            self.check_fhist = QtWidgets.QCheckBox(width=2)
            self.check_bhist = QtWidgets.QCheckBox(width=2)
            self.check_rhist = QtWidgets.QCheckBox(width=2)
            self.check_lhist = QtWidgets.QCheckBox(width=2)
            self.check_asym = QtWidgets.QCheckBox(width=2)
            self.check_time = QtWidgets.QCheckBox(width=2)
            self.check_uncertain = QtWidgets.QCheckBox(width=2)
            self.check_error = QtWidgets.QCheckBox(width=2)
            self.check_other = QtWidgets.QCheckBox(width=2)

            self.spin_fhist = QtWidgets.QSpinBox(width=10)
            self.spin_fhist.setEnabled(False)
            self.spin_bhist = QtWidgets.QSpinBox(width=10)
            self.spin_bhist.setEnabled(False)
            self.spin_rhist = QtWidgets.QSpinBox(width=10)
            self.spin_rhist.setEnabled(False)
            self.spin_lhist = QtWidgets.QSpinBox(width=10)
            self.spin_lhist.setEnabled(False)
            self.spin_asym = QtWidgets.QSpinBox(width=10)
            self.spin_asym.setEnabled(False)
            self.spin_time = QtWidgets.QSpinBox(width=10)
            self.spin_time.setEnabled(False)
            self.spin_uncertain = QtWidgets.QSpinBox(width=10)
            self.spin_uncertain.setEnabled(False)
            self.spin_error = QtWidgets.QSpinBox(width=10)
            self.spin_error.setEnabled(False)
            self.spin_other = QtWidgets.QSpinBox(width=10)
            self.spin_other.setEnabled(False)
            self.spin_header = QtWidgets.QSpinBox(width=10)

        def layout_widgets(self):
            main_layout = QtWidgets.QHBoxLayout()
            col_one = QtWidgets.QVBoxLayout()
            col_two = QtWidgets.QVBoxLayout()
            row_one = QtWidgets.QHBoxLayout()
            row_two = QtWidgets.QHBoxLayout()
            row_three = QtWidgets.QHBoxLayout()
            row_four = QtWidgets.QHBoxLayout()
            row_five = QtWidgets.QHBoxLayout()
            row_six = QtWidgets.QHBoxLayout()
            row_seven = QtWidgets.QHBoxLayout()
            row_eight = QtWidgets.QHBoxLayout()
            row_nine = QtWidgets.QHBoxLayout()
            row_ten = QtWidgets.QHBoxLayout()
            row_eleven = QtWidgets.QHBoxLayout()
            row_twelve = QtWidgets.QHBoxLayout()
            row_thirteen = QtWidgets.QHBoxLayout()

            col_one.addWidget(self.file_list)
            col_one.addWidget(self.file_display)
            row_one.addWidget(self.label_header)
            row_one.addWidget(self.spin_header)
            row_two.addWidget(self.label_spins)
            row_two.addWidget(self.label_checks)
            row_three.addWidget(self.spin_fhist)
            row_three.addWidget(self.check_fhist)
            row_three.addWidget(self.label_fhist)
            row_three.addSpacing(50)
            row_four.addWidget(self.spin_bhist)
            row_four.addWidget(self.check_bhist)
            row_four.addWidget(self.label_bhist)
            row_four.addSpacing(50)
            row_five.addWidget(self.spin_rhist)
            row_five.addWidget(self.check_rhist)
            row_five.addWidget(self.label_rhist)
            row_five.addSpacing(50)
            row_six.addWidget(self.spin_lhist)
            row_six.addWidget(self.check_lhist)
            row_six.addWidget(self.label_lhist)
            row_six.addSpacing(50)
            row_seven.addWidget(self.spin_asym)
            row_seven.addWidget(self.check_asym)
            row_seven.addWidget(self.label_asym)
            row_seven.addSpacing(50)
            row_eight.addWidget(self.spin_time)
            row_eight.addWidget(self.check_time)
            row_eight.addWidget(self.label_time)
            row_eight.addSpacing(50)
            row_nine.addWidget(self.spin_uncertain)
            row_nine.addWidget(self.check_uncertain)
            row_nine.addWidget(self.label_uncertain)
            row_nine.addSpacing(50)
            row_ten.addWidget(self.spin_error)
            row_ten.addWidget(self.check_error)
            row_ten.addWidget(self.label_error)
            row_ten.addSpacing(50)
            row_eleven.addWidget(self.spin_other)
            row_eleven.addWidget(self.check_other)
            row_eleven.addWidget(self.label_other)
            row_eleven.addSpacing(50)
            
            row_twelve.addWidget(self.apply_button)
            row_twelve.addWidget(self.apply_all_button)
            row_thirteen.addWidget(self.done_button)

            row_one.setAlignment(QtCore.Qt.AlignLeft)
            row_two.setAlignment(QtCore.Qt.AlignLeft)
            row_three.setAlignment(QtCore.Qt.AlignLeft)
            row_four.setAlignment(QtCore.Qt.AlignLeft)
            row_five.setAlignment(QtCore.Qt.AlignLeft)
            row_six.setAlignment(QtCore.Qt.AlignLeft)
            row_seven.setAlignment(QtCore.Qt.AlignLeft)
            row_eight.setAlignment(QtCore.Qt.AlignLeft)
            row_nine.setAlignment(QtCore.Qt.AlignLeft)
            row_ten.setAlignment(QtCore.Qt.AlignLeft)
            row_eleven.setAlignment(QtCore.Qt.AlignLeft)
            row_twelve.setAlignment(QtCore.Qt.AlignLeft)
            row_thirteen.setAlignment(QtCore.Qt.AlignLeft)

            col_two.setGeometry
            col_two.addLayout(row_one)
            col_two.addLayout(row_two)
            col_two.addLayout(row_three)
            col_two.addLayout(row_four)
            col_two.addLayout(row_five)
            col_two.addLayout(row_six)
            col_two.addLayout(row_seven)
            col_two.addLayout(row_eight)
            col_two.addLayout(row_nine)
            col_two.addLayout(row_ten)
            col_two.addLayout(row_eleven)
            col_two.addLayout(row_twelve)
            col_two.addLayout(row_thirteen)

            main_vertical = QtWidgets.QVBoxLayout()
            main_vertical.addWidget(self.label_info)
            main_layout.addLayout(col_one)
            main_layout.addLayout(col_two)
            main_vertical.addLayout(main_layout)

            self.setLayout(main_vertical)




