
import traceback
import enum

from PyQt5 import QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

from app.util import widgets
from app.model import files
from app.dialog_misc import WarningMessageDialog, FileDisplayDialog
from app.model.model import MuonDataContext, FocusContext


# noinspection PyArgumentList
class HistogramDisplayTab(QtWidgets.QWidget):
    class HistogramCanvas(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.figure.set_facecolor("#FFFFFF")
            self.canvas_axes = self.figure.add_subplot(111, label='Canvas')

    class HistogramToolbar(NavigationToolbar2QT):
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

    class KWArgs:
        Histograms = 'histograms'
        Meta = 'meta'
        Histogram = 'histogram'
        Histogram_Label = 'label'
        File = 'file'
        Run_ID = 'id'

    def __init__(self):
        super(HistogramDisplayTab, self).__init__()
        self._main = QtWidgets.QMainWindow()
        widget = QtWidgets.QWidget()
        self._new_layout = QtWidgets.QVBoxLayout(widget)

        self.radio_bkgd_one = QtWidgets.QRadioButton()
        self.radio_bkgd_two = QtWidgets.QRadioButton()
        self.radio_t0 = QtWidgets.QRadioButton()
        self.radio_goodbin1 = QtWidgets.QRadioButton()
        self.radio_goodbin2 = QtWidgets.QRadioButton()
        self.button_reset = widgets.StyleTwoButton("Reset")
        self.button_save = widgets.StyleOneButton("Save")
        self.button_see_file = widgets.StyleOneButton("See File")
        self.button_apply = widgets.StyleTwoButton("Apply")
        self.button_done = widgets.StyleOneButton("Save")
        self.canvas = HistogramDisplayTab.HistogramCanvas()
        self.check_editing = QtWidgets.QCheckBox()
        self.label_explanation = QtWidgets.QLabel()
        self.label_bkgd1 = QtWidgets.QLabel("Background Start")
        self.label_bkgd2 = QtWidgets.QLabel("Background End")
        self.label_t0 = QtWidgets.QLabel("T0")
        self.label_goodbin1 = QtWidgets.QLabel("Good Bin Start")
        self.label_goodbin2 = QtWidgets.QLabel("Good Bin End")
        self.input_bkgd1 = QtWidgets.QLineEdit()
        self.input_bkgd2 = QtWidgets.QLineEdit()
        self.input_t0 = QtWidgets.QLineEdit()
        self.input_goodbin1 = QtWidgets.QLineEdit()
        self.input_goodbin2 = QtWidgets.QLineEdit()
        self.histogram_choices = QtWidgets.QComboBox()

        self._extent = None
        self._toolbar = HistogramDisplayTab.HistogramToolbar(self.canvas, self._main)
        self._main.addToolBar(self._toolbar)
        self._set_widget_attributes()
        self._set_widget_dimensions()
        self._set_widget_tooltips()
        self._set_widget_layout()
        self._main.setCentralWidget(widget)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._main)

        self._presenter = HistogramDisplayPresenter(self)
        self.set_blank()

        self.histogram = None
        self.histogram_label = None
        self.bkgd1 = None
        self.bkgd2 = None
        self.t0 = None
        self.goodbin1 = None
        self.goodbin2 = None

        self.__initial = True

    def set_blank(self):
        self.setEnabled(False)
        self.canvas.canvas_axes.clear()
        self.canvas.canvas_axes.spines['right'].set_visible(False)
        self.canvas.canvas_axes.spines['top'].set_visible(False)
        self.canvas.canvas_axes.spines['left'].set_visible(False)
        self.canvas.canvas_axes.spines['bottom'].set_visible(False)
        self.canvas.canvas_axes.set_title("Load and select files in the display on the left to see histogram data.",
                                  fontsize=12)
        self.canvas.canvas_axes.title.set_color("#B8B8B8")
        self.canvas.canvas_axes.tick_params(axis='x', colors='white')
        self.canvas.canvas_axes.tick_params(axis='y', colors='white')
        self.canvas.canvas_axes.set_xlabel("", fontsize=12)
        self.canvas.canvas_axes.set_ylabel("", fontsize=12)
        self.canvas.canvas_axes.set_facecolor("#FFFFFF")

        self.canvas.canvas_axes.figure.canvas.draw()

    def set_new_lines(self, bkg1=None, bkg2=None, t0=None, goodbin1=None, goodbin2=None, thick=False, new_histogram=None):
        bkg1_width = 1
        bkg2_width = 1
        t0_width = 1
        goodbin1_width = 1
        goodbin2_width = 1

        if bkg1 is not None:
            self.bkgd1 = bkg1
            self.input_bkgd1.setText(str(bkg1))
            if thick:
                bkg1_width = 2
        if bkg2 is not None:
            self.bkgd2 = bkg2
            self.input_bkgd2.setText(str(bkg2))
            if thick:
                bkg2_width = 2
        if t0 is not None:
            self.t0 = t0
            self.input_t0.setText(str(t0))
            if thick:
                t0_width = 2
        if goodbin1 is not None:
            self.goodbin1 = goodbin1
            self.input_goodbin1.setText(str(goodbin1))
            if thick:
                goodbin1_width = 2
        if goodbin2 is not None:
            self.goodbin2 = goodbin2
            self.input_goodbin2.setText(str(goodbin2))
            if thick:
                goodbin2_width = 2

        self._extent = self.canvas.canvas_axes.axis()
        self.canvas.canvas_axes.clear()
        self.canvas.canvas_axes.plot(self.histogram, linestyle='None', marker='s')
        self.canvas.canvas_axes.axvline(x=self.bkgd1, linewidth=bkg1_width, color='r')
        self.canvas.canvas_axes.axvline(x=self.bkgd2, linewidth=bkg2_width, color='r')
        self.canvas.canvas_axes.axvline(x=self.t0, linewidth=t0_width, color='g')
        self.canvas.canvas_axes.axvline(x=self.goodbin1, linewidth=goodbin1_width, color='b')
        self.canvas.canvas_axes.axvline(x=self.goodbin2, linewidth=goodbin2_width, color='b')

        if not self.__initial and new_histogram is None:
            self.canvas.canvas_axes.axis(self._extent)

        self.canvas.canvas_axes.figure.canvas.draw()

        self.__initial = False

    def reset(self, bkgd1, bkgd2, t0, goodbin1, goodbin2):
        self.bkgd2 = bkgd2
        self.bkgd1 = bkgd1
        self.t0 = t0
        self.goodbin1 = goodbin1
        self.goodbin2 = goodbin2

        self.input_bkgd1.setText(str(bkgd1))
        self.input_bkgd2.setText(str(bkgd2))
        self.input_t0.setText(str(t0))
        self.input_goodbin1.setText(str(goodbin1))
        self.input_goodbin2.setText(str(goodbin2))

        self._extent = self.canvas.canvas_axes.axis()
        self.canvas.canvas_axes.clear()
        self.canvas.canvas_axes.plot(self.histogram, linestyle='None', marker='s')
        self.canvas.canvas_axes.axvline(x=bkgd1, linewidth=1, color='r')
        self.canvas.canvas_axes.axvline(x=bkgd2, linewidth=1, color='r')
        self.canvas.canvas_axes.axvline(x=t0, linewidth=1, color='g')
        self.canvas.canvas_axes.axvline(x=goodbin1, linewidth=1, color='b')
        self.canvas.canvas_axes.axvline(x=goodbin2, linewidth=1, color='b')
        self.canvas.canvas_axes.axis(self._extent)
        self.canvas.canvas_axes.figure.canvas.draw()

    def _set_widget_tooltips(self):
        self.check_editing.setToolTip("Check to enable bin changes")

    def _set_widget_attributes(self):
        self.radio_bkgd_one.setChecked(True)
        self.set_enabled(False)

        message = "Before moving the bars manually below make sure you have deselected the zoom option in the toolbar.\n" \
                  "Then check the box to enable editing and select the bin you would like to change."
        self.label_explanation.setText(message)

        self.button_reset.setAutoDefault(False)
        self.button_save.setAutoDefault(False)
        self.button_see_file.setAutoDefault(False)
        self.button_apply.setAutoDefault(False)
        self.button_done.setAutoDefault(False)

    def _set_widget_dimensions(self):
        self.button_reset.setFixedWidth(60)
        self.button_save.setFixedWidth(60)
        self.button_see_file.setFixedWidth(60)
        self.button_done.setFixedWidth(60)
        self.button_apply.setFixedWidth(60)
        self.input_t0.setFixedWidth(30)
        self.input_bkgd1.setFixedWidth(30)
        self.input_bkgd2.setFixedWidth(30)
        self.input_goodbin1.setFixedWidth(30)
        self.input_goodbin2.setFixedWidth(30)

    def _set_widget_layout(self):
        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Histogram"))
        row.addSpacing(2)
        row.addWidget(self.histogram_choices)
        row.addSpacing(10)
        row.addWidget(self.button_see_file)
        row.addStretch()
        self._new_layout.addLayout(row)

        radio_layout = QtWidgets.QHBoxLayout()
        radio_layout.addWidget(self.check_editing)
        radio_layout.addSpacing(15)
        radio_layout.addWidget(self.radio_bkgd_one)
        radio_layout.addWidget(self.input_bkgd1)
        radio_layout.addWidget(self.label_bkgd1)
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_bkgd_two)
        radio_layout.addWidget(self.input_bkgd2)
        radio_layout.addWidget(self.label_bkgd2)
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_t0)
        radio_layout.addWidget(self.input_t0)
        radio_layout.addWidget(self.label_t0)
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_goodbin1)
        radio_layout.addWidget(self.input_goodbin1)
        radio_layout.addWidget(self.label_goodbin1)
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_goodbin2)
        radio_layout.addWidget(self.input_goodbin2)
        radio_layout.addWidget(self.label_goodbin2)
        radio_layout.addSpacing(65)
        radio_layout.addSpacing(65)
        radio_layout.addWidget(self.button_reset)
        # radio_layout.addSpacing(5)
        # radio_layout.addWidget(self.button_apply)
        radio_layout.addSpacing(5)
        radio_layout.addWidget(self.button_done)
        radio_layout.addStretch()

        radio_form = QtWidgets.QGroupBox("Edit")
        radio_form_layout = QtWidgets.QFormLayout()
        radio_form_layout.addWidget(self.label_explanation)
        radio_form_layout.addRow(radio_layout)
        radio_form.setLayout(radio_form_layout)
        radio_form.setMaximumHeight(100)

        self._new_layout.addWidget(radio_form)
        self._new_layout.addWidget(self.canvas)

    def replace_histogram_plot(self, histogram):
        self.histogram_label = self.histogram_choices.currentText()
        self.histogram = histogram
        self.set_new_lines(new_histogram=True)

    def set_enabled(self, enabled, multiple=False, editing=False):
        if not enabled:
            self.set_blank()

        self.setEnabled(enabled)
        self.button_save.setEnabled(enabled)
        self.button_reset.setEnabled(enabled)
        self.button_see_file.setEnabled(enabled)

        self.radio_bkgd_two.setEnabled(editing and enabled)
        self.radio_bkgd_one.setEnabled(editing and enabled)
        self.radio_t0.setEnabled(editing and enabled)
        self.radio_goodbin2.setEnabled(editing and enabled)
        self.radio_goodbin1.setEnabled(editing and enabled)
        self.label_bkgd2.setEnabled(editing and enabled)
        self.label_bkgd1.setEnabled(editing and enabled)
        self.label_t0.setEnabled(editing and enabled)
        self.label_goodbin2.setEnabled(editing and enabled)
        self.label_goodbin1.setEnabled(editing and enabled)
        self.input_bkgd1.setEnabled(editing and enabled)
        self.input_bkgd2.setEnabled(editing and enabled)
        self.input_t0.setEnabled(editing and enabled)
        self.input_goodbin2.setEnabled(editing and enabled)
        self.input_goodbin1.setEnabled(editing and enabled)

        if multiple and enabled:
            self.button_see_file.setEnabled(False)
            self.canvas.canvas_axes.clear()
            self.canvas.canvas_axes.spines['right'].set_visible(False)
            self.canvas.canvas_axes.spines['top'].set_visible(False)
            self.canvas.canvas_axes.spines['left'].set_visible(False)
            self.canvas.canvas_axes.spines['bottom'].set_visible(False)
            self.canvas.canvas_axes.set_title("Cannot display histogram with multiple runs selected.\nValues can be edited above (this will apply changes to all selected runs).",
                                              fontsize=12)
            self.canvas.canvas_axes.title.set_color("#B8B8B8")
            self.canvas.canvas_axes.tick_params(axis='x', colors='white')
            self.canvas.canvas_axes.tick_params(axis='y', colors='white')
            self.canvas.canvas_axes.set_facecolor("#FFFFFF")
            self.canvas.canvas_axes.figure.canvas.draw()
            self.label_bkgd2.setEnabled(enabled)
            self.label_bkgd1.setEnabled(enabled)
            self.label_t0.setEnabled(enabled)
            self.label_goodbin2.setEnabled(enabled)
            self.label_goodbin1.setEnabled(enabled)
            self.input_bkgd1.setEnabled(enabled)
            self.input_bkgd2.setEnabled(enabled)
            self.input_t0.setEnabled(enabled)
            self.input_goodbin2.setEnabled(enabled)
            self.input_goodbin1.setEnabled(enabled)
        elif enabled:
            self.button_see_file.setEnabled(True)
            self.canvas.canvas_axes.tick_params(axis='x', colors='black')
            self.canvas.canvas_axes.tick_params(axis='y', colors='black')
            self.canvas.canvas_axes.tick_params(axis='x', colors='black')
            self.canvas.canvas_axes.tick_params(axis='y', colors='black')

            title_font_size = 12
            self.canvas.canvas_axes.spines['right'].set_visible(False)
            self.canvas.canvas_axes.spines['top'].set_visible(False)
            self.canvas.canvas_axes.spines['left'].set_visible(True)
            self.canvas.canvas_axes.spines['bottom'].set_visible(True)
            self.canvas.canvas_axes.set_xlabel("Time Bin", fontsize=title_font_size)
            self.canvas.canvas_axes.set_ylabel("Counts", fontsize=title_font_size)
            self.canvas.canvas_axes.xaxis.label.set_color("#000000")
            self.canvas.canvas_axes.set_facecolor("#FFFFFF")
            self.canvas.canvas_axes.figure.canvas.draw()

    def get_histogram_label(self):
        return self.histogram_choices.currentText()

    def get_input_bkgd1(self):
        return int(self.input_bkgd1.text())

    def get_input_bkgd2(self):
        return int(self.input_bkgd2.text())

    def get_input_t0(self):
        return int(self.input_t0.text())

    def get_input_goodbin1(self):
        return int(self.input_goodbin1.text())

    def get_input_goodbin2(self):
        return int(self.input_goodbin2.text())

    def get_bkgd1(self):
        return self.bkgd1

    def get_bkgd2(self):
        return self.bkgd2

    def get_t0(self):
        return self.t0

    def get_goodbin1(self):
        return self.goodbin1

    def get_goodbin2(self):
        return self.goodbin2

    def is_bkgd1(self):
        return self.radio_bkgd_one.isChecked()

    def is_bkgd2(self):
        return self.radio_bkgd_two.isChecked()

    def is_t0(self):
        return self.radio_t0.isChecked()

    def is_goodbin1(self):
        return self.radio_goodbin1.isChecked()

    def is_goodbin2(self):
        return self.radio_goodbin2.isChecked()

    def is_editing(self):
        return self.check_editing.isChecked()

    def add_histogram_labels(self, labels):
        self.histogram_choices.clear()
        self.histogram_choices.addItems(labels)


