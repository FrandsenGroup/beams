# View for BEAMS Application

# Installed modules
from PyQt5 import QtWidgets, QtGui, QtCore
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas,
                                                NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

style_imported = False


# noinspection PyArgumentList
class MainGUIWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainGUIWindow, self).__init__()

        self.setGeometry(100, 100, 1700, 900)
        self.setWindowTitle("BEAMS | Basic and Effective Analysis for Muon Spin-Spectroscopy")
        self.statusBar()

        # Initialize Panels in Main Window
        self.file_manager = FileManagerPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.file_manager)

        self.plot_editor = PlotEditorPanel()
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.plot_editor)

        self.run_display = RunDisplayPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.run_display)

        self.mufyt_panel = MuFytPanel()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.mufyt_panel)

        self.plot_panel = PlotPanel()
        self.setCentralWidget(self.plot_panel)

        self.addToolBar(NavigationToolbar(self.plot_panel.canvas_one, self))

        # Initialize Menu Bar for Main Window
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


# noinspection PyArgumentList
class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(FileManagerPanel, self).__init__()
        self.setWindowTitle("File Manager")

        # Create our widget which will hold everything for this panel.
        self._full_widget = QtWidgets.QWidget()

        # Create Widgets
        self.file_list = QtWidgets.QListWidget()
        self.select_all = QtWidgets.QCheckBox()
        self.write_button = QtWidgets.QPushButton("Write")
        self.import_button = QtWidgets.QPushButton("+")
        self.remove_button = QtWidgets.QPushButton('-')
        self.plot_button = QtWidgets.QPushButton("Plot")
        self.convert_button = QtWidgets.QPushButton("Convert")

        # Set Widget Dimensions
        self.select_all.setFixedWidth(20)
        self.import_button.setFixedWidth(25)
        self.remove_button.setFixedWidth(25)
        self.write_button.setFixedWidth(60)
        self.plot_button.setFixedWidth(60)
        self.convert_button.setFixedWidth(60)

        # Set Widget Tooltips
        self.write_button.setToolTip('Write currently plotted data to .asy files')
        self.import_button.setToolTip('Add files')
        self.remove_button.setToolTip('Remove currently selected files.')
        self.plot_button.setToolTip('Plot currently selected files')
        self.convert_button.setToolTip('Convert .msr formatted files to .dat ')
        self.select_all.setToolTip('Select all files.')

        # Layout Widgets
        hbox_one = QtWidgets.QHBoxLayout()
        hbox_one.addWidget(self.select_all, alignment=QtCore.Qt.AlignCenter)
        hbox_one.addWidget(self.import_button)
        hbox_one.addWidget(self.remove_button)
        hbox_one.addWidget(self.convert_button)
        hbox_one.addWidget(self.plot_button)
        hbox_one.addWidget(self.write_button)

        hbox_two = QtWidgets.QHBoxLayout()
        hbox_two.addWidget(self.file_list)

        vbox_one = QtWidgets.QVBoxLayout()
        vbox_one.addLayout(hbox_one)
        vbox_one.addLayout(hbox_two)
        self._full_widget.setLayout(vbox_one)

        # Set DockWidget to be fully laid out widget.
        self.setWidget(self._full_widget)
        self.setFloating(False)


# Yo Dylan! See FileManagerPanel above for a good example.
# noinspection PyArgumentList
class MuFytPanel(QtWidgets.QDockWidget):
    def __init__(self):
        # Call superclass so all dock widget attributes are initialized.
        super(MuFytPanel, self).__init__()
        self.setWindowTitle('Fit Data')

        # Create a widget which will hold everything for this panel.
        self._full_widget = QtWidgets.QWidget()

        # Create Widgets

        # Set Widget Dimensions

        # Set Widget Tooltips

        # Set other Widget Attributes

        # Layout Widgets

        # Set DockWidget to be fully laid out widget.
        self.setWidget(self._full_widget)
        self.setFloating(False)


