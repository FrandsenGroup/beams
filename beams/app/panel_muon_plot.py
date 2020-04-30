
import threading
import warnings

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np

from app.model.model import PlotContext, MuonDataContext
from app.model import muon
from app.dialog_misc import WarningMessageDialog


# noinspection PyArgumentList
class MuonPlotPanel(QtWidgets.QDockWidget):
    # noinspection PyArgumentList
    class PlotToolbar(NavigationToolbar2QT):
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
    class PlotDisplay(FigureCanvas):
        def __init__(self):
            # fixme we need to add the toolbar but to do that this needs to be QMainWindow
            self._draw_pending = True
            self._is_drawing = True

            FigureCanvas.__init__(self, Figure())
            axes = self.figure.subplots(2, 1, gridspec_kw={'height_ratios': [2, 1]})
            self.figure.set_facecolor("#f9f9fd")
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
            self.axes_time.set_facecolor("#f9f9fd")

            self.axes_freq.spines['right'].set_visible(False)
            self.axes_freq.spines['top'].set_visible(False)
            self.axes_freq.spines['left'].set_visible(False)
            self.axes_freq.spines['bottom'].set_visible(False)
            self.axes_freq.tick_params(axis='x', colors='white')
            self.axes_freq.tick_params(axis='y', colors='white')
            self.axes_freq.set_facecolor("#f9f9fd")

        def set_style(self, remove_legend):
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
            self.axes_time.xaxis.label.set_color("#000000")
            self.axes_time.set_facecolor("#f9f9fd")

            self.axes_freq.spines['right'].set_visible(False)
            self.axes_freq.spines['top'].set_visible(False)
            self.axes_freq.spines['left'].set_visible(True)
            self.axes_freq.spines['bottom'].set_visible(True)
            self.axes_freq.set_xlabel(r'Frequency (MHz)', fontsize=title_font_size)
            self.axes_freq.set_ylabel(r'FFT$^2$', fontsize=title_font_size)
            self.axes_freq.ticklabel_format(style='sci', axis='y', scilimits=(0, 0))
            self.axes_freq.set_facecolor("#f9f9fd")
            if not remove_legend:
                self.axes_freq.legend(loc='upper right')

            self.figure.tight_layout()

    # noinspection PyArgumentList
    class PlotControl(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            # self.setTitleBarWidget(QtWidgets.QWidget())

            # self._full_widget = QtWidgets.QWidget()

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

            # self.setWidget(self._full_widget)

        def _set_widget_attributes(self):
            self.check_freq_xauto.setChecked(True)
            self.check_freq_yauto.setChecked(True)
            self.check_time_yauto.setChecked(True)

            self.input_time_xmin.setText("0")
            self.input_time_xmax.setText("8")
            self.input_time_ymin.setText("-0.3")
            self.input_time_ymax.setText("-0.5")

            self.input_time_ymin.setEnabled(False)
            self.input_time_ymax.setEnabled(False)

            self.input_freq_xmin.setEnabled(False)
            self.input_freq_xmax.setEnabled(False)

            self.input_freq_ymin.setEnabled(False)
            self.input_freq_ymax.setEnabled(False)

            self.slider_bin.setMinimum(0)
            self.slider_bin.setMaximum(500)
            self.slider_bin.setValue(150)
            self.slider_bin.setTickPosition(QtWidgets.QSlider.TicksBothSides)
            self.slider_bin.setTickInterval(20)

            self.input_bin.setText(str(self.slider_bin.value()))

        def _set_widget_tooltips(self):
            pass

        def _set_widget_dimensions(self):
            box_size = 40
            self.input_time_xmin.setFixedWidth(box_size)
            self.input_time_xmax.setFixedWidth(box_size)
            self.input_time_ymin.setFixedWidth(box_size)
            self.input_time_ymax.setFixedWidth(box_size)
            self.input_freq_xmin.setFixedWidth(box_size)
            self.input_freq_xmax.setFixedWidth(box_size)
            self.input_freq_ymin.setFixedWidth(box_size)
            self.input_freq_ymax.setFixedWidth(box_size)
            self.input_bin.setFixedWidth(50)

        def _set_widget_layout(self):
            main_layout = QtWidgets.QVBoxLayout()

            row_1 = QtWidgets.QHBoxLayout()
            row_1.addWidget(self._label_input_bin)
            row_1.addWidget(self.input_bin)
            row_1.addWidget(self.slider_bin)

            main_layout.addLayout(row_1)

            time_form = QtWidgets.QGroupBox('Time')
            time_layout = QtWidgets.QFormLayout()
            time_grid = QtWidgets.QGridLayout()

            time_grid.addWidget(self._label_time_xmin, 0, 2)
            time_grid.addWidget(self.input_time_xmin, 0, 3)
            time_grid.addWidget(self._label_time_xmax, 0, 4)
            time_grid.addWidget(self.input_time_xmax, 0, 5)
            time_grid.addWidget(self._label_time_yauto, 1, 0)
            time_grid.addWidget(self.check_time_yauto, 1, 1)
            time_grid.addWidget(self._label_time_ymin, 1, 2)
            time_grid.addWidget(self.input_time_ymin, 1, 3)
            time_grid.addWidget(self._label_time_ymax, 1, 4)
            time_grid.addWidget(self.input_time_ymax, 1, 5)

            temp_row = QtWidgets.QHBoxLayout()
            temp_row.addLayout(time_grid)
            time_layout.addRow(temp_row)

            time_form.setLayout(time_layout)

            freq_form = QtWidgets.QGroupBox('Frequency')
            freq_layout = QtWidgets.QFormLayout()
            freq_grid = QtWidgets.QGridLayout()

            freq_grid.addWidget(self._label_freq_xauto, 0, 0)
            freq_grid.addWidget(self.check_freq_xauto, 0, 1)
            freq_grid.addWidget(self._label_freq_xmin, 0, 2)
            freq_grid.addWidget(self.input_freq_xmin, 0, 3)
            freq_grid.addWidget(self._label_freq_xmax, 0, 4)
            freq_grid.addWidget(self.input_freq_xmax, 0, 5)
            freq_grid.addWidget(self._label_freq_yauto, 1, 0)
            freq_grid.addWidget(self.check_freq_yauto, 1, 1)
            freq_grid.addWidget(self._label_freq_ymin, 1, 2)
            freq_grid.addWidget(self.input_freq_ymin, 1, 3)
            freq_grid.addWidget(self._label_freq_ymax, 1, 4)
            freq_grid.addWidget(self.input_freq_ymax, 1, 5)

            temp_row = QtWidgets.QHBoxLayout()
            temp_row.addLayout(freq_grid)
            freq_layout.addRow(temp_row)

            freq_form.setLayout(freq_layout)

            editor_layout = QtWidgets.QHBoxLayout()
            editor_layout.addWidget(time_form)
            editor_layout.addWidget(freq_form)

            main_layout.addLayout(editor_layout)

            # self._full_widget.setLayout(main_layout)
            self.setLayout(main_layout)

    def __init__(self):
        super(MuonPlotPanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())

        self._display = MuonPlotPanel.PlotDisplay()
        self._control = MuonPlotPanel.PlotControl()

        self._control.setFixedHeight(130)

        # This insanity is all because dock widgets can't have toolbars.
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._display)
        layout.addWidget(self._control)
        dock_central_widget = QtWidgets.QWidget()
        dock_central_widget.setLayout(layout)
        dock_widget = QtWidgets.QDockWidget()
        dock_widget.setTitleBarWidget(QtWidgets.QWidget())
        dock_widget.setWidget(dock_central_widget)
        widget = QtWidgets.QMainWindow()
        widget.setCentralWidget(dock_widget)
        widget.addToolBar(QtCore.Qt.TopToolBarArea, MuonPlotPanel.PlotToolbar(self._display, widget))
        self.setWidget(widget)
        self.setEnabled(False)
        self._presenter = MuonPlotPanelPresenter(self)

    def connect_plot_parameters_to_slot(self, slot):
        self._control.input_freq_ymin.returnPressed.connect(lambda: slot())
        self._control.input_freq_ymax.returnPressed.connect(lambda: slot())
        self._control.input_time_ymin.returnPressed.connect(lambda: slot())
        self._control.input_time_ymax.returnPressed.connect(lambda: slot())
        self._control.input_freq_xmin.returnPressed.connect(lambda: slot())
        self._control.input_freq_xmax.returnPressed.connect(lambda: slot())
        self._control.input_time_xmax.returnPressed.connect(lambda: slot())
        self._control.input_time_xmin.returnPressed.connect(lambda: slot())
        self._control.check_freq_xauto.stateChanged.connect(lambda: slot())
        self._control.check_freq_yauto.stateChanged.connect(lambda: slot())
        self._control.check_time_yauto.stateChanged.connect(lambda: slot())

    def connect_bin_parameters_to_slot(self, slot):
        self._control.slider_bin.sliderMoved.connect(lambda: slot(moving=True))
        self._control.slider_bin.sliderReleased.connect(lambda: slot(moving=False))
        self._control.input_bin.returnPressed.connect(lambda: slot(moving=False))

    def connect_check_parameters_to_slot(self, slot):
        self._control.check_freq_yauto.stateChanged.connect(lambda: slot())
        self._control.check_freq_xauto.stateChanged.connect(lambda: slot())
        self._control.check_time_yauto.stateChanged.connect(lambda: slot())

    def get_max_time(self):
        return float(self._control.input_time_xmax.text())

    def get_min_time(self):
        return float(self._control.input_time_xmin.text())

    def get_max_freq(self):
        return float(self._control.input_freq_xmax.text())

    def get_min_freq(self):
        return float(self._control.input_freq_xmin.text())

    def get_max_asymmetry(self):
        return float(self._control.input_time_ymax.text())

    def get_min_asymmetry(self):
        return float(self._control.input_time_ymin.text())

    def get_max_fft(self):
        return float(self._control.input_freq_ymax.text())

    def get_min_fft(self):
        return float(self._control.input_freq_ymin.text())

    def get_bin_from_input(self):
        return float(self._control.input_bin.text())

    def get_bin_from_slider(self):
        return float(self._control.slider_bin.value())

    def is_asymmetry_auto(self):
        return self._control.check_time_yauto.isChecked()

    def is_fft_auto(self):
        return self._control.check_freq_yauto.isChecked()

    def is_freq_auto(self):
        return self._control.check_freq_xauto.isChecked()

    def set_enabled_asymmetry_auto(self, enabled):
        self._control.input_time_ymin.setEnabled(enabled)
        self._control.input_time_ymax.setEnabled(enabled)

    def set_enabled_frequency_auto(self, enabled):
        self._control.input_freq_xmin.setEnabled(enabled)
        self._control.input_freq_xmax.setEnabled(enabled)

    def set_enabled_fft_auto(self, enabled):
        self._control.input_freq_ymin.setEnabled(enabled)
        self._control.input_freq_ymax.setEnabled(enabled)

    def set_max_time(self, value):
        self._control.input_time_xmax.setText('{0:.3f}'.format(value))

    def set_min_time(self, value):
        self._control.input_time_xmin.setText('{0:.3f}'.format(value))

    def set_max_freq(self, value):
        self._control.input_freq_xmax.setText('{0:.3f}'.format(value))

    def set_min_freq(self, value):
        self._control.input_freq_xmin.setText('{0:.3f}'.format(value))

    def set_max_asymmetry(self, value):
        self._control.input_time_ymax.setText('{0:.3f}'.format(value))

    def set_min_asymmetry(self, value):
        self._control.input_time_ymin.setText('{0:.3f}'.format(value))

    def set_max_fft(self, value):
        self._control.input_freq_ymax.setText('{0:.1f}'.format(value))

    def set_min_fft(self, value):
        self._control.input_freq_ymin.setText('{0:.1f}'.format(value))

    def set_bin_input(self, value):
        self._control.input_bin.setText(str(value))

    def set_bin_slider(self, value):
        self._control.slider_bin.setValue(int(value))

    def plot_asymmetry(self, time, asymmetry, uncertainty, color, marker_color, line_color, errorbar_color,
                       linestyle, marker, errorbar_style, fillstyle, line_width, marker_size, errorbar_width):

        marker_color = color if marker_color == 'Default' else marker_color
        line_color = color if line_color == 'Default' else line_color
        errorbar_color = color if errorbar_color == 'Default' else errorbar_color

        if uncertainty is not None:
            print(uncertainty)
            self._display.axes_time.errorbar(time, asymmetry, uncertainty, mfc=marker_color, mec=marker_color,
                                             color=color, linestyle=linestyle, marker=marker, fillstyle=fillstyle,
                                             linewidth=line_width, markersize=marker_size, elinewidth=errorbar_width)
        else:
            self._display.axes_time.plot(time, asymmetry, mfc=marker_color, mec=marker_color, color=color,
                                         linestyle=linestyle, marker=marker, fillstyle=fillstyle, linewidth=line_width,
                                         markersize=marker_size)

    def plot_fft(self, frequencies, fft, color, label):
        self._display.axes_freq.plot(frequencies, fft, color=color, label=label)

    def set_asymmetry_plot_limits(self, max_asymmetry, min_asymmetry):
        if not self.is_asymmetry_auto():
            try:
                y_min = self.get_min_asymmetry()
                y_max = self.get_max_asymmetry()
            except ValueError:
                WarningMessageDialog.launch(["Invalid asymmetry limits."])
                return
            self._display.axes_time.set_ylim(y_min, y_max)
        else:
            y_min = min_asymmetry - abs(min_asymmetry * 0.1)
            y_max = max_asymmetry + abs(max_asymmetry * 0.1)
            self._display.axes_time.set_ylim(y_min, y_max)
            self.set_min_asymmetry(y_min)
            self.set_max_asymmetry(y_max)

        try:
            x_min = self.get_min_time()
            x_max = self.get_max_time()
        except ValueError:
            WarningMessageDialog.launch(["Invalid asymmetry limits."])
            return
        self._display.axes_time.set_xlim(x_min, x_max)

    def set_fft_plot_limits(self, max_fft):
        if not self.is_fft_auto():
            try:
                y_min = self.get_min_fft()
                y_max = self.get_max_fft()
            except ValueError:
                WarningMessageDialog.launch(["Invalid frequency limits."])
                return
            self._display.axes_freq.set_ylim(y_min, y_max)
        else:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                self._display.axes_freq.set_ylim(0, max_fft * 1.1)
            self.set_min_fft(0)
            self.set_max_fft(max_fft * 1.1)

        if not self.is_freq_auto():
            try:
                x_min = self.get_min_freq()
                x_max = self.get_max_freq()
            except ValueError:
                WarningMessageDialog.launch(["Invalid frequency limits."])
                return
            self._display.axes_freq.set_xlim(x_min, x_max)
        else:
            x_min, x_max = self._display.axes_freq.get_xlim()
            self.set_min_freq(x_min)
            self.set_max_freq(x_max)

    def finish_plotting(self, remove_legend=False):
        self._display.set_style(remove_legend)
        self._display.axes_time.figure.canvas.draw()

    def start_plotting(self):
        self._display.axes_time.clear()
        self._display.axes_freq.clear()

    def set_blank(self):
        self.setEnabled(False)
        self._display.set_blank()
        self._display.axes_time.figure.canvas.draw()


