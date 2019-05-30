# View for BEAMS Application

# Installed modules
from PyQt5 import QtWidgets, QtGui, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt


# Main Window GUI and Panels
class MainGUIWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainGUIWindow, self).__init__()
        self.init_UI()

    def init_UI(self):
        self.init_menu_bar()
        self.init_panels()

    def init_panels(self):
        self.setGeometry(100, 100, 1700, 900)
        self.setWindowTitle("BEAMS | Basic and Effective Analysis for Muon Spin-Spectroscopy")
        self.statusBar()

        self.file_manager = FileManagerPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.file_manager)

        self.plot_editor = PlotEditorPanel()
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.plot_editor)

        self.run_display = RunDisplayPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.run_display)

        self.plot_panel = PlotPanel()
        self.setCentralWidget(self.plot_panel)

    def init_menu_bar(self):
        self.menu_bar = self.menuBar()

        self.exit_act = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.setStatusTip('Exit application')

        self.add_data_act = QtWidgets.QAction(QtGui.QIcon('addDada.png'), '&Add Data File', self)
        self.add_data_act.setStatusTip('Add a data file to current session')

        self.format_act = QtWidgets.QAction(QtGui.QIcon(None), '&Format', self)
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
        super(FileManagerPanel, self).__init__()
        self.setWindowTitle("File Manager")

        tempWidget = QtWidgets.QWidget()

        self.write_button = QtWidgets.QPushButton("Write")
        self.import_button = QtWidgets.QPushButton("+")
        self.plot_button = QtWidgets.QPushButton("Plot")
        self.convert_button = QtWidgets.QPushButton("Convert")

        self.import_button.setFixedWidth(30)

        self.write_button.setToolTip('Write currently plotted data to .dat files')
        self.import_button.setToolTip('Add files')
        self.plot_button.setToolTip('Plot currently selected files')
        self.convert_button.setToolTip('Convert .msr formatted files to .dat ')

        hbox_one = QtWidgets.QHBoxLayout()
        hbox_one.addWidget(self.write_button)
        hbox_one.addWidget(self.plot_button)
        hbox_one.addWidget(self.convert_button)
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
        super(PlotEditorPanel, self).__init__()
        self.init_UI()

    def init_UI(self):
        self.setWindowTitle("Graph Editor")
        self.init_check_options()
        self.init_sliders()
        self.init_input_boxes()
        self.setWidget(self.layout_UI())

    def init_check_options(self):
        self.check_uncertain = QtWidgets.QCheckBox()
        self.check_annotation = QtWidgets.QCheckBox()
        self.check_plot_lines = QtWidgets.QCheckBox()
        self.check_autoscale_one = QtWidgets.QCheckBox()
        self.check_autoscale_two = QtWidgets.QCheckBox()
        self.check_uncertain.setChecked(True)
        self.check_autoscale_one.setChecked(True)
        self.check_autoscale_two.setChecked(True)
        self.label_uncertain = QtWidgets.QLabel('Show Uncertainty')
        self.label_annotation = QtWidgets.QLabel('Show Annotations')
        self.label_plot_lines = QtWidgets.QLabel('Show Plot Lines')

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
        self.input_ymin_one = QtWidgets.QLineEdit()
        self.input_ymin_two = QtWidgets.QLineEdit()
        self.input_ymax_one = QtWidgets.QLineEdit()
        self.input_ymax_two = QtWidgets.QLineEdit()
        self.input_xmin_one.setFixedWidth(50)
        self.input_xmax_one.setFixedWidth(50)
        self.input_xmin_two.setFixedWidth(50)
        self.input_xmax_two.setFixedWidth(50)
        self.input_ymin_one.setFixedWidth(50)
        self.input_ymin_two.setFixedWidth(50)
        self.input_ymax_one.setFixedWidth(50)
        self.input_ymax_two.setFixedWidth(50)

        self.input_xmin_one.setText("1")
        self.input_xmin_two.setText("1")
        self.input_xmax_one.setText("4")
        self.input_xmax_two.setText("8")
        self.input_ymin_one.setText("-0.5")
        self.input_ymin_two.setText("0.5")
        self.input_ymax_one.setText("-0.5")
        self.input_ymax_two.setText("0.5")
        self.input_ymax_one.setEnabled(False)
        self.input_ymax_two.setEnabled(False)
        self.input_ymin_one.setEnabled(False)
        self.input_ymin_two.setEnabled(False)

    def layout_UI(self):
        try:  # Deals with issues with mu symbol
            label_xmin_one = QtWidgets.QLabel("XMin (" + chr(956) + "s)")
            label_xmin_two = QtWidgets.QLabel("XMin (" + chr(956) + "s)")
            label_xmax_one = QtWidgets.QLabel("XMax (" + chr(956) + "s)")
            label_xmax_two = QtWidgets.QLabel("XMax (" + chr(956) + "s)")
        except ValueError:
            try:
                label_xmin_one = QtWidgets.QLabel("XMin (\u03BCs)")
                label_xmin_two = QtWidgets.QLabel("XMin (\u03BCs)")
                label_xmax_one = QtWidgets.QLabel("XMax (\u03BCs)")
                label_xmax_two = QtWidgets.QLabel("XMax (\u03BCs)")
            except ValueError:
                label_xmin_one = QtWidgets.QLabel("XMin (micro-sec)")
                label_xmin_two = QtWidgets.QLabel("XMin (micro-sec)")
                label_xmax_one = QtWidgets.QLabel("XMax (micro-sec)")
                label_xmax_two = QtWidgets.QLabel("XMax (micro-sec)")
                
        label_ymin_one = QtWidgets.QLabel("YMin")
        label_ymin_two = QtWidgets.QLabel("YMin")
        label_ymax_one = QtWidgets.QLabel("YMax")
        label_ymax_two = QtWidgets.QLabel("YMax")
        slider_label_one = QtWidgets.QLabel("Time Bins (ns)")
        slider_label_two = QtWidgets.QLabel("Time Bins (ns)")
        label_auto_one = QtWidgets.QLabel("Plot 1 -     Auto")
        label_auto_two = QtWidgets.QLabel("Plot 2 -     Auto")

        temp_widget = QtWidgets.QWidget()
        row_one = QtWidgets.QHBoxLayout()
        row_two = QtWidgets.QHBoxLayout()

        row_one.addWidget(label_auto_one)
        row_one.addWidget(self.check_autoscale_one)
        row_one.addSpacing(10)
        row_one.addWidget(label_ymin_one)
        row_one.addWidget(self.input_ymin_one)
        row_one.addSpacing(10)
        row_one.addWidget(label_ymax_one)
        row_one.addWidget(self.input_ymax_one)
        row_one.addSpacing(10)
        row_one.addWidget(label_xmin_one)
        row_one.addWidget(self.input_xmin_one)
        row_one.addSpacing(10)
        row_one.addWidget(label_xmax_one)
        row_one.addWidget(self.input_xmax_one)
        row_one.addSpacing(10)
        row_one.addWidget(slider_label_one)
        row_one.addWidget(self.input_slider_one)
        row_one.addSpacing(10)
        row_one.addWidget(self.slider_one)

        row_two.addWidget(label_auto_two)
        row_two.addWidget(self.check_autoscale_two)
        row_two.addSpacing(10)
        row_two.addWidget(label_ymin_two)
        row_two.addWidget(self.input_ymin_two)
        row_two.addSpacing(10)
        row_two.addWidget(label_ymax_two)
        row_two.addWidget(self.input_ymax_two)
        row_two.addSpacing(10)
        row_two.addWidget(label_xmin_two)
        row_two.addWidget(self.input_xmin_two)
        row_two.addSpacing(10)
        row_two.addWidget(label_xmax_two)
        row_two.addWidget(self.input_xmax_two)
        row_two.addSpacing(10)
        row_two.addWidget(slider_label_two)
        row_two.addWidget(self.input_slider_two)
        row_two.addSpacing(10)
        row_two.addWidget(self.slider_two)

        col_one = QtWidgets.QVBoxLayout()
        col_one.addLayout(row_one)
        col_one.addLayout(row_two)

        col_two = QtWidgets.QVBoxLayout()

        row_unc = QtWidgets.QHBoxLayout()
        row_unc.addWidget(self.check_uncertain)
        row_unc.addWidget(self.label_uncertain)
        row_unc.setAlignment(QtCore.Qt.AlignLeft)
        row_ann = QtWidgets.QHBoxLayout()
        row_ann.addWidget(self.check_annotation)
        row_ann.addWidget(self.label_annotation)
        row_ann.setAlignment(QtCore.Qt.AlignLeft)
        row_lns = QtWidgets.QHBoxLayout()
        row_lns.addWidget(self.check_plot_lines)
        row_lns.addWidget(self.label_plot_lines)
        row_lns.setAlignment(QtCore.Qt.AlignLeft)

        col_two.addLayout(row_unc)
        col_two.addLayout(row_ann)
        col_two.addLayout(row_lns)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(col_one)
        main_layout.addLayout(col_two)

        temp_widget.setLayout(main_layout)
        return temp_widget


class RunDisplayPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(RunDisplayPanel, self).__init__()
        self.init_UI()

    def init_UI(self):
        self.create_widgets()
        self.layout_widgets()
        self.setWindowTitle('Run Display')

    def create_widgets(self):
        self.display_label = QtWidgets.QLabel("Choose a currently plotted run below.\n")
        self.run_titles = QtWidgets.QComboBox()
        self.run_titles.addItem("No Runs Plotted")
        self.color_choices = QtWidgets.QComboBox()
        self.color_choices.setEnabled(False)
        self.color_choices.addItems(["None", "blue", "red", "green", "orange", "purple",
                                     "brown", "yellow", "gray", "olive", "cyan", "pink", "custom"])
        self.isolate_button = QtWidgets.QPushButton("Isolate")
        self.isolate_button.setEnabled(False)
        self.header_data = QtWidgets.QComboBox()
        self.header_data.setEnabled(False)
        self.header_display = QtWidgets.QLineEdit()
        self.header_display.setEnabled(False)
        self.histograms = QtWidgets.QComboBox()
        self.histograms.addItem("None")
        self.histograms.setEnabled(False)
        self.inspect_hist_button = QtWidgets.QPushButton("Inspect Hist")
        self.inspect_hist_button.setEnabled(False)
        self.inspect_file_button = QtWidgets.QPushButton("Inspect File")
        self.inspect_file_button.setEnabled(False)
        self.plot_all_button = QtWidgets.QPushButton("Plot All Runs")
        self.plot_all_button.setEnabled(False)
        self.header_data_label = QtWidgets.QLabel()
        self.histogram_label = QtWidgets.QLabel()

    def layout_widgets(self):
        tempWidget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.display_label)
        main_layout.addWidget(self.run_titles)

        row_one = QtWidgets.QHBoxLayout()
        row_one.addWidget(self.isolate_button)
        row_one.addWidget(self.color_choices)
        row_two = QtWidgets.QHBoxLayout()
        row_two.addWidget(self.histograms)
        row_two.addWidget(self.inspect_hist_button)
        row_two.addWidget(self.inspect_file_button)
        row_thr = QtWidgets.QHBoxLayout()
        row_thr.addWidget(self.header_data)  # Disable if not BEAMS
        row_thr.addWidget(self.header_display)  # Disable if not BEAMS

        main_layout.addLayout(row_one)
        main_layout.addLayout(row_two)
        main_layout.addLayout(row_thr)
        main_layout.addWidget(self.plot_all_button)

        main_layout.addStretch(1)
        tempWidget.setLayout(main_layout)
        self.setWidget(tempWidget)


class PlotPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(PlotPanel, self).__init__()

        self.init_center_UI()

        plt.ion()

    def init_center_UI(self):
        self.setWindowTitle("Graphing Area")
        tempWidget = QtWidgets.QWidget()

        self.canvas_one = RunPlot()
        self.canvas_two = RunPlot()
        self.linestyle = 'None'

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.canvas_one)
        hbox.addWidget(self.canvas_two)
        tempWidget.setLayout(hbox)

        self.setWidget(tempWidget)


class HistogramDisplay(QtWidgets.QDockWidget):
    def __init__(self, histogram=None):
        super(HistogramDisplay, self).__init__()
        temp_widget = QtWidgets.QWidget()
        self.canvas = CanvasUI()

        layout_hist = QtWidgets.QHBoxLayout()
        layout_hist.addWidget(self.canvas)
        temp_widget.setLayout(layout_hist)
        self.setWidget(temp_widget)
        plt.ion()

        self.canvas.canvas_axes.plot(histogram, linestyle='None', marker='s')
        # self.exec_()


class CanvasUI(FigureCanvas):
    def __init__(self):
        fig = plt.figure(dpi=100)
        self.canvas_axes = fig.add_subplot(111, label='Canvas')
        self._draw_pending = True
        FigureCanvas.__init__(self, fig)