# noinspection PyArgumentList
class PlotEditorPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(PlotEditorPanel, self).__init__()
        self.setWindowTitle("Graph Editor")

        self._full_widget = QtWidgets.QWidget()

        self.save_button = QtWidgets.QPushButton('Save')
        self.check_uncertain = QtWidgets.QCheckBox()
        self.check_annotation = QtWidgets.QCheckBox()
        self.check_plot_lines = QtWidgets.QCheckBox()
        self.check_spline = QtWidgets.QCheckBox()
        self.check_autoscale_one = QtWidgets.QCheckBox()
        self.check_autoscale_two = QtWidgets.QCheckBox()
        self.slider_one = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_two = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.input_slider_one = QtWidgets.QLineEdit()
        self.input_slider_two = QtWidgets.QLineEdit()
        self.input_xmin_one = QtWidgets.QLineEdit()
        self.input_xmin_two = QtWidgets.QLineEdit()
        self.input_xmax_one = QtWidgets.QLineEdit()
        self.input_xmax_two = QtWidgets.QLineEdit()
        self.input_ymin_one = QtWidgets.QLineEdit()
        self.input_ymin_two = QtWidgets.QLineEdit()
        self.input_ymax_one = QtWidgets.QLineEdit()
        self.input_ymax_two = QtWidgets.QLineEdit()
        self._label_uncertain = QtWidgets.QLabel('Show Uncertainty')
        self._label_annotation = QtWidgets.QLabel('Show Annotations')
        self._label_plot_lines = QtWidgets.QLabel('Show Plot Lines')
        self._label_spline = QtWidgets.QLabel('FFT Spline')
        self._label_ymin_one = QtWidgets.QLabel("YMin")
        self._label_ymin_two = QtWidgets.QLabel("YMin")
        self._label_ymax_one = QtWidgets.QLabel("YMax")
        self._label_ymax_two = QtWidgets.QLabel("YMax")
        self._label_slider_one = QtWidgets.QLabel("Time Bins (ns)")
        self._label_slider_two = QtWidgets.QLabel("Time Bins (ns)")
        self._label_auto_one = QtWidgets.QLabel("Plot 1 -     Auto")
        self._label_auto_two = QtWidgets.QLabel("Plot 2 -     Auto")
        self._label_xmin_one = QtWidgets.QLabel("XMin (\u03BCs)")
        self._label_xmin_two = QtWidgets.QLabel("XMin (\u03BCs)")
        self._label_xmax_one = QtWidgets.QLabel("XMax (\u03BCs)")
        self._label_xmax_two = QtWidgets.QLabel("XMax (\u03BCs)")

        self._set_widget_attributes()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.setWidget(self._full_widget)

    def _set_widget_attributes(self):
        self.check_uncertain.setChecked(True)
        self.check_annotation.setChecked(True)
        self.check_spline.setChecked(False)
        self.check_autoscale_one.setChecked(True)
        self.check_autoscale_two.setChecked(True)

        self.input_xmin_one.setText("0")
        self.input_xmin_two.setText("0")
        self.input_xmax_one.setText("8")
        self.input_xmax_two.setText("0.5")
        self.input_ymin_one.setText("-0.3")
        self.input_ymin_two.setText("0.5")
        self.input_ymax_one.setText("-0.5")
        self.input_ymax_two.setText("0.5")
        self.input_ymax_one.setEnabled(False)
        self.input_ymax_two.setEnabled(False)
        self.input_ymin_one.setEnabled(False)
        self.input_ymin_two.setEnabled(False)

        self.slider_one.setMinimum(0)
        self.slider_one.setMaximum(500)
        self.slider_one.setValue(150)
        self.slider_one.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider_one.setTickInterval(20)
        self.slider_two.setMinimum(0)
        self.slider_two.setMaximum(500)
        self.slider_two.setValue(2)
        self.slider_two.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.slider_two.setTickInterval(20)

        self.input_slider_one.setText(str(self.slider_one.value()))
        self.input_slider_two.setText(str(self.slider_two.value()))

    def _set_widget_dimensions(self):
        self.input_slider_one.setFixedWidth(50)
        self.input_slider_two.setFixedWidth(50)
        self.input_xmin_one.setFixedWidth(50)
        self.input_xmax_one.setFixedWidth(50)
        self.input_xmin_two.setFixedWidth(50)
        self.input_xmax_two.setFixedWidth(50)
        self.input_ymin_one.setFixedWidth(50)
        self.input_ymin_two.setFixedWidth(50)
        self.input_ymax_one.setFixedWidth(50)
        self.input_ymax_two.setFixedWidth(50)

    def _set_widget_layout(self):
        row_one = QtWidgets.QHBoxLayout()
        row_two = QtWidgets.QHBoxLayout()

        row_one.addWidget(self._label_auto_one)
        row_one.addWidget(self.check_autoscale_one)
        row_one.addSpacing(10)
        row_one.addWidget(self._label_ymin_one)
        row_one.addWidget(self.input_ymin_one)
        row_one.addSpacing(10)
        row_one.addWidget(self._label_ymax_one)
        row_one.addWidget(self.input_ymax_one)
        row_one.addSpacing(10)
        row_one.addWidget(self._label_xmin_one)
        row_one.addWidget(self.input_xmin_one)
        row_one.addSpacing(10)
        row_one.addWidget(self._label_xmax_one)
        row_one.addWidget(self.input_xmax_one)
        row_one.addSpacing(10)
        row_one.addWidget(self._label_slider_one)
        row_one.addWidget(self.input_slider_one)
        row_one.addSpacing(10)
        row_one.addWidget(self.slider_one)

        row_two.addWidget(self._label_auto_two)
        row_two.addWidget(self.check_autoscale_two)
        row_two.addSpacing(10)
        row_two.addWidget(self._label_ymin_two)
        row_two.addWidget(self.input_ymin_two)
        row_two.addSpacing(10)
        row_two.addWidget(self._label_ymax_two)
        row_two.addWidget(self.input_ymax_two)
        row_two.addSpacing(10)
        row_two.addWidget(self._label_xmin_two)
        row_two.addWidget(self.input_xmin_two)
        row_two.addSpacing(10)
        row_two.addWidget(self._label_xmax_two)
        row_two.addWidget(self.input_xmax_two)
        row_two.addSpacing(10)
        row_two.addWidget(self._label_slider_two)
        row_two.addWidget(self.input_slider_two)
        row_two.addSpacing(10)
        row_two.addWidget(self.slider_two)

        col_one = QtWidgets.QVBoxLayout()
        col_one.addLayout(row_one)
        col_one.addLayout(row_two)

        col_two = QtWidgets.QVBoxLayout()

        row_unc = QtWidgets.QHBoxLayout()
        row_unc.addWidget(self.check_uncertain)
        row_unc.addWidget(self._label_uncertain)
        row_unc.setAlignment(QtCore.Qt.AlignLeft)
        row_ann = QtWidgets.QHBoxLayout()
        row_ann.addWidget(self.check_annotation)
        row_ann.addWidget(self._label_annotation)
        row_ann.setAlignment(QtCore.Qt.AlignLeft)
        row_lns = QtWidgets.QHBoxLayout()
        row_lns.addWidget(self.check_plot_lines)
        row_lns.addWidget(self._label_plot_lines)
        row_lns.setAlignment(QtCore.Qt.AlignLeft)
        row_spl = QtWidgets.QHBoxLayout()
        row_spl.addWidget(self.check_spline)
        row_spl.addWidget(self._label_spline)
        row_spl.setAlignment(QtCore.Qt.AlignLeft)

        col_two.addLayout(row_unc)
        col_two.addLayout(row_ann)
        col_two.addLayout(row_lns)
        col_two.addLayout(row_spl)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(col_one)
        main_layout.addLayout(col_two)
        main_layout.addSpacing(15)
        main_layout.addWidget(self.save_button)

        self._full_widget.setLayout(main_layout)


