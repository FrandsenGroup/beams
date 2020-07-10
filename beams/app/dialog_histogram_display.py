
import traceback

from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

from app.util import widgets
from app.model import files
from app.dialog_misc import WarningMessageDialog, FileDisplayDialog
from app.model.model import MuonDataContext


# noinspection PyArgumentList
class HistogramDisplayDialog(QtWidgets.QDialog):
    class HistogramCanvas(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
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

    def __init__(self, args):
        super(HistogramDisplayDialog, self).__init__()
        self._histograms = args[8]
        self._meta = args[10]

        self._initial_values = {title: {files.T0_KEY: int(self._meta[files.T0_KEY][title]),
                                        files.BACKGROUND_ONE_KEY: int(self._meta[files.BACKGROUND_ONE_KEY][title]),
                                        files.BACKGROUND_TWO_KEY: int(self._meta[files.BACKGROUND_TWO_KEY][title]),
                                        files.GOOD_BIN_ONE_KEY: int(self._meta[files.GOOD_BIN_ONE_KEY][title]),
                                        files.GOOD_BIN_TWO_KEY: int(self._meta[files.GOOD_BIN_TWO_KEY][title])}
                                for title in self._histograms}

        self._current_values = {title: {files.T0_KEY: int(self._meta[files.T0_KEY][title]),
                                        files.BACKGROUND_ONE_KEY: int(self._meta[files.BACKGROUND_ONE_KEY][title]),
                                        files.BACKGROUND_TWO_KEY: int(self._meta[files.BACKGROUND_TWO_KEY][title]),
                                        files.GOOD_BIN_ONE_KEY: int(self._meta[files.GOOD_BIN_ONE_KEY][title]),
                                        files.GOOD_BIN_TWO_KEY: int(self._meta[files.GOOD_BIN_TWO_KEY][title])}
                                for title in self._histograms}

        self.__initial = True

        self.histogram = args[3]
        self.histogram_label = args[5]
        self._histograms = args[8]
        self._file = args[9]

        self.run_id = args[4]

        self._main = QtWidgets.QMainWindow()
        widget = QtWidgets.QWidget()
        self._new_layout = QtWidgets.QVBoxLayout(widget)

        self.radio_bkgd_one = QtWidgets.QRadioButton()
        self.radio_bkgd_two = QtWidgets.QRadioButton()
        self.radio_t0 = QtWidgets.QRadioButton()
        self.radio_goodbin1 = QtWidgets.QRadioButton()
        self.radio_goodbin2 = QtWidgets.QRadioButton()
        self.button_reset = widgets.StyleOneButton("Reset")
        self.button_save = widgets.StyleOneButton("Save")
        self.button_see_file = widgets.StyleOneButton("See File")
        self.canvas = HistogramDisplayDialog.HistogramCanvas()
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
        self._toolbar = HistogramDisplayDialog.HistogramToolbar(self.canvas, self._main)
        self._main.addToolBar(self._toolbar)
        self._set_widget_attributes()
        self._set_widget_dimensions()
        self._set_widget_tooltips()
        self._set_widget_layout()
        self._main.setCentralWidget(widget)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._main)

        self.set_new_lines()
        self._presenter = HistogramDisplayPresenter(self)

    def set_new_lines(self, bkg1=None, bkg2=None, t0=None, goodbin1=None, goodbin2=None, thick=False, new_histogram=None):
        bkg1_width = 1
        bkg2_width = 1
        t0_width = 1
        goodbin1_width = 1
        goodbin2_width = 1

        if bkg1 is not None:
            self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY] = bkg1
            self.input_bkgd1.setText(str(bkg1))
            if thick:
                bkg1_width = 2
        if bkg2 is not None:
            self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY] = bkg2
            self.input_bkgd2.setText(str(bkg2))
            if thick:
                bkg2_width = 2
        if t0 is not None:
            self._current_values[self.histogram_label][files.T0_KEY] = t0
            self.input_t0.setText(str(t0))
            if thick:
                t0_width = 2
        if goodbin1 is not None:
            self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY] = goodbin1
            self.input_goodbin1.setText(str(goodbin1))
            if thick:
                goodbin1_width = 2
        if goodbin2 is not None:
            self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY] = goodbin2
            self.input_goodbin2.setText(str(goodbin2))
            if thick:
                goodbin2_width = 2

        self._extent = self.canvas.canvas_axes.axis()
        self.canvas.canvas_axes.clear()
        # self.canvas.canvas_axes.bar(x=range(len(self.histogram)), height=self.histogram)
        # self.canvas.canvas_axes.hist(range(len(self.histogram)), bins=int(len(self.histogram)/10), weights=self.histogram)
        self.canvas.canvas_axes.plot(self.histogram, linestyle='None', marker='s')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY], linewidth=bkg1_width, color='r')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY], linewidth=bkg2_width, color='r')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.T0_KEY], linewidth=t0_width, color='g')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY], linewidth=goodbin1_width, color='b')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY], linewidth=goodbin2_width, color='b')

        if not self.__initial and new_histogram is None:
            self.canvas.canvas_axes.axis(self._extent)

        self.canvas.canvas_axes.figure.canvas.draw()

        self.__initial = False

    def reset(self):
        self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY] = self._initial_values[self.histogram_label][files.BACKGROUND_ONE_KEY]
        self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY] = self._initial_values[self.histogram_label][files.BACKGROUND_TWO_KEY]
        self._current_values[self.histogram_label][files.T0_KEY] = self._initial_values[self.histogram_label][files.T0_KEY]
        self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY] = self._initial_values[self.histogram_label][files.GOOD_BIN_ONE_KEY]
        self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY] = self._initial_values[self.histogram_label][files.GOOD_BIN_TWO_KEY]

        self.input_bkgd1.setText(str(self._initial_values[self.histogram_label][files.BACKGROUND_ONE_KEY]))
        self.input_bkgd2.setText(str(self._initial_values[self.histogram_label][files.BACKGROUND_TWO_KEY]))
        self.input_t0.setText(str(self._initial_values[self.histogram_label][files.T0_KEY]))
        self.input_goodbin1.setText(str(self._initial_values[self.histogram_label][files.GOOD_BIN_ONE_KEY]))
        self.input_goodbin2.setText(str(self._initial_values[self.histogram_label][files.GOOD_BIN_TWO_KEY]))

        self._extent = self.canvas.canvas_axes.axis()
        self.canvas.canvas_axes.clear()
        self.canvas.canvas_axes.plot(self.histogram, linestyle='None', marker='s')
        # self.canvas.canvas_axes.bar(x=range(len(self.histogram)), height=self.histogram)
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY], linewidth=1, color='r')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY], linewidth=1, color='r')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.T0_KEY], linewidth=1, color='g')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY], linewidth=1, color='b')
        self.canvas.canvas_axes.axvline(x=self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY], linewidth=1, color='b')
        self.canvas.canvas_axes.axis(self._extent)
        self.canvas.canvas_axes.figure.canvas.draw()

        return self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY], self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY], self._current_values[self.histogram_label][files.T0_KEY], self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY], self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY]

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
        self.histogram_choices.addItems(self._histograms)

        self.input_bkgd1.setText(str(self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY]))
        self.input_bkgd2.setText(str(self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY]))
        self.input_t0.setText(str(self._current_values[self.histogram_label][files.T0_KEY]))
        self.input_goodbin1.setText(str(self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY]))
        self.input_goodbin2.setText(str(self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY]))

        self.histogram_choices.currentTextChanged.connect(self._replace_histogram_plot)
        self.button_see_file.released.connect(self._see_file_clicked)

    def _set_widget_dimensions(self):
        self.button_reset.setFixedWidth(60)
        self.button_save.setFixedWidth(60)
        self.button_see_file.setFixedWidth(60)
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
        radio_layout.addSpacing(5)
        radio_layout.addWidget(self.button_save)
        radio_layout.addStretch()

        radio_form = QtWidgets.QGroupBox("Edit")
        radio_form_layout = QtWidgets.QFormLayout()
        radio_form_layout.addWidget(self.label_explanation)
        radio_form_layout.addRow(radio_layout)
        radio_form.setLayout(radio_form_layout)

        self._new_layout.addWidget(radio_form)
        self._new_layout.addWidget(self.canvas)

    def _replace_histogram_plot(self):
        self.histogram_label = self.histogram_choices.currentText()
        self.histogram = self._file.read_data()[self.histogram_label]
        self.set_new_lines(new_histogram=True)

    def _see_file_clicked(self):
        filename = self._file.file_path
        with open(filename) as f:
            file_content = f.read()
        FileDisplayDialog.launch([filename, file_content])

    def set_enabled(self, enabled):
        self.radio_bkgd_two.setEnabled(enabled)
        self.radio_bkgd_one.setEnabled(enabled)
        self.radio_t0.setEnabled(enabled)
        self.radio_goodbin2.setEnabled(enabled)
        self.radio_goodbin1.setEnabled(enabled)
        self.button_save.setEnabled(enabled)
        self.button_reset.setEnabled(enabled)
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
        return self._current_values[self.histogram_label][files.BACKGROUND_ONE_KEY]

    def get_bkgd2(self):
        return self._current_values[self.histogram_label][files.BACKGROUND_TWO_KEY]

    def get_t0(self):
        return self._current_values[self.histogram_label][files.T0_KEY]

    def get_goodbin1(self):
        return self._current_values[self.histogram_label][files.GOOD_BIN_ONE_KEY]

    def get_goodbin2(self):
        return self._current_values[self.histogram_label][files.GOOD_BIN_TWO_KEY]

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

    @staticmethod
    def launch(args):
        dialog = HistogramDisplayDialog(args)
        return dialog.exec()


