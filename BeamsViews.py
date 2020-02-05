# View for BEAMS Application

# Standard Library Modules
import socket
import logging

# Installed modules
from PyQt5 import QtWidgets, QtGui, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure


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

        self.run_display = RunDisplayPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.run_display)

        self.plot_editor = PlotEditorPanel()
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.plot_editor)

        self.mufyt_panel = MuFytPanel()
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.mufyt_panel)

        self.plot_panel = PlotPanel()
        self.setCentralWidget(self.plot_panel)

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

    def set_status_message(self, message):
        self.setStatusTip(message)


# noinspection PyArgumentList
class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(FileManagerPanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setWindowTitle("File Manager")

        # Create our widget which will hold everything for this panel.
        self._full_widget = QtWidgets.QWidget()

        # Create Widgets
        self.file_list = QtWidgets.QListWidget()
        self.select_all = QtWidgets.QCheckBox()
        self.write_button = StyleOneButton("Write")
        self.import_button = StyleTwoButton("+")
        self.remove_button = StyleTwoButton('-')
        self.plot_button = StyleOneButton("Plot")
        self.convert_button = StyleOneButton("Convert")

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
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setWindowTitle("Graph Options")

        self._full_widget = QtWidgets.QWidget()

        self.check_uncertain = QtWidgets.QCheckBox()
        self.check_annotation = QtWidgets.QCheckBox()
        self.check_plot_lines = QtWidgets.QCheckBox()

        self._label_uncertain = QtWidgets.QLabel('Show Uncertainty')
        self._label_annotation = QtWidgets.QLabel('Show Annotations')
        self._label_plot_lines = QtWidgets.QLabel('Show Plot Lines')

        self._set_widget_attributes()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.setWidget(self._full_widget)

    def _set_widget_attributes(self):
        self.check_uncertain.setChecked(True)
        self.check_annotation.setChecked(True)

    def _set_widget_dimensions(self):
        pass

    def _set_widget_layout(self):
        col_two = QtWidgets.QVBoxLayout()

        row_unc = QtWidgets.QHBoxLayout()
        row_unc.addWidget(self.check_uncertain)
        row_unc.addWidget(self._label_uncertain)
        row_unc.setAlignment(QtCore.Qt.AlignLeft)
        row_ann = QtWidgets.QHBoxLayout()
        row_ann.addWidget(self.check_annotation)
        row_ann.addWidget(self._label_annotation)
        row_ann.setAlignment(QtCore.Qt.AlignLeft)

        col_thr = QtWidgets.QVBoxLayout()

        row_lns = QtWidgets.QHBoxLayout()
        row_lns.addWidget(self.check_plot_lines)
        row_lns.addWidget(self._label_plot_lines)
        row_lns.setAlignment(QtCore.Qt.AlignLeft)

        col_two.addLayout(row_unc)
        col_two.addLayout(row_ann)
        col_thr.addLayout(row_lns)

        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(col_two)
        main_layout.addLayout(col_thr)
        main_layout.addSpacing(15)

        self._full_widget.setLayout(main_layout)


# noinspection PyArgumentList
class RunDisplayPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(RunDisplayPanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setWindowTitle('Run Display')

        self._full_widget = QtWidgets.QWidget()

        self.color_choices = QtWidgets.QComboBox()
        self.marker_choices = QtWidgets.QComboBox()
        self.header_data = QtWidgets.QComboBox()
        self.histograms = QtWidgets.QComboBox()
        self.current_runs = QtWidgets.QListWidget()
        self.isolate_button = StyleOneButton("Isolate")
        self.inspect_hist_button = StyleTwoButton("See Hist")
        self.inspect_file_button = StyleTwoButton("See File")
        self.correction_button = StyleTwoButton("Apply Correction")
        self.integrate_button = StyleTwoButton("Integrate")
        self.plot_all_button = StyleOneButton("Plot All Runs")
        self.clear_all_button = StyleOneButton("Clear All Runs")

        self.integrate_button = StyleTwoButton("Integrate")
        self.integrate_choices = QtWidgets.QComboBox()
        self.input_integrate_time = QtWidgets.QLineEdit()

        self.output_current_file = QtWidgets.QLineEdit()
        self.output_header_display = QtWidgets.QLineEdit()
        self.input_alpha = QtWidgets.QLineEdit()
        self._label_alpha = QtWidgets.QLabel("α = ")
        self._label_header_data = QtWidgets.QLabel()
        self._label_histogram = QtWidgets.QLabel()
        self._label_display = QtWidgets.QLabel("Plot a file to interact with data below\n")

        self._set_widget_attributes()
        self._set_widget_tooltips()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.setWidget(self._full_widget)

    def set_color_options(self):
        self.color_choices.clear()
        self.color_choices.addItems(["Blue", "Red", "Purple", "Green", "Orange", "Maroon", "Pink", "Dark Blue",
                                     "Dark Green", "Light Blue", "Light Purple", "Dark Orange", "Yellow", "Light Red",
                                     "Light Green"])

    def set_marker_options(self):
        self.marker_choices.clear()
        self.marker_choices.addItems(['point', 'triangle_down', 'triangle_up', 'triangle_left',
                                      'triangle_right', 'octagon', 'square', 'pentagon', 'plus',
                                      'star', 'hexagon_1', 'hexagon_2', 'x', 'diamond',
                                      'thin_diamond'])

    def set_enabled(self, enabled):
        self.marker_choices.setEnabled(enabled)
        self.color_choices.setEnabled(enabled)
        self.isolate_button.setEnabled(enabled)
        self.histograms.setEnabled(enabled)
        self.inspect_hist_button.setEnabled(enabled)
        self.inspect_file_button.setEnabled(enabled)
        self.plot_all_button.setEnabled(enabled)
        self.clear_all_button.setEnabled(enabled)
        self.header_data.setEnabled(enabled)
        self.output_header_display.setEnabled(enabled)
        self.correction_button.setEnabled(enabled)
        self.input_alpha.setEnabled(enabled)
        self.integrate_choices.setEnabled(enabled)
        self.integrate_button.setEnabled(enabled)

    def clear_panel(self):
        self.header_data.clear()
        self.current_runs.clear()
        self.histograms.clear()
        self.output_current_file.clear()
        self.output_header_display.clear()
        self.input_alpha.clear()
        self.color_choices.clear()
        self.marker_choices.clear()

    def _set_widget_tooltips(self):
        self.output_header_display.setToolTip('Edits are not saved.')

    def _set_widget_attributes(self):
        self.set_enabled(False)
        self.integrate_choices.addItems(['Temp', 'Field'])
        self.current_runs.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def _set_widget_dimensions(self):
        self.color_choices.setFixedWidth(60)
        self.marker_choices.setFixedWidth(60)
        self.header_data.setFixedWidth(100)
        self.inspect_hist_button.setFixedWidth(70)
        self.inspect_file_button.setFixedWidth(70)
        self.isolate_button.setFixedWidth(70)
        self.correction_button.setFixedWidth(120)
        self.integrate_button.setFixedWidth(120)

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._label_display)
        main_layout.addWidget(self.output_current_file)

        row_one = QtWidgets.QHBoxLayout()
        row_one.addWidget(self.isolate_button)
        row_one.addWidget(self.color_choices)
        row_one.addWidget(self.marker_choices)
        row_two = QtWidgets.QHBoxLayout()
        row_two.addWidget(self.inspect_hist_button)
        row_two.addWidget(self.histograms)
        row_thr = QtWidgets.QHBoxLayout()
        row_thr.addWidget(self.inspect_file_button)
        row_thr.addWidget(self.header_data)
        row_thr.addWidget(self.output_header_display)
        row_four = QtWidgets.QHBoxLayout()
        row_four.addWidget(self.correction_button)
        row_four.addSpacing(15)
        row_four.addWidget(self._label_alpha)
        row_four.addWidget(self.input_alpha)
        row_five = QtWidgets.QHBoxLayout()
        row_five.addWidget(self.integrate_button)
        row_five.addWidget(self.integrate_choices)
        # row_five.addWidget(self.input_integrate_time)

        main_layout.addLayout(row_one)
        main_layout.addLayout(row_two)
        main_layout.addLayout(row_thr)

        main_layout.addWidget(self.current_runs)
        main_layout.addLayout(row_four)
        main_layout.addLayout(row_five)

        row_six = QtWidgets.QHBoxLayout()
        row_six.addWidget(self.plot_all_button)
        row_six.addWidget(self.clear_all_button)
        main_layout.addLayout(row_six)

        # main_layout.addStretch(1)
        self._full_widget.setLayout(main_layout)


# noinspection PyArgumentList
class PlotPanel(QtWidgets.QDockWidget):
    # noinspection PyArgumentList
    class CanvasWrapper(QtWidgets.QMainWindow):
        def __init__(self):
            QtWidgets.QMainWindow.__init__(self)
            self.canvas = RunPlot()
            self.setCentralWidget(self.canvas)
            self.addToolBar(QtCore.Qt.TopToolBarArea, NavigationToolbar(self.canvas, self))
            self.plot_editor = SinglePlotEditor()
            self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.plot_editor)

    def __init__(self):
        super(PlotPanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())

        self.setWindowTitle("Graphing Area")
        self.full_widget = QtWidgets.QWidget()

        self.canvas_wrapper_one = self.CanvasWrapper()
        self.canvas_wrapper_two = self.CanvasWrapper()
        self.canvas_wrapper_one.plot_editor.setWindowTitle('Plot 1 Editor')
        self.canvas_wrapper_two.plot_editor.setWindowTitle('Plot 2 Editor')
        self.canvas_one = self.canvas_wrapper_one.canvas
        self.canvas_two = self.canvas_wrapper_two.canvas
        self.editor_one = self.canvas_wrapper_one.plot_editor
        self.editor_two = self.canvas_wrapper_two.plot_editor

        self.linestyle = 'None'

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.canvas_wrapper_one)
        hbox.addWidget(self.canvas_wrapper_two)
        self.full_widget.setLayout(hbox)

        self.setWidget(self.full_widget)

        self.slider_one = self.editor_one.slider_bin
        self.slider_two = self.editor_two.slider_bin
        self.input_slider_one = self.editor_one.input_bin
        self.input_slider_two = self.editor_two.input_bin

        self.input_time_xmin_one = self.editor_one.input_time_xmin
        self.input_time_xmin_two = self.editor_two.input_time_xmin
        self.input_time_xmax_one = self.editor_one.input_time_xmax
        self.input_time_xmax_two = self.editor_two.input_time_xmax
        self.input_time_ymin_one = self.editor_one.input_time_ymin
        self.input_time_ymin_two = self.editor_two.input_time_ymin
        self.input_time_ymax_one = self.editor_one.input_time_ymax
        self.input_time_ymax_two = self.editor_two.input_time_ymax

        self.input_freq_xmin_one = self.editor_one.input_freq_xmin
        self.input_freq_xmin_two = self.editor_two.input_freq_xmin
        self.input_freq_xmax_one = self.editor_one.input_freq_xmax
        self.input_freq_xmax_two = self.editor_two.input_freq_xmax

        self.input_freq_ymin_one = self.editor_one.input_freq_ymin
        self.input_freq_ymin_two = self.editor_two.input_freq_ymin
        self.input_freq_ymax_one = self.editor_one.input_freq_ymax
        self.input_freq_ymax_two = self.editor_two.input_freq_ymax

        self.check_time_y_autoscale_one = self.editor_one.check_time_yauto
        self.check_time_y_autoscale_two = self.editor_two.check_time_yauto
        self.check_freq_y_autoscale_one = self.editor_one.check_freq_yauto
        self.check_freq_y_autoscale_two = self.editor_two.check_freq_yauto
        self.check_freq_x_autoscale_one = self.editor_one.check_freq_xauto
        self.check_freq_x_autoscale_two = self.editor_two.check_freq_xauto

        self._set_widget_attributes()

    def _set_widget_attributes(self):
        self.input_time_xmin_one.setText("0")
        self.input_time_xmin_two.setText("0")
        self.input_time_xmax_one.setText("8")
        self.input_time_xmax_two.setText("0.5")
        self.input_time_ymin_one.setText("-0.3")
        self.input_time_ymin_two.setText("0.5")
        self.input_time_ymax_one.setText("-0.5")
        self.input_time_ymax_two.setText("0.5")

        self.input_time_ymin_one.setEnabled(False)
        self.input_time_ymin_two.setEnabled(False)
        self.input_time_ymax_one.setEnabled(False)
        self.input_time_ymax_two.setEnabled(False)

        self.input_freq_xmin_one.setEnabled(False)
        self.input_freq_xmin_two.setEnabled(False)
        self.input_freq_xmax_one.setEnabled(False)
        self.input_freq_xmax_two.setEnabled(False)

        self.input_freq_ymin_one.setEnabled(False)
        self.input_freq_ymin_two.setEnabled(False)
        self.input_freq_ymax_one.setEnabled(False)
        self.input_freq_ymax_two.setEnabled(False)

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
class SinglePlotEditor(QtWidgets.QDockWidget):
    def __init__(self):
        super(SinglePlotEditor, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())

        self._full_widget = QtWidgets.QWidget()

        self._label_slider_bin = QtWidgets.QLabel('')
        self._label_input_bin = QtWidgets.QLabel('Time Bins (ns)')

        self.slider_bin = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.input_bin = QtWidgets.QLineEdit()

        self._label_time = QtWidgets.QLabel('Time')
        self._label_time_xmin = QtWidgets.QLabel('XMin (\u03BCs)')
        self._label_time_xmax = QtWidgets.QLabel('XMax (\u03BCs)')
        self._label_time_ymin = QtWidgets.QLabel('YMin')
        self._label_time_ymax = QtWidgets.QLabel('YMax')
        self._label_time_yauto = QtWidgets.QLabel('Auto Y')

        self.input_time_xmin = QtWidgets.QLineEdit()
        self.input_time_xmax = QtWidgets.QLineEdit()
        self.input_time_ymin = QtWidgets.QLineEdit()
        self.input_time_ymax = QtWidgets.QLineEdit()
        self.check_time_yauto = QtWidgets.QCheckBox()

        self._label_freq = QtWidgets.QLabel('Frequency')
        self._label_freq_xmin = QtWidgets.QLabel('XMin (MHz)')
        self._label_freq_xmax = QtWidgets.QLabel('XMax (MHz)')
        self._label_freq_ymin = QtWidgets.QLabel('YMin')
        self._label_freq_ymax = QtWidgets.QLabel('YMax')
        self._label_freq_yauto = QtWidgets.QLabel('Auto Y')
        self._label_freq_xauto = QtWidgets.QLabel('Auto X')

        self.input_freq_xmin = QtWidgets.QLineEdit()
        self.input_freq_xmax = QtWidgets.QLineEdit()
        self.input_freq_ymin = QtWidgets.QLineEdit()
        self.input_freq_ymax = QtWidgets.QLineEdit()
        self.check_freq_yauto = QtWidgets.QCheckBox()
        self.check_freq_xauto = QtWidgets.QCheckBox()

        self._set_widget_attributes()
        self._set_widget_tooltips()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.setWidget(self._full_widget)

    def _set_widget_attributes(self):
        self.check_freq_xauto.setChecked(True)
        self.check_freq_yauto.setChecked(True)
        self.check_time_yauto.setChecked(True)

    def _set_widget_tooltips(self):
        pass

    def _set_widget_dimensions(self):
        self.input_time_xmin.setFixedWidth(50)
        self.input_time_xmax.setFixedWidth(50)
        self.input_time_ymin.setFixedWidth(50)
        self.input_time_ymax.setFixedWidth(50)
        self.input_freq_xmin.setFixedWidth(50)
        self.input_freq_xmax.setFixedWidth(50)
        self.input_freq_ymin.setFixedWidth(50)
        self.input_freq_ymax.setFixedWidth(50)
        self.input_bin.setFixedWidth(50)

    def _set_widget_layout(self):
        spacing = 10
        main_layout = QtWidgets.QVBoxLayout()

        row_1 = QtWidgets.QHBoxLayout()
        row_1.addWidget(self._label_input_bin)
        row_1.addWidget(self.input_bin)
        row_1.addWidget(self.slider_bin)

        main_layout.addLayout(row_1)

        time_form = QtWidgets.QGroupBox('Time')
        time_layout = QtWidgets.QFormLayout()

        row_time_1 = QtWidgets.QHBoxLayout()
        row_time_1.addSpacing(65)
        row_time_1.addSpacing(spacing)
        row_time_1.addWidget(self._label_time_xmin)
        row_time_1.addWidget(self.input_time_xmin)
        row_time_1.addSpacing(spacing)
        row_time_1.addWidget(self._label_time_xmax)
        row_time_1.addWidget(self.input_time_xmax)
        row_time_1.addStretch()
        time_layout.addRow(row_time_1)

        row_time_2 = QtWidgets.QHBoxLayout()
        row_time_2.addWidget(self._label_time_yauto)
        row_time_2.addWidget(self.check_time_yauto)
        row_time_2.addSpacing(24)
        row_time_2.addSpacing(spacing)
        row_time_2.addWidget(self._label_time_ymin)
        row_time_2.addWidget(self.input_time_ymin)
        row_time_2.addSpacing(23)
        row_time_2.addSpacing(spacing)
        row_time_2.addWidget(self._label_time_ymax)
        row_time_2.addWidget(self.input_time_ymax)
        row_time_2.addStretch()
        time_layout.addRow(row_time_2)
        time_form.setLayout(time_layout)

        freq_form = QtWidgets.QGroupBox('Frequency')
        freq_layout = QtWidgets.QFormLayout()

        row_freq_1 = QtWidgets.QHBoxLayout()
        row_freq_1.addWidget(self._label_freq_xauto)
        row_freq_1.addWidget(self.check_freq_xauto)
        row_freq_1.addSpacing(10)
        row_freq_1.addSpacing(spacing)
        row_freq_1.addWidget(self._label_freq_xmin)
        row_freq_1.addWidget(self.input_freq_xmin)
        row_freq_1.addSpacing(spacing)
        row_freq_1.addWidget(self._label_freq_xmax)
        row_freq_1.addWidget(self.input_freq_xmax)
        row_freq_1.addStretch()
        freq_layout.addRow(row_freq_1)

        row_freq_2 = QtWidgets.QHBoxLayout()
        row_freq_2.addWidget(self._label_freq_yauto)
        row_freq_2.addWidget(self.check_freq_yauto)
        row_freq_2.addSpacing(42)
        row_freq_2.addSpacing(spacing)
        row_freq_2.addWidget(self._label_freq_ymin)
        row_freq_2.addWidget(self.input_freq_ymin)
        row_freq_2.addSpacing(31)
        row_freq_2.addSpacing(spacing)
        row_freq_2.addWidget(self._label_freq_ymax)
        row_freq_2.addWidget(self.input_freq_ymax)
        row_freq_2.addStretch()
        freq_layout.addRow(row_freq_2)
        freq_form.setLayout(freq_layout)

        editor_layout = QtWidgets.QHBoxLayout()
        editor_layout.addWidget(time_form)
        editor_layout.addWidget(freq_form)

        main_layout.addLayout(editor_layout)

        self._full_widget.setLayout(main_layout)


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

    def set_style(self, moving):
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
        self.axes_freq.set_xlabel(r'Frequency (MHz)', fontsize=title_font_size)
        self.axes_freq.set_ylabel(r'FFT$^2$', fontsize=title_font_size)
        self.axes_freq.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
        if not moving:
            self.axes_freq.legend(loc='upper right')