# noinspection PyArgumentList
class RunDisplayPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(RunDisplayPanel, self).__init__()
        self.setWindowTitle('Run Display')

        self._full_widget = QtWidgets.QWidget()

        self.color_choices = QtWidgets.QComboBox()
        self.marker_choices = QtWidgets.QComboBox()
        self.header_data = QtWidgets.QComboBox()
        self.histograms = QtWidgets.QComboBox()
        self.current_runs = QtWidgets.QListWidget()
        self.isolate_button = QtWidgets.QPushButton("Isolate")
        self.inspect_hist_button = QtWidgets.QPushButton("Inspect Hist")
        self.inspect_file_button = QtWidgets.QPushButton("Inspect File")
        self.plot_all_button = QtWidgets.QPushButton("Plot All Runs")
        self.output_current_file = QtWidgets.QLineEdit()
        self.output_header_display = QtWidgets.QLineEdit()
        self._label_header_data = QtWidgets.QLabel()
        self._label_histogram = QtWidgets.QLabel()
        self._label_display = QtWidgets.QLabel("Choose a currently plotted run below.\n")

        self._set_widget_attributes()
        self._set_widget_tooltips()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.setWidget(self._full_widget)

    def _set_widget_tooltips(self):
        self.output_header_display.setToolTip('Edits are not saved.')

    def _set_widget_attributes(self):
        self.isolate_button.setEnabled(False)
        self.header_data.setEnabled(False)
        self.output_header_display.setEnabled(False)
        self.inspect_hist_button.setEnabled(False)
        self.inspect_file_button.setEnabled(False)
        self.plot_all_button.setEnabled(False)
        self.output_current_file.setEnabled(False)

        self.color_choices.setEnabled(False)
        self.color_choices.addItems(["None", "blue", "red", "green", "orange", "purple",
                                     "brown", "yellow", "gray", "olive", "cyan", "pink", "custom"])

        self.marker_choices.setEnabled(False)
        self.marker_choices.addItems(['point', 'triangle_down', 'triangle_up', 'triangle_left',
                                      'triangle_right', 'octagon', 'square', 'pentagon', 'plus',
                                      'star', 'hexagon_1', 'hexagon_2', 'x', 'diamond',
                                      'thin_diamond'])

        self.histograms.setEnabled(False)
        self.histograms.addItem("None")

    def _set_widget_dimensions(self):
        self.color_choices.setFixedWidth(60)
        self.marker_choices.setFixedWidth(60)
        self.header_data.setFixedWidth(100)

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._label_display)
        main_layout.addWidget(self.output_current_file)

        row_one = QtWidgets.QHBoxLayout()
        row_one.addWidget(self.isolate_button)
        row_one.addWidget(self.color_choices)
        row_one.addWidget(self.marker_choices)
        row_two = QtWidgets.QHBoxLayout()
        row_two.addWidget(self.histograms)
        row_two.addWidget(self.inspect_hist_button)
        row_two.addWidget(self.inspect_file_button)
        row_thr = QtWidgets.QHBoxLayout()
        row_thr.addWidget(self.header_data)
        row_thr.addWidget(self.output_header_display)

        main_layout.addLayout(row_one)
        main_layout.addLayout(row_two)
        main_layout.addLayout(row_thr)
        main_layout.addWidget(self.current_runs)
        main_layout.addWidget(self.plot_all_button)

        main_layout.addStretch(1)
        self._full_widget.setLayout(main_layout)