class MuonPlotPanelPresenter:
    def __init__(self, view: MuonPlotPanel):
        self._view = view
        self._model = MuonPlotPanelModel(self)
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.connect_plot_parameters_to_slot(self._plot_parameter_changed)
        self._view.connect_bin_parameters_to_slot(self._bin_parameter_changed)
        self._view.connect_check_parameters_to_slot(self._check_parameter_changed)

    def _check_parameter_changed(self):
        self._view.set_enabled_asymmetry_auto(not self._view.is_asymmetry_auto())
        self._view.set_enabled_frequency_auto(not self._view.is_freq_auto())
        self._view.set_enabled_fft_auto(not self._view.is_fft_auto())

    def _plot_parameter_changed(self):
        threading.Thread(target=self._update_canvas(fast=False), daemon=True).start()

    def _bin_parameter_changed(self, moving):
        if moving:
            value = self._view.get_bin_from_slider()
            self._view.set_bin_input(value)

            if value % 5 != 0:  # fixme
                return

        else:
            self._view.set_bin_slider(self._view.get_bin_from_input())

        threading.Thread(target=self._update_canvas(fast=moving), daemon=True).start()

    def _update_canvas(self, fast=False):
        data = self._model.get_visible_run_data(self._view.get_bin_from_input(), fast)
        self._view.start_plotting()
        if len(data.items()) == 0:
            self._view.set_blank()
            return
        else:
            self._view.setEnabled(True)

        max_asymmetry = -1
        min_asymmetry = 1
        max_fft = 0
        min_time = self._view.get_min_time()
        max_time = self._view.get_max_time()
        bin_size = self._view.get_bin_from_input()

        for style, time, asymmetry, uncertainty in data.values():
            # We have to do this logic because Matplotlib is not good at setting good default plot limits
            frac_start = float(min_time) / (time[len(time) - 1] - time[0])
            frac_end = float(max_time) / (time[len(time) - 1] - time[0])
            start_index = int(np.floor(len(asymmetry) * frac_start))
            end_index = int(np.floor(len(asymmetry) * frac_end))
            local_max = np.max(asymmetry[start_index:end_index])
            max_asymmetry = local_max if local_max > max_asymmetry else max_asymmetry
            local_min = np.min(asymmetry[start_index:end_index])
            min_asymmetry = local_min if local_min < min_asymmetry else min_asymmetry

            self._view.plot_asymmetry(time, asymmetry, uncertainty,
                                      color=style[PlotContext.Keys.DEFAULT_COLOR],
                                      marker=style[PlotContext.Keys.MARKER],
                                      linestyle=style[PlotContext.Keys.LINESTYLE],
                                      fillstyle=style[PlotContext.Keys.FILLSTYLE],
                                      marker_color=style[PlotContext.Keys.MARKER_COLOR],
                                      marker_size=style[PlotContext.Keys.MARKER_SIZE],
                                      line_color=style[PlotContext.Keys.LINE_COLOR],
                                      line_width=style[PlotContext.Keys.LINE_WIDTH],
                                      errorbar_color=style[PlotContext.Keys.ERRORBAR_COLOR],
                                      errorbar_style=style[PlotContext.Keys.ERRORBAR_STYLE],
                                      errorbar_width=style[PlotContext.Keys.ERRORBAR_WIDTH])

            if not fast:
                frequencies, fft = self._model.get_fft_data(time, asymmetry, min_time, max_time, bin_size)
                local_max = np.max(fft)
                max_fft = local_max if local_max > max_fft else max_fft

                self._view.plot_fft(frequencies, fft,
                                    style[PlotContext.Keys.DEFAULT_COLOR],
                                    style[PlotContext.Keys.LABEL])

        self._view.set_asymmetry_plot_limits(max_asymmetry, min_asymmetry)
        self._view.set_fft_plot_limits(max_fft)
        self._view.finish_plotting(fast)

    def update(self):
        print('Updating the Plot Panel')
        threading.Thread(target=self._update_canvas(fast=False), daemon=True).start()


