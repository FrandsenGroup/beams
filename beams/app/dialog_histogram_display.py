
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

from app.util import widgets
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
        self.__initial = True
        self._initial_bkg1 = args[0]
        self._initial_bkg2 = args[1]
        self._initial_t0 = args[2]

        self.histogram = args[3]
        self.histogram_label = args[4]
        self._bkg1 = args[0]
        self._bkg2 = args[1]
        self._t0 = args[2]

        self.run_id = args[4]

        self._main = QtWidgets.QMainWindow()
        widget = QtWidgets.QWidget()
        self._new_layout = QtWidgets.QVBoxLayout(widget)

        self.radio_bkgd_one = QtWidgets.QRadioButton()
        self.radio_bkgd_two = QtWidgets.QRadioButton()
        self.radio_t0 = QtWidgets.QRadioButton()
        self.button_reset = widgets.StyleOneButton("Reset")
        self.button_save = widgets.StyleOneButton("Save")
        self.canvas = HistogramDisplayDialog.HistogramCanvas()
        self.check_editing = QtWidgets.QCheckBox()
        self.label_explanation = QtWidgets.QLabel()
        self.label_bkgd1 = QtWidgets.QLabel("Background Start")
        self.label_bkgd2 = QtWidgets.QLabel("Background End")
        self.label_t0 = QtWidgets.QLabel("T0")
        self.input_bkgd1 = QtWidgets.QLineEdit()
        self.input_bkgd2 = QtWidgets.QLineEdit()
        self.input_t0 = QtWidgets.QLineEdit()

        self._extent = None
        self._toolbar = HistogramDisplayDialog.HistogramToolbar(self.canvas, self._main)
        self._main.addToolBar(self._toolbar)
        self._set_widget_attributes()
        self._set_widget_dimensions()
        self._set_widget_tooltips()
        self._set_widget_layout()
        self.set_new_lines()

        self._main.setCentralWidget(widget)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._main)

        self._presenter = HistogramDisplayPresenter(self)

    def set_new_lines(self, bkg1=None, bkg2=None, t0=None, thick=False):
        bkg1_width = 1
        bkg2_width = 1
        t0_width = 1
        if bkg1 is not None:
            self._bkg1 = bkg1
            self.input_bkgd1.setText(str(bkg1))
            if thick:
                bkg1_width = 2
        if bkg2 is not None:
            self._bkg2 = bkg2
            self.input_bkgd2.setText(str(bkg2))
            if thick:
                bkg2_width = 2
        if t0 is not None:
            self._t0 = t0
            self.input_t0.setText(str(t0))
            if thick:
                t0_width = 2

        self._extent = self.canvas.canvas_axes.axis()
        self.canvas.canvas_axes.clear()
        self.canvas.canvas_axes.plot(self.histogram, linestyle='None', marker='s')
        self.canvas.canvas_axes.axvline(x=self._bkg1, linewidth=bkg1_width, color='r')
        self.canvas.canvas_axes.axvline(x=self._bkg2, linewidth=bkg2_width, color='r')
        self.canvas.canvas_axes.axvline(x=self._t0, linewidth=t0_width, color='g')

        if not self.__initial:
            self.canvas.canvas_axes.axis(self._extent)

        self.canvas.canvas_axes.figure.canvas.draw()

        self.__initial = False

    def reset(self):
        self._bkg1 = self._initial_bkg1
        self._bkg2 = self._initial_bkg2
        self._t0 = self._initial_t0

        self.input_bkgd1.setText(str(self._initial_bkg1))
        self.input_bkgd2.setText(str(self._initial_bkg2))
        self.input_t0.setText(str(self._initial_t0))

        self._extent = self.canvas.canvas_axes.axis()
        self.canvas.canvas_axes.clear()
        self.canvas.canvas_axes.plot(self.histogram, linestyle='None', marker='s')
        self.canvas.canvas_axes.axvline(x=self._bkg1, linewidth=1, color='r')
        self.canvas.canvas_axes.axvline(x=self._bkg2, linewidth=1, color='r')
        self.canvas.canvas_axes.axvline(x=self._t0, linewidth=1, color='g')
        self.canvas.canvas_axes.axis(self._extent)
        self.canvas.canvas_axes.figure.canvas.draw()

        return self._bkg1, self._bkg2, self._t0

    def _set_widget_tooltips(self):
        self.check_editing.setToolTip("Check to enable bin changes")

    def _set_widget_attributes(self):
        self.radio_bkgd_one.setChecked(True)
        self.set_enabled(False)

        message = "Before moving the bars manually below make sure you have deselected the zoom option in the toolbar.\n" \
                  "Then check the box to enable editing and select the bin you would like to change."
        self.label_explanation.setText(message)

        self.input_bkgd1.setText(str(self._bkg1))
        self.input_bkgd2.setText(str(self._bkg2))
        self.input_t0.setText(str(self._t0))

    def _set_widget_dimensions(self):
        self.button_reset.setFixedWidth(60)
        self.button_save.setFixedWidth(60)
        self.input_t0.setFixedWidth(30)
        self.input_bkgd1.setFixedWidth(30)
        self.input_bkgd2.setFixedWidth(30)

    def _set_widget_layout(self):
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

    def set_enabled(self, enabled):
        self.radio_bkgd_two.setEnabled(enabled)
        self.radio_bkgd_one.setEnabled(enabled)
        self.radio_t0.setEnabled(enabled)
        self.button_save.setEnabled(enabled)
        self.button_reset.setEnabled(enabled)
        self.label_bkgd2.setEnabled(enabled)
        self.label_bkgd1.setEnabled(enabled)
        self.label_t0.setEnabled(enabled)
        self.input_bkgd1.setEnabled(enabled)
        self.input_bkgd2.setEnabled(enabled)
        self.input_t0.setEnabled(enabled)

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
        self._histogram = self._view.histogram
        self._histogram_label = self._view.histogram_label

    def _set_callbacks(self):
        pass

    def _mouse_interaction(self):
        pass

    def _reset_clicked(self):
        pass

    def _save_clicked(self):
        pass

    def _editing_checked(self):
        pass

    def _option_changed(self):
        pass

    def _input_changed(self):
        pass