# noinspection PyArgumentList
class PlotPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(PlotPanel, self).__init__()

        self.setWindowTitle("Graphing Area")
        self.full_widget = QtWidgets.QWidget()

        # self.canvas_one = RunPlot()
        # self.canvas_two = RunPlot()
        self.canvas_wrapper_one = CanvasWrapper()
        self.canvas_wrapper_two = CanvasWrapper()
        self.canvas_one = self.canvas_wrapper_one.canvas
        self.canvas_two = self.canvas_wrapper_two.canvas

        self.linestyle = 'None'

        hbox = QtWidgets.QHBoxLayout()
        # hbox.addWidget(self.canvas_one)
        # hbox.addWidget(self.canvas_two)
        hbox.addWidget(self.canvas_wrapper_one)
        hbox.addWidget(self.canvas_wrapper_two)
        self.full_widget.setLayout(hbox)

        self.setWidget(self.full_widget)


# noinspection PyArgumentList
class HistogramDisplay(QtWidgets.QMainWindow):
    def __init__(self, histogram=None):
        super(HistogramDisplay, self).__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        self.canvas = CanvasUI()
        layout.addWidget(self.canvas)
        self.addToolBar(NavigationToolbar(self.canvas, self))

        self.canvas.canvas_axes.plot(histogram, linestyle='None', marker='s')