# noinspection PyArgumentList
class IntegrationDisplay(QtWidgets.QMainWindow):
    def __init__(self, integration, x_axis, x_axis_data):
        super(IntegrationDisplay, self).__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)

        self.canvas = CanvasUI()
        layout.addWidget(self.canvas)
        self.addToolBar(NavigationToolbar(self.canvas, self))

        self.canvas.canvas_axes.plot(x_axis_data, integration, linestyle='None', marker='o')
        self.canvas.canvas_axes.set_xlabel(x_axis)
        self.canvas.canvas_axes.set_ylabel("Integrated Asymmetry")


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

        self.status_bar = QtWidgets.QStatusBar()
        self.file_list = QtWidgets.QComboBox()
        self.select_folder = StyleTwoButton('Custom')
        self.skip_file = StyleOneButton('Skip File')
        self.write_file = StyleOneButton('Write')
        self.write_all = StyleOneButton('Write All')
        self.done = StyleOneButton('Done')
        self.input_filename = QtWidgets.QLineEdit()
        self.input_filename.setPlaceholderText('Default is [run number].asy')
        self.label_full = QtWidgets.QLabel('Full Data')
        self.label_binned = QtWidgets.QLabel('Binned Data')
        self.label_binned_size = QtWidgets.QLabel('Bin Size')
        self.label_fft = QtWidgets.QLabel('FFT')
        self.radio_binned = QtWidgets.QRadioButton()
        self.radio_binned_size = QtWidgets.QLineEdit()
        self.radio_full = QtWidgets.QRadioButton()
        self.radio_fft = QtWidgets.QRadioButton()

        self._set_widget_attributes()
        self._set_widget_tooltips()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.set_status_message('Ready.')

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def set_enabled(self, binned):
        if binned:
            self.radio_binned_size.setEnabled(True)
            self.write_file.setEnabled(False)
            self.write_all.setEnabled(False)
        else:
            self.radio_binned_size.setEnabled(False)
            self.write_file.setEnabled(True)
            self.write_all.setEnabled(True)

    def _set_widget_attributes(self):
        self.radio_full.setChecked(True)
        self.radio_binned_size.setEnabled(False)

    def _set_widget_tooltips(self):
        pass

    def _set_widget_dimensions(self):
        self.select_folder.setFixedWidth(80)
        self.skip_file.setFixedWidth(80)
        self.write_file.setFixedWidth(80)
        self.write_all.setFixedWidth(80)
        self.done.setFixedWidth(80)
        self.radio_binned_size.setFixedWidth(60)

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
        row_two.addStretch()
        row_two.addWidget(self.label_binned)
        row_two.addWidget(self.radio_binned)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_binned_size)
        row_two.addWidget(self.radio_binned_size)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_full)
        row_two.addWidget(self.radio_full)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_fft)
        row_two.addWidget(self.radio_fft)
        row_two.addSpacing(10)
        row_two.setAlignment(QtCore.Qt.AlignLeft)
        row_two.addStretch()
        col_one.addLayout(row_two)
        col_one.addSpacing(15)

        row_thr.addStretch()
        row_thr.addWidget(self.skip_file)
        row_thr.addSpacing(5)
        row_thr.addWidget(self.write_file)
        row_thr.addSpacing(5)
        row_thr.addWidget(self.write_all)
        row_thr.addWidget(self.done)
        row_thr.addStretch()
        row_thr.setAlignment(QtCore.Qt.AlignLeft)
        col_one.addLayout(row_thr)

        col_one.addWidget(self.status_bar)

        self.setLayout(col_one)