class RunPlot(FigureCanvas):
    def __init__(self, dpi=100):
        fig = plt.figure(dpi=dpi)
        self.axes_time = fig.add_subplot(211, label="Time Domain")
        self.axes_freq = fig.add_subplot(212, label="Frequency Domain")
        self.set_style()
        FigureCanvas.__init__(self, fig)

    def set_style(self):
        self.axes_time.spines['right'].set_visible(False)
        self.axes_time.spines['top'].set_visible(False)
        self.axes_time.tick_params(bottom=False, left=False)
        self.axes_time.set_xlabel("Time (" + chr(956) + "s)")
        self.axes_time.set_ylabel("Asymmetry")

        self.axes_freq.spines['right'].set_visible(False)
        self.axes_freq.spines['top'].set_visible(False)
        self.axes_freq.tick_params(bottom=False, left=False)
        self.axes_freq.set_xlabel("Frequency (MHz)")
        self.axes_freq.set_ylabel("Magnitude")
        self.axes_freq.set_yticklabels([])
        self.axes_freq.set_xlim(0, 2.5)
        self.axes_freq.set_ylim(0, None)


# Miscellaneous GUIs

class FileFormatterUI(QtWidgets.QDialog):
    def __init__(self, filenames=None):
        super(FileFormatterUI, self).__init__()
        self.selected_columns = []
        self.filenames = filenames
        self.initUI()

    def initUI(self):
        self.create_widgets()
        self.set_intitial_states()
        self.format_widgets()
        self.file_list.addItems(self.filenames)
        self.layout_widgets()

    def create_widgets(self):
        self.file_list = QtWidgets.QComboBox()
        self.apply_all_button = QtWidgets.QPushButton("Apply to All")
        self.apply_button = QtWidgets.QPushButton("Apply")
        self.done_button = QtWidgets.QPushButton("Done")
        self.inspect_button = QtWidgets.QPushButton("Inspect")
        self.skip_button = QtWidgets.QPushButton("Skip File")
        self.file_display = QtWidgets.QPlainTextEdit()
        self.columns = QtWidgets.QComboBox()
        self.inspect_column = QtWidgets.QPushButton("Inspect Column")
        self.bin_input = QtWidgets.QLineEdit()
        self.initial_t = QtWidgets.QLineEdit()
        # self.start_t = QtWidgets.QLineEdit()

        self.label_info = QtWidgets.QLabel(
            "Some of the files you wanted to plot were in an unrecognized format, specify the proper format in this app and press 'Apply'\n")
        self.label_header = QtWidgets.QLabel("Header Data (# Rows)")
        self.label_fhist = QtWidgets.QLabel("Front Histogram")
        self.label_bhist = QtWidgets.QLabel("Back Histogram ")
        self.label_rhist = QtWidgets.QLabel("Right Histogram")
        self.label_lhist = QtWidgets.QLabel("Left Histogram")
        self.label_asym = QtWidgets.QLabel("Asymmetry")
        self.label_time = QtWidgets.QLabel("Time")
        self.label_uncertain = QtWidgets.QLabel("Uncertainty")
        self.label_error = QtWidgets.QLabel("Error")
        self.label_checks = QtWidgets.QLabel("    |      Check Data in File")
        self.label_spins = QtWidgets.QLabel("Column")

        self.check_fhist = QtWidgets.QCheckBox(width=2)
        self.check_bhist = QtWidgets.QCheckBox(width=2)
        self.check_rhist = QtWidgets.QCheckBox(width=2)
        self.check_lhist = QtWidgets.QCheckBox(width=2)
        self.check_asym = QtWidgets.QCheckBox(width=2)
        self.check_time = QtWidgets.QCheckBox(width=2)
        self.check_uncertain = QtWidgets.QCheckBox(width=2)
        self.check_error = QtWidgets.QCheckBox(width=2)

        self.spin_fhist = QtWidgets.QSpinBox(width=10)
        self.spin_bhist = QtWidgets.QSpinBox(width=10)
        self.spin_rhist = QtWidgets.QSpinBox(width=10)
        self.spin_lhist = QtWidgets.QSpinBox(width=10)
        self.spin_asym = QtWidgets.QSpinBox(width=10)
        self.spin_time = QtWidgets.QSpinBox(width=10)
        self.spin_uncertain = QtWidgets.QSpinBox(width=10)
        self.spin_error = QtWidgets.QSpinBox(width=10)
        self.spin_header = QtWidgets.QSpinBox(width=10)

    def set_intitial_states(self):
        self.columns.clear()
        self.spin_asym.setValue(0)
        self.spin_fhist.setValue(0)
        self.spin_bhist.setValue(0)
        self.spin_rhist.setValue(0)
        self.spin_lhist.setValue(0)
        self.spin_time.setValue(0)
        self.spin_uncertain.setValue(0)
        self.spin_header.setValue(0)
        self.check_asym.setChecked(False)
        self.check_fhist.setChecked(False)
        self.check_rhist.setChecked(False)
        self.check_lhist.setChecked(False)
        self.check_bhist.setChecked(False)
        self.check_uncertain.setChecked(False)
        self.check_time.setChecked(False)
        self.bin_input.clear()
        self.initial_t.clear()
        # self.start_t.clear()
        self.file_display.clear()
        self.bin_input.setEnabled(False)
        self.initial_t.setEnabled(False)
        # self.start_t.setEnabled(False)
        self.spin_fhist.setEnabled(False)
        self.spin_bhist.setEnabled(False)
        self.spin_rhist.setEnabled(False)
        self.spin_lhist.setEnabled(False)
        self.spin_asym.setEnabled(False)
        self.spin_time.setEnabled(False)
        self.spin_uncertain.setEnabled(False)
        self.spin_error.setEnabled(False)

    def format_widgets(self):
        self.apply_all_button.setFixedWidth(85)
        self.apply_button.setFixedWidth(85)
        self.done_button.setFixedWidth(85)
        self.skip_button.setFixedWidth(85)
        self.columns.setFixedWidth(85)
        self.inspect_column.setFixedWidth(85)
        self.bin_input.setFixedWidth(85)
        self.initial_t.setFixedWidth(85)
        # self.start_t.setFixedWidth(40)
        self.file_display.setWordWrapMode(False)
        self.bin_input.setPlaceholderText("Time Bin Size")
        self.initial_t.setPlaceholderText("Initial Bin")
        # self.start_t.setPlaceholderText("Start Bin")

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
        row_three.addSpacing(5)
        row_three.addWidget(self.check_fhist)
        row_three.addSpacing(5)
        row_three.addWidget(self.label_fhist)
        row_three.addSpacing(50)
        row_four.addWidget(self.spin_bhist)
        row_four.addSpacing(5)
        row_four.addWidget(self.check_bhist)
        row_four.addSpacing(5)
        row_four.addWidget(self.label_bhist)
        row_four.addSpacing(50)
        row_five.addWidget(self.spin_rhist)
        row_five.addSpacing(5)
        row_five.addWidget(self.check_rhist)
        row_five.addSpacing(5)
        row_five.addWidget(self.label_rhist)
        row_five.addSpacing(50)
        row_six.addWidget(self.spin_lhist)
        row_six.addSpacing(5)
        row_six.addWidget(self.check_lhist)
        row_six.addSpacing(5)
        row_six.addWidget(self.label_lhist)
        row_six.addSpacing(50)
        row_seven.addWidget(self.spin_asym)
        row_seven.addSpacing(5)
        row_seven.addWidget(self.check_asym)
        row_seven.addSpacing(5)
        row_seven.addWidget(self.label_asym)
        row_seven.addSpacing(50)
        row_eight.addWidget(self.spin_time)
        row_eight.addSpacing(5)
        row_eight.addWidget(self.check_time)
        row_eight.addSpacing(5)
        row_eight.addWidget(self.label_time)
        row_eight.addSpacing(50)
        row_nine.addWidget(self.spin_uncertain)
        row_nine.addSpacing(5)
        row_nine.addWidget(self.check_uncertain)
        row_nine.addSpacing(5)
        row_nine.addWidget(self.label_uncertain)
        row_nine.addSpacing(50)
        row_ten.addWidget(self.columns)
        # row_ten.addSpacing(15)
        row_ten.addWidget(self.inspect_column)
        row_ten.addSpacing(50)
        row_eleven.addWidget(self.bin_input)
        row_eleven.addWidget(self.initial_t)
        # row_eleven.addWidget(self.start_t)
        row_eleven.addSpacing(50)

        row_twelve.addWidget(self.apply_button)
        row_twelve.addWidget(self.apply_all_button)
        row_thirteen.addWidget(self.done_button)
        row_thirteen.addWidget(self.skip_button)

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
        col_two.addLayout(row_eleven)
        col_two.addLayout(row_ten)
        col_two.addLayout(row_twelve)
        col_two.addLayout(row_thirteen)

        main_vertical = QtWidgets.QVBoxLayout()
        main_vertical.addWidget(self.label_info)
        main_layout.addLayout(col_one)
        main_layout.addSpacing(20)
        main_layout.addLayout(col_two)
        main_vertical.addLayout(main_layout)

        self.setLayout(main_vertical)