# noinspection PyArgumentList
class CanvasUI(FigureCanvas):
    def __init__(self):
        self._draw_pending = False
        self._is_drawing = False
        FigureCanvas.__init__(self, Figure())

        self.canvas_axes = self.figure.add_subplot(111, label='Canvas')


# noinspection PyArgumentList
class CanvasWrapper(QtWidgets.QMainWindow):
    def __init__(self):
        super(CanvasWrapper, self).__init__()
        self.canvas = RunPlot()
        self.setCentralWidget(self.canvas)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, NavigationToolbar(self.canvas, self))

# noinspection PyArgumentList
class RunPlot(FigureCanvas):
    def __init__(self):
        # I get an error if I don't create these variables, True or False hasn't made a difference.
        self._draw_pending = True
        self._is_drawing = True

        FigureCanvas.__init__(self, Figure())
        axes = self.figure.subplots(2, 1)

        self.axes_time = axes[0]
        self.axes_freq = axes[1]

        self.set_blank()

    def set_blank(self):
        title_font_size = 12
        self.axes_time.spines['right'].set_visible(False)
        self.axes_time.spines['top'].set_visible(False)
        self.axes_time.spines['left'].set_visible(False)
        self.axes_time.spines['bottom'].set_visible(False)
        self.axes_time.set_xlabel("Add '.msr', '.dat' or '.asy' files and press 'Plot' to see data.",
                                  fontsize=title_font_size)
        self.axes_time.xaxis.label.set_color("#B8B8B8")
        # self.axes_time.set_ylabel("Asymmetry", fontsize=title_font_size)
        self.axes_time.tick_params(axis='x', colors='white')
        self.axes_time.tick_params(axis='y', colors='white')

        self.axes_freq.spines['right'].set_visible(False)
        self.axes_freq.spines['top'].set_visible(False)
        self.axes_freq.spines['left'].set_visible(False)
        self.axes_freq.spines['bottom'].set_visible(False)
        # self.axes_freq.set_xlabel("Frequency (MHz)", fontsize=title_font_size)
        # self.axes_freq.set_ylabel("Magnitude", fontsize=title_font_size)
        # self.axes_freq.legend(loc='upper right')
        self.axes_freq.tick_params(axis='x', colors='white')
        self.axes_freq.tick_params(axis='y', colors='white')

    def set_style(self):
        if style_imported:
            self.figure.set_facecolor('#32414B')
            self.axes_time.set_facecolor('#32414B')
            self.axes_freq.set_facecolor('#32414B')
            self.axes_time.spines['left'].set_color('white')
            self.axes_time.spines['bottom'].set_color('white')
            self.axes_time.xaxis.label.set_color('white')
            self.axes_time.yaxis.label.set_color('white')
            self.axes_time.tick_params(axis='x', colors='white')
            self.axes_time.tick_params(axis='y', colors='white')
            self.axes_freq.spines['left'].set_color('white')
            self.axes_freq.spines['bottom'].set_color('white')
            self.axes_freq.xaxis.label.set_color('white')
            self.axes_freq.yaxis.label.set_color('white')
            self.axes_freq.tick_params(axis='x', colors='white')
            self.axes_freq.tick_params(axis='y', colors='white')
        else:
            self.axes_time.tick_params(axis='x', colors='black')
            self.axes_time.tick_params(axis='y', colors='black')
            self.axes_freq.tick_params(axis='x', colors='black')
            self.axes_freq.tick_params(axis='y', colors='black')

        title_font_size = 12
        self.axes_time.spines['right'].set_visible(False)
        self.axes_time.spines['top'].set_visible(False)
        self.axes_time.spines['left'].set_visible(True)
        self.axes_time.spines['bottom'].set_visible(True)
        self.axes_time.set_xlabel("Time (" + chr(956) + "s)", fontsize=title_font_size)
        self.axes_time.set_ylabel("Asymmetry", fontsize=title_font_size)

        self.axes_freq.spines['right'].set_visible(False)
        self.axes_freq.spines['top'].set_visible(False)
        self.axes_freq.spines['left'].set_visible(True)
        self.axes_freq.spines['bottom'].set_visible(True)
        self.axes_freq.set_xlabel("Frequency (MHz)", fontsize=title_font_size)
        self.axes_freq.set_ylabel("Magnitude", fontsize=title_font_size)
        self.axes_freq.legend(loc='upper right') # fixme, move this line to the update canvas in controller