# noinspection PyArgumentList
class PlotDataUI(QtWidgets.QDialog):
    def __init__(self):
        super(PlotDataUI, self).__init__()
        self.t_tip = QtWidgets.QLabel('Specify the two histograms you want to use calculate the asymmetry.')
        self.c_file_list = QtWidgets.QComboBox()
        self.c_hist_one = QtWidgets.QComboBox()
        self.c_hist_two = QtWidgets.QComboBox()
        self.b_apply = StyleOneButton('Apply')
        self.b_apply_all = StyleOneButton('Apply All')
        self.b_plot = StyleOneButton('Plot')
        self.b_skip = StyleOneButton('Skip')
        self.b_cancel = StyleTwoButton('Cancel')
        self.status_bar = QtWidgets.QStatusBar()

        self.b_plot.setEnabled(False)

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
        col.addWidget(self.status_bar)

        self.setLayout(col)

    def set_status_message(self, message):
        self.status_bar.showMessage(message)


# noinspection PyArgumentList
class ErrorMessageUI(QtWidgets.QDialog):
    def __init__(self, error_message=None, pos_function=None):
        super(ErrorMessageUI, self).__init__()
        self.setWindowTitle('Error')
        message = QtWidgets.QLabel(error_message)
        pos_button = StyleOneButton('Okay')
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
        self.pos_button = StyleOneButton('Okay')
        self.neg_button = StyleTwoButton('Cancel')
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


