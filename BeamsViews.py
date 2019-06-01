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

        self.save_session_act = QtWidgets.QAction('&Save Session', self)
        self.save_session_act.setShortcut('Ctrl+s')
        self.save_session_act.setStatusTip('Save current session.')

        self.open_session_act = QtWidgets.QAction('&Open Session', self)
        self.open_session_act.setShortcut('Ctrl+o')
        self.open_session_act.setStatusTip('Open an old session. Current session will not be saved.')

        self.exit_act = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.setStatusTip('Exit application.')

        self.add_data_act = QtWidgets.QAction(QtGui.QIcon('addDada.png'), '&Add Data File', self)
        self.add_data_act.setStatusTip('Add a data file to current session.')

        self.format_act = QtWidgets.QAction(QtGui.QIcon(None), '&Format', self)
        self.format_act.setShortcut('Ctrl+F')
        self.format_act.setStatusTip('Specify format of unfamiliar files')

        file_menu = self.menu_bar.addMenu('&File')
        file_menu.addAction(self.add_data_act)
        file_menu.addAction(self.save_session_act)
        file_menu.addAction(self.open_session_act)
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
        hbox_one.addWidget(self.import_button)
        hbox_one.addWidget(self.convert_button)
        hbox_one.addWidget(self.plot_button)
        hbox_one.addWidget(self.write_button)

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
        # self.axes_freq.set_yticklabels([])
        self.axes_freq.set_xlim(0, 2.5)
        self.axes_freq.set_ylim(0, None)


# Formatter GUI

class FileFormatterUI(QtWidgets.QDialog):
    def __init__(self, filenames=None):
        super(FileFormatterUI, self).__init__()

        self.exec_()


# Other GUI's

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