# noinspection PyArgumentList
class FileFormatterUI(QtWidgets.QDialog):
    def __init__(self):
        super(FileFormatterUI, self).__init__()
        self.column_data = QtWidgets.QTableWidget()
        self.data = None
        self.column_data.setRowCount(10)
        self.column_data.setColumnCount(8)
        self.set_data(self.column_data)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.column_data)
        self.setLayout(layout)

        self.exec_()

    def populate_table(self):
        pass

    def set_data(self, table):
        horizontal_headers = []
        for n, key in enumerate(sorted(self.data.keys())):
            horizontal_headers.append(key)
            for m, item in enumerate(self.data[key]):
                new_item = QtWidgets.QTableWidgetItem(item)
                table.setItem(m, n, new_item)
        table.setHorizontalHeaderLabels(horizontal_headers)


# noinspection PyArgumentList
class FileDisplayUI(QtWidgets.QPlainTextEdit):
    def __init__(self, filename=None):
        super(FileDisplayUI, self).__init__()
        if filename:
            self.filename = filename
            self.setGeometry(500, 300, 400, 400)
            self.setPlainText(open(self.filename).read())
            self.setWordWrapMode(False)


# noinspection PyArgumentList
class WriteDataUI(QtWidgets.QDialog):
    def __init__(self):
        super(WriteDataUI, self).__init__()
        self.setWindowTitle('Specify options for writing data')

        self.file_list = QtWidgets.QComboBox()
        self.select_folder = QtWidgets.QPushButton('Custom')
        self.skip_file = QtWidgets.QPushButton('Skip File')
        self.write_file = QtWidgets.QPushButton('Write')
        self.write_all = QtWidgets.QPushButton('Write All')
        self.done = QtWidgets.QPushButton('Done')
        self.input_filename = QtWidgets.QLineEdit()
        self.input_filename.setPlaceholderText('Default is [run number].asy')
        self.label_full = QtWidgets.QLabel('Full Data')
        self.label_binned = QtWidgets.QLabel('Binned Data')
        self.label_fft = QtWidgets.QLabel('FFT')
        self.radio_binned = QtWidgets.QRadioButton()
        self.radio_full = QtWidgets.QRadioButton()
        self.radio_fft = QtWidgets.QRadioButton()

        self._set_widget_attributes()
        self._set_widget_tooltips()
        self._set_widget_dimensions()
        self._set_widget_layout()

    def _set_widget_attributes(self):
        self.radio_binned.setChecked(True)

    def _set_widget_tooltips(self):
        pass

    def _set_widget_dimensions(self):
        pass

    def _set_widget_layout(self):
        col_one = QtWidgets.QVBoxLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_two = QtWidgets.QHBoxLayout()
        row_thr = QtWidgets.QHBoxLayout()

        col_one.addWidget(self.file_list)

        row_one.addWidget(self.select_folder)
        row_one.addWidget(self.input_filename)
        col_one.addLayout(row_one)

        col_one.addSpacing(15)
        row_two.addWidget(self.label_binned)
        row_two.addWidget(self.radio_binned)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_full)
        row_two.addWidget(self.radio_full)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_fft)
        row_two.addWidget(self.radio_fft)
        row_two.addSpacing(10)
        row_two.setAlignment(QtCore.Qt.AlignLeft)
        col_one.addLayout(row_two)
        col_one.addSpacing(15)

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