class HistogramDisplayPresenter:
    def __init__(self, view: HistogramDisplayDialog):
        self.__pressed = False
        self.__editing = False
        self._view = view
        self._context = MuonDataContext()
        self._run = self._context.get_run_by_id(self._view.run_id)
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.canvas.figure.canvas.mpl_connect('button_press_event', self._mouse_interaction)
        self._view.canvas.figure.canvas.mpl_connect('button_release_event', self._mouse_interaction)
        self._view.canvas.figure.canvas.mpl_connect('motion_notify_event', self._mouse_interaction)
        self._view.button_reset.pressed.connect(self._reset_clicked)
        self._view.button_save.pressed.connect(self._save_clicked)
        self._view.check_editing.stateChanged.connect(self._editing_checked)
        self._view.input_t0.returnPressed.connect(lambda: self._input_changed('t0', self._view.get_input_t0()))
        self._view.input_bkgd1.returnPressed.connect(lambda: self._input_changed('bkgd1', self._view.get_input_bkgd1()))
        self._view.input_bkgd2.returnPressed.connect(lambda: self._input_changed('bkgd2', self._view.get_input_bkgd2()))
        self._view.input_goodbin1.returnPressed.connect(lambda: self._input_changed('goodbin1', self._view.get_input_goodbin1()))
        self._view.input_goodbin2.returnPressed.connect(lambda: self._input_changed('goodbin2', self._view.get_input_goodbin2()))

    def _mouse_interaction(self, event):
        if not self.__editing:
            return

        if event.button is not None:
            self.__pressed = True

            thick = True if event.name != 'button_release_event' else False

            if self._view.is_bkgd1() and self._view.get_bkgd2() > event.xdata > 0:
                self._view.set_new_lines(bkg1=int(event.xdata), thick=thick)

            elif self._view.is_bkgd2() and event.xdata > self._view.get_bkgd1():
                self._view.set_new_lines(bkg2=int(event.xdata), thick=thick)

            elif self._view.is_t0() and event.xdata > 0:
                self._view.set_new_lines(t0=int(event.xdata), thick=thick)

            elif self._view.is_goodbin1() and event.xdata > 0:
                self._view.set_new_lines(goodbin1=int(event.xdata), thick=thick)

            elif self._view.is_goodbin2() and event.xdata > 0:
                self._view.set_new_lines(goodbin2=int(event.xdata), thick=thick)

        elif event.button is None and self.__pressed:
            self.__pressed = False

    def _reset_clicked(self):
        self._view.reset()

    def _save_clicked(self):
        label = self._view.get_histogram_label()
        self._run.meta[files.BACKGROUND_ONE_KEY][label] = self._view.get_bkgd1()
        self._run.meta[files.BACKGROUND_TWO_KEY][label] = self._view.get_bkgd2()
        self._run.meta[files.T0_KEY][label] = self._view.get_t0()
        self._run.meta[files.GOOD_BIN_ONE_KEY][label] = self._view.get_goodbin1()
        self._run.meta[files.GOOD_BIN_TWO_KEY][label] = self._view.get_goodbin2()
        self._view.done(0)
        self._context.reload_run_by_id(self._run.id)

    def _editing_checked(self):
        self.__editing = self._view.is_editing()
        self._view.set_enabled(self.__editing)

    def _input_changed(self, input_box, input_value):
        try:
            val = int(input_value)
        except ValueError:
            WarningMessageDialog.launch(["Invalid input. Should be an integer."])
            return

        if input_box == "bkgd1" and val < self._view.get_input_bkgd2():
            self._view.set_new_lines(bkg1=val)

        if input_box == "bkgd2" and val > self._view.get_input_bkgd1():
            self._view.set_new_lines(bkg2=val)

        if input_box == "t0" and val > 0:
            self._view.set_new_lines(t0=val)

        if input_box == "goodbin1" and val < self._view.get_input_goodbin2():
            self._view.set_new_lines(goodbin1=val)

        if input_box == "goodbin2" and val > self._view.get_input_goodbin1():
            self._view.set_new_lines(goodbin2=val)