class HistogramDisplayPresenter:
    def __init__(self, view: HistogramDisplayTab):
        self.__pressed = False
        self.__editing = False
        self.__multiple = False
        self._view = view
        self._model = HistogramDisplayModel(self)
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.canvas.figure.canvas.mpl_connect('button_press_event', self._mouse_interaction)
        self._view.canvas.figure.canvas.mpl_connect('button_release_event', self._mouse_interaction)
        self._view.canvas.figure.canvas.mpl_connect('motion_notify_event', self._mouse_interaction)
        self._view.button_reset.pressed.connect(self._reset_clicked)
        self._view.button_done.pressed.connect(self._save_clicked)
        self._view.button_see_file.pressed.connect(self._see_file_clicked)
        self._view.check_editing.stateChanged.connect(self._editing_checked)
        self._view.histogram_choices.currentTextChanged.connect(self._histogram_choice_changed)
        self._view.input_t0.returnPressed.connect(lambda: self._input_changed('t0', self._view.get_input_t0()))
        self._view.input_bkgd1.returnPressed.connect(lambda: self._input_changed('bkgd1', self._view.get_input_bkgd1()))
        self._view.input_bkgd2.returnPressed.connect(lambda: self._input_changed('bkgd2', self._view.get_input_bkgd2()))
        self._view.input_goodbin1.returnPressed.connect(lambda: self._input_changed('goodbin1', self._view.get_input_goodbin1()))
        self._view.input_goodbin2.returnPressed.connect(lambda: self._input_changed('goodbin2', self._view.get_input_goodbin2()))

    def _mouse_interaction(self, event):
        if not self.__editing:
            return

        if event.button is not None and event.xdata is not None:
            self.__pressed = True

            thick = True if event.name != 'button_release_event' else False

            if self._view.is_bkgd1() and self._view.get_bkgd2() > event.xdata > 0:
                self._view.set_new_lines(bkg1=int(event.xdata), thick=thick)

            elif self._view.is_bkgd2() and event.xdata > self._view.get_bkgd1():
                self._view.set_new_lines(bkg2=int(event.xdata), thick=thick)

            elif self._view.is_t0() and event.xdata > 0:
                self._view.set_new_lines(t0=int(event.xdata), thick=thick)

            elif self._view.is_goodbin1() and event.xdata < self._view.get_goodbin2():
                self._view.set_new_lines(goodbin1=int(event.xdata), thick=thick)

            elif self._view.is_goodbin2() and event.xdata > self._view.get_goodbin1():
                self._view.set_new_lines(goodbin2=int(event.xdata), thick=thick)

            bkgd1 = self._view.get_bkgd1()
            bkgd2 = self._view.get_bkgd2()
            t0 = self._view.get_t0()
            goodbin1 = self._view.get_goodbin1()
            goodbin2 = self._view.get_goodbin2()

            self._model.store_focused_run_meta(self._view.get_histogram_label(), bkgd1, bkgd2, t0, goodbin1, goodbin2)

        elif event.button is None and self.__pressed:
            self.__pressed = False

    def _reset_clicked(self):
        self._model.reset_focused_run_meta()

        for item in self._model.get_focused_run_meta(self._view.histogram_label).items():
            self._view.reset(item[1][files.BACKGROUND_ONE_KEY], item[1][files.BACKGROUND_TWO_KEY], item[1][files.T0_KEY],
                             item[1][files.GOOD_BIN_ONE_KEY], item[1][files.GOOD_BIN_TWO_KEY])
            break

    def _save_clicked(self):
        self._model.finish()

    def _editing_checked(self):
        self.__editing = self._view.is_editing()
        self._view.set_enabled(True, self.__multiple, self.__editing)

    def _see_file_clicked(self):
        filename, file_content = self._model.get_focused_run_file_content()
        FileDisplayDialog.launch([filename, file_content])

    def _histogram_choice_changed(self):
        histogram_label = self._view.get_histogram_label()

        if histogram_label != '':
            histogram = self._model.get_focused_run_histogram(histogram_label)
            self._view.replace_histogram_plot(histogram)

    def _input_changed(self, input_box, input_value):
        try:
            val = int(input_value)
        except ValueError:
            WarningMessageDialog.launch(["Invalid input. Should be an integer."])
            return

        bkgd1 = self._view.get_bkgd1()
        bkgd2 = self._view.get_bkgd2()
        t0 = self._view.get_t0()
        goodbin1 = self._view.get_goodbin1()
        goodbin2 = self._view.get_goodbin2()

        if input_box == "bkgd1" and val < bkgd2:
            self._view.set_new_lines(bkg1=val)

        if input_box == "bkgd2" and val > bkgd1:
            self._view.set_new_lines(bkg2=val)

        if input_box == "t0" and val > 0:
            self._view.set_new_lines(t0=val)

        if input_box == "goodbin1" and val < goodbin2:
            self._view.set_new_lines(goodbin1=val)

        if input_box == "goodbin2" and val > goodbin1:
            self._view.set_new_lines(goodbin2=val)

        self._model.store_focused_run_meta(self._view.get_histogram_label(), bkgd1, bkgd2, t0, goodbin1, goodbin2)

    def update(self):
        self.__editing = False

        if self._model.are_any_runs_focused() and self._model.is_run_histogram():
            self.__multiple = self._model.are_multiple_runs_focused()
            self._view.set_enabled(True, self.__multiple, self.__editing)

            if not self.__multiple:
                labels = self._model.get_focused_runs_histogram_labels()
                meta = list(self._model.get_focused_run_meta(labels[0]).items())[0][1]
                self._view.histogram = self._model.get_focused_run_histogram(labels[0])
                self._view.reset(meta[files.BACKGROUND_ONE_KEY], meta[files.BACKGROUND_TWO_KEY], meta[files.T0_KEY],
                                 meta[files.GOOD_BIN_ONE_KEY], meta[files.GOOD_BIN_TWO_KEY])

                self._view.add_histogram_labels(labels)
            else:
                pass
        else:
            self._view.set_blank()