# noinspection PyArgumentList
class SavePlotUI(QtWidgets.QDialog):
    def __init__(self):
        super(SavePlotUI, self).__init__()
        self.setWindowTitle('Specify plot to save')

        self.message = QtWidgets.QLabel('Would you like to save the left-side or right-side plots?')
        self.left_radio = QtWidgets.QRadioButton()
        self.right_radio = QtWidgets.QRadioButton()
        self.save_button = QtWidgets.QPushButton('Save As')
        self.left_label = QtWidgets.QLabel('Left')
        self.right_label = QtWidgets.QLabel('Right')

        main_layout = QtWidgets.QVBoxLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_one.addSpacing(35)
        row_one.addWidget(self.message)
        row_one.setAlignment(self.message, QtCore.Qt.AlignCenter)
        row_one.addSpacing(35)
        row_two = QtWidgets.QHBoxLayout()
        row_two.addStretch()
        row_two.addWidget(self.left_label)
        row_two.addWidget(self.left_radio)
        row_two.addSpacing(15)
        row_two.addWidget(self.right_label)
        row_two.addWidget(self.right_radio)
        row_two.addSpacing(25)
        row_two.addWidget(self.save_button)
        row_two.addStretch()
        main_layout.addLayout(row_one)
        main_layout.addSpacing(5)
        main_layout.addLayout(row_two)

        self.setLayout(main_layout)


# noinspection PyArgumentList
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


# noinspection PyArgumentList
class ErrorMessageUI(QtWidgets.QDialog):
    def __init__(self, error_message=None, pos_function=None):
        super(ErrorMessageUI, self).__init__()
        self.setWindowTitle('Error')
        message = QtWidgets.QLabel(error_message)
        pos_button = QtWidgets.QPushButton('Okay')
        self.setMinimumWidth(300)
        self.setMinimumHeight(80)
        pos_button.setFixedWidth(80)

        if pos_function:
            pos_button.released.connect(lambda: pos_function())

        pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()

        col.addWidget(message)
        col.addWidget(pos_button)
        col.setAlignment(message, QtCore.Qt.AlignCenter)
        col.setAlignment(pos_button, QtCore.Qt.AlignCenter)
        self.setLayout(col)

        self.exec_()


# noinspection PyArgumentList
class PermissionsMessageUI(QtWidgets.QDialog):
    def __init__(self, permissions_message=None, pos_function=None, neg_function=None):
        super(PermissionsMessageUI, self).__init__()
        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel(permissions_message)
        self.pos_button = QtWidgets.QPushButton('Okay')
        self.neg_button = QtWidgets.QPushButton('Cancel')
        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(80)
        self.neg_button.setFixedWidth(80)

        if pos_function:
            self.pos_button.released.connect(lambda: pos_function())

        if neg_function:
            self.neg_button.released.connect(lambda: neg_function())

        self.neg_button.released.connect(lambda: self.close())
        self.pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)
        col.setAlignment(message, QtCore.Qt.AlignCenter)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        row.setAlignment(self.pos_button, QtCore.Qt.AlignRight)
        row.setAlignment(self.neg_button, QtCore.Qt.AlignLeft)
        col.addLayout(row)
        self.setLayout(col)

        self.exec_()