# noinspection PyArgumentList
class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    NavigationToolbar2QT.toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        # (None, None, None, None),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        # ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
        # (None, None, None, None),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    )


# noinspection PyArgumentList
class WebDownloadUI(QtWidgets.QDialog):
    def __init__(self):
        super(WebDownloadUI, self).__init__()

        self.status_bar = QtWidgets.QStatusBar()
        self.input_area = QtWidgets.QLineEdit()
        self.input_year = QtWidgets.QLineEdit()
        self.input_runs = QtWidgets.QLineEdit()
        self.input_file = QtWidgets.QLineEdit()
        self.input_expt = QtWidgets.QLineEdit()
        self.output_web = QtWidgets.QPlainTextEdit()
        self.select_button = StyleTwoButton('Save to')
        self.download_button = StyleOneButton('Download')
        self.search_button = StyleOneButton('Search')
        self.done_button = StyleOneButton('Done')
        self._label_description = QtWidgets.QLabel('Provide the information below to search and/or download runs from '
                                                   'musr.ca.\n * indicates required for download. You can search'
                                                   ' based on incomplete info.')

        self._set_widget_dimensions()
        self._set_widget_attributes()
        self._set_widget_layout()

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def _set_widget_dimensions(self):
        self.input_area.setFixedWidth(70)
        self.input_expt.setFixedWidth(70)
        self.input_year.setFixedWidth(70)
        self.select_button.setFixedWidth(80)
        self.download_button.setFixedWidth(80)
        self.done_button.setFixedWidth(80)
        self.search_button.setFixedWidth(80)
        self.output_web.setFixedHeight(150)
        self.setFixedWidth(400)

    def _set_widget_attributes(self):
        self.input_area.setPlaceholderText('*Area')
        self.input_year.setPlaceholderText('*Year (YYYY)')
        self.input_runs.setPlaceholderText('*Range of Runs (N-N)')
        self.input_file.setPlaceholderText('Save Directory (default is current)')
        self.input_expt.setPlaceholderText('Expt #')

        self.output_web.setEnabled(True)
        self.output_web.appendPlainText('No queries or downloads attempted.\n')

        self.set_status_message('Ready.')

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._label_description)
        main_layout.addSpacing(5)

        row_1 = QtWidgets.QHBoxLayout()
        row_1.addWidget(self.input_expt)
        row_1.addWidget(self.input_year)
        row_1.addWidget(self.input_area)
        row_1.addWidget(self.input_runs)
        main_layout.addLayout(row_1)

        row_2 = QtWidgets.QHBoxLayout()
        row_2.addWidget(self.select_button)
        row_2.addWidget(self.input_file)
        main_layout.addLayout(row_2)
        main_layout.addSpacing(10)

        row_3 = QtWidgets.QHBoxLayout()
        row_3.addStretch()
        row_3.addWidget(self.search_button)
        row_3.addSpacing(10)
        row_3.addWidget(self.download_button)
        row_3.addSpacing(10)
        row_3.addWidget(self.done_button)
        row_3.addStretch()
        main_layout.addLayout(row_3)
        main_layout.addSpacing(10)

        row_4 = QtWidgets.QHBoxLayout()
        row_4.addWidget(self.output_web)
        main_layout.addLayout(row_4)
        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)