class HistogramDisplayModel:
    def __init__(self, observer):
        self._data_context = MuonDataContext()
        self._focus_context = FocusContext()
        self._focus_context.subscribe(self)
        self._observer = observer
        self._focused_runs = self._focus_context.get_focused_runs()
        self._focused_runs_changed = False
        self._initial_run_meta = {}
        self._current_run_meta = {}

    def are_multiple_runs_focused(self):
        return len(self._focused_runs) > 1

    def are_any_runs_focused(self):
        return len(self._focused_runs) > 0

    def is_run_histogram(self):
        return files.file(self._focused_runs[0].file).DATA_FORMAT == files.Format.HISTOGRAM

    def get_initial_focused_run_data(self):
        pass

    def get_focused_runs_histogram_labels(self):
        return list(files.file(self._focused_runs[0].file).read_data().keys())

    def get_focused_run_histogram(self, histogram_label):
        return files.file(self._focused_runs[0].file).read_data()[histogram_label]

    def get_focused_run_meta(self, histogram):
        if histogram not in self._initial_run_meta.keys():
            self._initial_run_meta[histogram] = {run.id: {files.BACKGROUND_ONE_KEY: int(run.meta[files.BACKGROUND_ONE_KEY][histogram]),
                             files.BACKGROUND_TWO_KEY: int(run.meta[files.BACKGROUND_TWO_KEY][histogram]),
                             files.T0_KEY: int(run.meta[files.T0_KEY][histogram]),
                             files.GOOD_BIN_ONE_KEY: int(run.meta[files.GOOD_BIN_ONE_KEY][histogram]),
                             files.GOOD_BIN_TWO_KEY: int(run.meta[files.GOOD_BIN_TWO_KEY][histogram])}
                    for run in self._focused_runs}

        return self._initial_run_meta[histogram].copy()

    def get_focused_run_file_content(self):
        filename = self._focused_runs[0].file
        with open(filename) as f:
            file_content = f.read()
            return filename, file_content

    def reset_focused_run_meta(self):
        self._current_run_meta = self._initial_run_meta.copy()

    def store_focused_run_meta(self, histogram, bkgd1, bkgd2, t0, goodbin1, goodbin2):
        self._focused_runs_changed = True
        self._current_run_meta[histogram] = {run.id: {files.BACKGROUND_ONE_KEY: bkgd1,
                         files.BACKGROUND_TWO_KEY: bkgd2,
                         files.T0_KEY: t0,
                         files.GOOD_BIN_ONE_KEY: goodbin1,
                         files.GOOD_BIN_TWO_KEY: goodbin2}
                for run in self._focused_runs}

    def finish(self):
        if self._focused_runs_changed:
            for histogram in self._current_run_meta.keys():
                for run in self._focused_runs:
                    run.meta[files.BACKGROUND_ONE_KEY][histogram] = self._current_run_meta[histogram][run.id][files.BACKGROUND_ONE_KEY]
                    run.meta[files.BACKGROUND_TWO_KEY][histogram] = self._current_run_meta[histogram][run.id][files.BACKGROUND_TWO_KEY]
                    run.meta[files.T0_KEY][histogram] = self._current_run_meta[histogram][run.id][files.T0_KEY]
                    run.meta[files.GOOD_BIN_ONE_KEY][histogram] = self._current_run_meta[histogram][run.id][files.GOOD_BIN_ONE_KEY]
                    run.meta[files.GOOD_BIN_TWO_KEY][histogram] = self._current_run_meta[histogram][run.id][files.GOOD_BIN_TWO_KEY]

            for run in self._focused_runs:
                self._data_context.reload_run_by_id(run.id, stop_signal=True)

            self._initial_run_meta = self._current_run_meta.copy()

            self._data_context.send_signal()

    def update(self):
        self._initial_run_meta = {}
        self._focused_runs_changed = False
        self._focused_runs = self._focus_context.get_focused_runs()
        self._observer.update()