class FileDisplayUI(QtWidgets.QPlainTextEdit):
    def __init__(self, filename=None):
        super(FileDisplayUI, self).__init__()
        if filename:
            self.filename = filename
            self.setGeometry(500, 300, 400, 400)
            self.setPlainText(open(self.filename).read())
            self.setWordWrapMode(False)


class WriteDataUI(QtWidgets.QDialog):
    def __init__(self):
        super(WriteDataUI, self).__init__()
        self.init_UI()

    def init_UI(self):
        self.create_widgets()
        self.layout_widgets()

    def create_widgets(self):
        self.file_list = QtWidgets.QComboBox()
        self.select_folder = QtWidgets.QPushButton('Select Folder')
        self.skip_file = QtWidgets.QPushButton('Skip File')
        self.write_file = QtWidgets.QPushButton('Write')
        self.write_all = QtWidgets.QPushButton('Write All')
        self.done = QtWidgets.QPushButton('Done')
        self.input_filename = QtWidgets.QLineEdit()
        self.input_filename.setPlaceholderText('Default is [filename]_data.dat')
        self.check_asymmetry = QtWidgets.QCheckBox()
        self.check_asymmetry.setChecked(True)
        self.check_time = QtWidgets.QCheckBox()
        self.check_time.setChecked(True)
        self.check_uncertainty = QtWidgets.QCheckBox()
        self.check_uncertainty.setChecked(True)
        self.label_asymmetry = QtWidgets.QLabel('Asymmetry')
        self.label_time = QtWidgets.QLabel('Time')
        self.label_uncertainty = QtWidgets.QLabel('Uncertainty')

    def layout_widgets(self):
        col_one = QtWidgets.QVBoxLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_two = QtWidgets.QHBoxLayout()
        row_thr = QtWidgets.QHBoxLayout()

        col_one.addWidget(self.file_list)

        row_one.addWidget(self.select_folder)
        row_one.addWidget(self.input_filename)
        col_one.addLayout(row_one)

        row_two.addWidget(self.check_asymmetry)
        row_two.addWidget(self.label_asymmetry)
        row_two.addSpacing(10)
        row_two.addWidget(self.check_time)
        row_two.addWidget(self.label_time)
        row_two.addSpacing(10)
        row_two.addWidget(self.check_uncertainty)
        row_two.addWidget(self.label_uncertainty)
        row_two.setAlignment(QtCore.Qt.AlignLeft)
        col_one.addLayout(row_two)
        col_one.addSpacing(25)

        row_thr.addWidget(self.skip_file)
        row_thr.addSpacing(5)
        row_thr.addWidget(self.write_file)
        row_thr.addSpacing(5)
        row_thr.addWidget(self.write_all)
        row_thr.addSpacing(20)
        row_thr.addWidget(self.done)
        row_thr.setAlignment(QtCore.Qt.AlignLeft)
        col_one.addLayout(row_thr)

        self.setLayout(col_one)