# noinspection PyArgumentList
class AddFileUI(QtWidgets.QDialog):
    def __init__(self, file_manager, web_manager):
        super(AddFileUI, self).__init__()
        self.file_manager = file_manager
        self.web_manager = web_manager

        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel('Would you like to add files from the local file system or online.')
        self.pos_button = StyleOneButton('From disk')
        self.neg_button = StyleOneButton('From musr.ca')
        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(100)
        self.neg_button.setFixedWidth(100)

        self.pos_button.released.connect(lambda: self._set_type(True))
        self.neg_button.released.connect(lambda: self._set_type(False))

        try:
            socket.create_connection(("www.google.com", 80))
        except OSError:
            self.neg_button.setEnabled(False)

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

    def _set_type(self, x=False):
        self.close()
        if x:
            self.file_manager.add_file_from_disk()
        else:
            self.web_manager()


# noinspection PyArgumentList
class StyleFile:
    def __init__(self, qss_file, var_file):
        qss_vars = self._parse_var_file(var_file)
        self.style = self._parse_qss_file(qss_file, qss_vars)

    @staticmethod
    def _parse_var_file(var_file):
        var_read_file = open(var_file).read().split()
        keys = [key for key in var_read_file if key[0] == '@']
        values = [value for value in var_read_file if value[0] == '#']
        qss_vars = {k: v for k, v in zip(keys, values)}
        return qss_vars

    @staticmethod
    def _parse_qss_file(qss_file, qss_vars):
        qss_read_file = open(qss_file).read()
        qss_updated_file = ""
        current_char = 0
        for _ in qss_read_file:
            if current_char == len(qss_read_file):
                break
            for key in qss_vars.keys():
                len_key = len(key)
                if qss_read_file[current_char:current_char+len_key] == key:
                    qss_updated_file += qss_vars[key]
                    current_char += len_key
                    break
            else:
                qss_updated_file += qss_read_file[current_char]
                current_char += 1
        return qss_updated_file


class StyleOneButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super(StyleOneButton, self).__init__(*args)


class StyleTwoButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super(StyleTwoButton, self).__init__(*args)


class StyleThreeButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super(StyleThreeButton, self).__init__(*args)
