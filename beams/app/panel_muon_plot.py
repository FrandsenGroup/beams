
import threading

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

from util import muon
from app.model import PlotContext, MuonDataContext


# noinspection PyArgumentList
class MuonPlotPanel(QtWidgets.QDockWidget):
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

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._display)
        layout.addWidget(self._control)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setWidget(widget)

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
        return float(self._control.input_freq_ymin.tex())

    def get_bin_from_input(self):
        return float(self._control.input_bin.text())

    def get_bin_from_slider(self):
        return float(self._control.slider_bin.text())

    def is_asymmetry_auto(self):
        return self._control.check_time_yauto.isChecked()

    def is_fft_auto(self):
        return self._control.check_freq_yauto.isChecked()

    def is_freq_auto(self):
        return self._control.check_freq_xauto.isChecked()

    def set_max_time(self, value):
        self._control.input_time_xmax.setText(str(value))

    def set_min_time(self, value):
        self._control.input_time_xmin.setText(str(value))

    def set_max_freq(self, value):
        self._control.input_freq_xmax.setText(str(value))

    def set_min_freq(self, value):
        self._control.input_freq_xmin.setText(str(value))

    def set_max_asymmetry(self, value):
        self._control.input_time_ymax.setText(str(value))

    def set_min_asymmetry(self, value):
        self._control.input_time_ymin.setText(str(value))

    def set_max_fft(self, value):
        self._control.input_freq_ymax.setText(str(value))

    def set_min_fft(self, value):
        self._control.input_freq_ymin.setText(str(value))

    def set_bin_input(self, value):
        self._control.input_bin.setText(str(value))

    def set_bin_slider(self, value):
        self._control.slider_bin.setValue(int(value))

    def plot_asymmetry(self, time, asymmetry, uncertainty, color, marker, linestyle, fillstyle):
        if uncertainty:
            self._display.axes_time.errorbar(time, asymmetry, uncertainty, color=color, marker=marker,
                                             linestyle=linestyle, fillstyle=fillstyle)
        else:
            self._display.axes_time.plot(time, asymmetry, color=color, marker=marker, linestyle=linestyle,
                                         fillstyle=fillstyle)

    def plot_fft(self, frequencies, fft, color, label):
        self._display.axes_freq.plot(frequencies, fft, color=color, label=label)

    def _set_asymmetry_plot_limits(self):
        pass

    def _set_fft_plot_limits(self):
        pass

    def _display_x_limits(self):
        pass

    def _display_y_limits(self):
        pass


class MuonPlotPanelPresenter:
    def __init__(self, view: MuonPlotPanel):
        self._view = view
        self._model = MuonPlotPanelModel(self)

    def _set_callbacks(self):
        self._view.connect_plot_parameters_to_slot(self._plot_parameter_changed)
        self._view.connect_bin_parameters_to_slot(self._bin_parameter_changed)

    def _plot_parameter_changed(self):
        threading.Thread(target=self._update_canvas(fast=False), daemon=True).start()

    def _bin_parameter_changed(self, moving):
        if moving:
            value = self._view.get_bin_from_slider()
            self._view.set_bin_input(value)

            if value % 5 != 0:  # fixme, do we still need or want this? Check if it has a significant effect.
                return

        else:
            self._view.set_bin_slider(self._view.get_bin_from_input())

        threading.Thread(target=self._update_canvas(fast=moving), daemon=True).start()

    def _update_canvas(self, fast=False):
        data = self._model.get_visible_run_data(self._view.get_bin_from_input(), fast)

        for style, time, asymmetry, uncertainty, frequencies, fft in data.items():
            self._view.plot_asymmetry(time, asymmetry, uncertainty,
                                      style[PlotContext.Keys.LINE_COLOR],
                                      style[PlotContext.Keys.MARKER],
                                      style[PlotContext.Keys.LINE],
                                      style[PlotContext.Keys.FILLSTYLE])

            if not fast:
                self._view.plot_fft(frequencies, fft,
                                    style[PlotContext.Keys.LINE_COLOR],
                                    style[PlotContext.Keys.LABEL])

    def update(self):
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
            frequencies, fft = None, None if fast else muon.calculate_muon_fft(asymmetry, time)
            full_data[run.run_id] = [style, time, asymmetry, uncertainty, frequencies, fft]

        return full_data

    def update(self):
        pass

    def notify(self):
        self._observer.update()