class PlotDataUI(QtWidgets.QDialog):
    def __init__(self):
        super(PlotDataUI, self).__init__()
        self.t_tip = QtWidgets.QLabel('Specify the two histograms you want to use calculate the asymmetry.')
        self.c_file_list = QtWidgets.QComboBox()
        self.c_hist_one = QtWidgets.QComboBox()
        self.c_hist_two = QtWidgets.QComboBox()
        self.b_apply = QtWidgets.QPushButton('Apply')
        self.b_apply_all = QtWidgets.QPushButton('Apply All')
        self.b_plot = QtWidgets.QPushButton('Plot')
        self.b_skip = QtWidgets.QPushButton('Skip')
        self.b_cancel = QtWidgets.QPushButton('Cancel')
        self.layout_widgets()

    def layout_widgets(self):
        col = QtWidgets.QVBoxLayout()
        row_1 = QtWidgets.QHBoxLayout()
        row_2 = QtWidgets.QHBoxLayout()

        col.addWidget(self.t_tip)
        col.addWidget(self.c_file_list)
        row_1.addWidget(self.c_hist_one)
        row_1.addWidget(self.c_hist_two)
        row_2.addWidget(self.b_apply)
        row_2.addWidget(self.b_apply_all)
        row_2.addWidget(self.b_skip)
        row_2.addWidget(self.b_plot)
        row_2.addWidget(self.b_cancel)
        col.addLayout(row_1)
        col.addLayout(row_2)

        self.setLayout(col)


# Support GUIs
class ErrorMessageUI(QtWidgets.QDialog):
    def __init__(self, error_message=None, pos_function=None):
        super(ErrorMessageUI, self).__init__()
        self.setWindowTitle('Error')
        message = QtWidgets.QLabel(error_message)
        pos_button = QtWidgets.QPushButton('Okay')

        if pos_function:
            pos_button.released.connect(lambda: pos_function())

        pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)
        col.addWidget(pos_button)
        self.setLayout(col)

        self.exec_()


class PermissionsMessageUI(QtWidgets.QDialog):
    def __init__(self, permissions_message=None, pos_function=None, neg_function=None):
        super(PermissionsMessageUI, self).__init__()
        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel(permissions_message)
        self.pos_button = QtWidgets.QPushButton('Okay')
        self.neg_button = QtWidgets.QPushButton('Cancel')

        if pos_function:
            self.pos_button.released.connect(lambda: pos_function())

        if neg_function:
            self.neg_button.released.connect(lambda: neg_function())

        self.neg_button.released.connect(lambda: self.close())
        self.pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        col.addLayout(row)
        self.setLayout(col)

        self.exec_()