class MuonPlotPanelModel:
    def __init__(self, observer):
        self._observer = observer
        self._plot_context = PlotContext()
        self._data_context = MuonDataContext()

        self._plot_context.subscribe(self)
        self._data_context.subscribe(self)

    def get_visible_run_data(self, bin_size, fast=False):
        styles = self._plot_context.get_visible_styles()
        full_data = dict()
        for style in styles:

            run = self._data_context.get_run_by_id(style[PlotContext.Keys.ID])
            asymmetry = muon.bin_muon_asymmetry(run, bin_size)
            time = muon.bin_muon_time(run, bin_size)
            uncertainty = None if fast else muon.bin_muon_uncertainty(run, bin_size)
            full_data[run.id] = [style, time, asymmetry, uncertainty]

        return full_data

    def get_fft_data(self, time, asymmetry, xmin, xmax, bin_size):
        num_bins = self.get_num_bins(xmin, xmax, bin_size)
        start_bin = self.get_start_bin(xmin, bin_size)
        return muon.calculate_muon_fft(asymmetry[start_bin:start_bin + num_bins], time[start_bin:start_bin + num_bins])

    def get_num_bins(self, xmin, xmax, bin_size):
        return int((float(xmax)-float(xmin))/(float(bin_size)/1000))

    def get_start_bin(self, xmin, bin_size):
        return int(float(xmin) / (float(bin_size) / 1000))

    def update(self):
        self.notify()

    def notify(self):
        self._observer.update()
