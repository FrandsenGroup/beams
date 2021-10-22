
import logging

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure

from app.gui.dialogs.dialog_misc import FileDisplayDialog, WarningMessageDialog
from app.gui.gui import Panel, PanelPresenter
from app.model import files, services, domain
from app.util import qt_widgets, qt_constants


class HistogramPanel(Panel):
    class HistogramDisplay(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.figure.set_facecolor("#FFFFFF")
            self.canvas_axes = self.figure.add_subplot(111, label='Canvas')

    class HistogramToolbar(NavigationToolbar2QT):
        def _init_toolbar(self):
            pass

        def __init__(self, canvas, parent):
            super().__init__(canvas, parent)
            if 'locLabel' not in self.__dict__:
                self.locLabel = None

        # only display the buttons we need
        NavigationToolbar2QT.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            ('Save', 'Save the figure', 'filesave', 'save_figure'),
        )

    class SupportPanel(QtWidgets.QDockWidget):
        class Tree(QtWidgets.QTreeWidget):
            def __init__(self):
                super().__init__()
                self.__manager = HistogramPanel.SupportPanel.TreeManager(self)
                self.setHeaderHidden(True)
                self.setContextMenuPolicy(qt_constants.CustomContextMenu)
                self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
                self.setHorizontalScrollBarPolicy(qt_constants.ScrollBarAsNeeded)
                self.header().setMinimumSectionSize(600)
                self.header().setDefaultSectionSize(900)
                self.header().setStretchLastSection(False)
                self._set_callbacks()

            def _set_callbacks(self):
                self.customContextMenuRequested.connect(self._launch_menu)

            def _launch_menu(self, point):
                index = self.indexAt(point)

                if not index.isValid():
                    return

                item = self.itemAt(point)
                menu = item.menu(self.selectedItems())
                menu.exec_(self.mapToGlobal(point))

            def set_tree(self, tree):
                self.clear()
                self.addTopLevelItems(tree)

            def get_selected_run_ids(self):
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Selected)

                ids = []
                while iterator.value():
                    if isinstance(iterator.value().model, domain.Histogram):
                        ids.append(iterator.value().model.id)

                    iterator += 1

                return ids

            def get_selected_histograms(self):
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Selected)

                histograms = []
                while iterator.value():
                    if isinstance(iterator.value().model, domain.Histogram):
                        histograms.append(iterator.value().model)
                    iterator += 1
                return histograms

            def get_all_histograms(self):
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.IteratorFlag.All)

                histograms = []
                while iterator.value():
                    if isinstance(iterator.value().model, domain.Histogram):
                        histograms.append(iterator.value().model)
                    iterator += 1
                return histograms

        class TreeManager(PanelPresenter):
            def __init__(self, view):
                super().__init__(view)
                self.__view = view
                self.__logger = logging.getLogger("HistogramPanelTreeManager")
                self.__run_service = services.RunService()
                self.__fit_service = services.FitService()
                self.__file_service = services.FileService()

                self.__run_service.signals.added.connect(self.update)
                self.__run_service.signals.changed.connect(self.update)

            def _create_tree_model(self, run_datasets):
                run_nodes = []
                for dataset in run_datasets:
                    run_nodes.append(HistogramPanel.SupportPanel.RunNode(dataset))
                return run_nodes

            @QtCore.pyqtSlot()
            def update(self):
                self.__logger.debug("Accepted Signal")
                run_datasets = self.__run_service.get_loaded_runs()
                tree = self._create_tree_model(run_datasets)
                self.__view.set_tree(tree)

        class RunNode(QtWidgets.QTreeWidgetItem):
            def __init__(self, run_data):
                super(HistogramPanel.SupportPanel.RunNode, self).__init__([run_data.meta[files.TITLE_KEY]])
                self.model = run_data
                self.__selected_items = None

                if isinstance(run_data, domain.RunDataset):
                    if run_data.isLoaded and run_data.histograms:
                        for histogram in run_data.histograms.values():
                            self.addChild(HistogramPanel.SupportPanel.HistogramNode(histogram))

            def menu(self, items):
                self.__selected_items = items
                menu = QtWidgets.QMenu()
                menu.addAction("Plot", self._action_plot)
                menu.addAction("Save", self._action_save)
                return menu

            def _action_save(self):
                pass

            def _action_plot(self):
                pass

        class HistogramNode(QtWidgets.QTreeWidgetItem):
            def __init__(self, histogram):
                super(HistogramPanel.SupportPanel.HistogramNode, self).__init__([histogram.title])
                self.model = histogram
                self.__selected_items = None

            def menu(self, items):
                self.__selected_items = items
                menu = QtWidgets.QMenu()
                menu.addAction("Edit", self._action_edit)
                menu.addAction("Combine", self._action_combine)
                return menu

            def _action_combine(self):
                pass

            def _action_asymmetry(self):
                pass

            def _action_edit(self):
                pass

            def _action_write(self):
                pass

        def __init__(self):
            super().__init__()
            self.tree = HistogramPanel.SupportPanel.Tree()
            self.setTitleBarWidget(QtWidgets.QWidget())
            # self.setFixedWidth(350)
            self.setMinimumHeight(500)
            layout = QtWidgets.QVBoxLayout()

            self.see_file_button = qt_widgets.StyleOneButton("See File")
            self.reset_button = qt_widgets.StyleOneButton("Reset")
            self.save_button = qt_widgets.StyleTwoButton("Save")

            self.see_file_button.setToolTip('View file details')
            self.reset_button.setToolTip('Reset bins')
            self.save_button.setToolTip('Save edits')

            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(self.see_file_button)
            hbox.addWidget(self.reset_button)
            hbox.addWidget(self.save_button)
            layout.addLayout(hbox)

            layout.addWidget(self.tree)
            temp = QtWidgets.QWidget()
            temp.setLayout(layout)
            self.setWidget(temp)

    def __init__(self):
        super().__init__()
        self.support_panel = self.SupportPanel()
        self._main = QtWidgets.QMainWindow()
        widget = QtWidgets.QWidget()
        self._new_layout = QtWidgets.QVBoxLayout(widget)

        self.radio_bkgd_one = QtWidgets.QRadioButton()
        self.radio_bkgd_two = QtWidgets.QRadioButton()
        self.radio_t0 = QtWidgets.QRadioButton()
        self.radio_goodbin1 = QtWidgets.QRadioButton()
        self.radio_goodbin2 = QtWidgets.QRadioButton()
        self.canvas = self.HistogramDisplay()
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
        self._toolbar = self.HistogramToolbar(self.canvas, self._main)
        self._main.addToolBar(self._toolbar)
        self._set_widget_attributes()
        self._set_widget_dimensions()
        self._set_widget_tooltips()
        self._set_widget_layout()
        self._main.setCentralWidget(widget)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._main)

        self._presenter = HistogramPanelPresenter(self)
        self.set_blank()

        self.histogram = None
        self.histogram_label = None
        self.bkgd1 = None
        self.bkgd2 = None
        self.t0 = None
        self.goodbin1 = None
        self.goodbin2 = None

        self.__initial = True

    def createSupportPanel(self) -> QtWidgets.QDockWidget:
        return self.support_panel

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

        self.support_panel.reset_button.setAutoDefault(False)
        self.support_panel.save_button.setAutoDefault(False)
        self.support_panel.see_file_button.setAutoDefault(False)

    def _set_widget_dimensions(self):
        self.input_t0.setFixedWidth(30)
        self.input_bkgd1.setFixedWidth(30)
        self.input_bkgd2.setFixedWidth(30)
        self.input_goodbin1.setFixedWidth(30)
        self.input_goodbin2.setFixedWidth(30)

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
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_goodbin1)
        radio_layout.addWidget(self.input_goodbin1)
        radio_layout.addWidget(self.label_goodbin1)
        radio_layout.addSpacing(25)
        radio_layout.addWidget(self.radio_goodbin2)
        radio_layout.addWidget(self.input_goodbin2)
        radio_layout.addWidget(self.label_goodbin2)
        radio_layout.addStretch()

        radio_form = QtWidgets.QGroupBox("Edit")
        radio_form_layout = QtWidgets.QFormLayout()
        radio_form_layout.addWidget(self.label_explanation)
        radio_form_layout.addRow(radio_layout)
        radio_form.setLayout(radio_form_layout)
        radio_form.setMaximumHeight(120)

        self._new_layout.addWidget(radio_form)
        self._new_layout.addWidget(self.canvas)

    def replace_histogram_plot(self, histogram, bkgd1, bkgd2, t0, goodbin1, goodbin2):
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

        self.histogram_label = self.histogram_choices.currentText()
        self.histogram = histogram
        self.set_new_lines(new_histogram=True)

    def set_enabled(self, enabled, multiple=False, editing=False):
        if not enabled:
            self.set_blank()

        self.setEnabled(enabled)
        self.support_panel.save_button.setEnabled(enabled)
        self.support_panel.reset_button.setEnabled(enabled)
        self.support_panel.see_file_button.setEnabled(enabled)

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
            self.support_panel.see_file_button.setEnabled(False)
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
            self.support_panel.see_file_button.setEnabled(True)
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


class HistogramPanelPresenter(PanelPresenter):
    def __init__(self, view: Panel):
        super().__init__(view)
        self.__logger = logging.getLogger("HistogramPanelPresenter")
        self.__run_service = services.RunService()
        self.__alterations = {}
        self.__current_histogram = None
        self.__editing = False
        self.__multiple = False
        self.__pressed = False

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.support_panel.tree.itemSelectionChanged.connect(self._selection_changed)
        self._view.canvas.figure.canvas.mpl_connect('button_press_event', self._mouse_interaction)
        self._view.canvas.figure.canvas.mpl_connect('button_release_event', self._mouse_interaction)
        self._view.canvas.figure.canvas.mpl_connect('motion_notify_event', self._mouse_interaction)
        self._view.support_panel.reset_button.pressed.connect(self._reset_clicked)
        self._view.support_panel.save_button.pressed.connect(self._save_clicked)
        self._view.support_panel.see_file_button.pressed.connect(self._see_file_clicked)
        self._view.check_editing.stateChanged.connect(self._editing_checked)
        self._view.input_t0.returnPressed.connect(lambda: self._input_changed('t0', self._view.get_input_t0()))
        self._view.input_bkgd1.returnPressed.connect(lambda: self._input_changed('bkgd1', self._view.get_input_bkgd1()))
        self._view.input_bkgd2.returnPressed.connect(lambda: self._input_changed('bkgd2', self._view.get_input_bkgd2()))
        self._view.input_goodbin1.returnPressed.connect(lambda: self._input_changed('goodbin1', self._view.get_input_goodbin1()))
        self._view.input_goodbin2.returnPressed.connect(lambda: self._input_changed('goodbin2', self._view.get_input_goodbin2()))

    def _selection_changed(self):
        histograms = self._view.support_panel.tree.get_selected_histograms()

        if len(histograms) == 0:
            self._view.set_enabled(False)
            return

        self.__multiple = len(histograms) > 1

        for histogram in histograms:
            self.__current_histogram = histogram

            if histogram.id not in self.__alterations.keys():
                self.__alterations[histogram.id] = dict()
                self.__alterations[histogram.id][histogram.title] = {
                    files.BACKGROUND_ONE_KEY: histogram.background_start,
                    files.BACKGROUND_TWO_KEY: histogram.background_end,
                    files.GOOD_BIN_ONE_KEY: histogram.good_bin_start,
                    files.GOOD_BIN_TWO_KEY: histogram.good_bin_end,
                    files.T0_KEY: histogram.time_zero
                }
            elif histogram.title not in self.__alterations[histogram.id].keys():
                self.__alterations[histogram.id][histogram.title] = {
                    files.BACKGROUND_ONE_KEY: histogram.background_start,
                    files.BACKGROUND_TWO_KEY: histogram.background_end,
                    files.GOOD_BIN_ONE_KEY: histogram.good_bin_start,
                    files.GOOD_BIN_TWO_KEY: histogram.good_bin_end,
                    files.T0_KEY: histogram.time_zero
                }

        if not self.__multiple:
            self._view.replace_histogram_plot(self.__current_histogram,
                                              self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.BACKGROUND_ONE_KEY],
                                              self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.BACKGROUND_TWO_KEY],
                                              self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.T0_KEY],
                                              self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.GOOD_BIN_ONE_KEY],
                                              self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.GOOD_BIN_TWO_KEY])

        self._view.set_enabled(True, self.__multiple, self.__editing)

    def _mouse_interaction(self, event):
        if not self.__editing:
            return

        if self.__multiple:
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

            self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.BACKGROUND_ONE_KEY] = bkgd1
            self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.BACKGROUND_TWO_KEY] = bkgd2
            self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.T0_KEY] = t0
            self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.GOOD_BIN_ONE_KEY] = goodbin1
            self.__alterations[self.__current_histogram.id][self.__current_histogram.title][files.GOOD_BIN_TWO_KEY] = goodbin2

        elif event.button is None and self.__pressed:
            self.__pressed = False

    def _reset_clicked(self):
        for histogram in self._view.support_panel.tree.get_selected_histograms():
            self.__alterations[histogram.id][histogram.title][files.BACKGROUND_ONE_KEY] = histogram.background_start
            self.__alterations[histogram.id][histogram.title][files.BACKGROUND_TWO_KEY] = histogram.background_end
            self.__alterations[histogram.id][histogram.title][files.T0_KEY] = histogram.time_zero
            self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_ONE_KEY] = histogram.good_bin_start
            self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_TWO_KEY] = histogram.good_bin_end

        self._view.reset(self.__current_histogram.background_start,
                         self.__current_histogram.background_end,
                         self.__current_histogram.time_zero,
                         self.__current_histogram.good_bin_start,
                         self.__current_histogram.good_bin_end)

    def _save_clicked(self):
        altered_run_ids = []
        for histogram in self._view.support_panel.tree.get_all_histograms():
            if histogram.id in self.__alterations.keys() and histogram.title in self.__alterations[histogram.id].keys():
                if histogram.background_start != self.__alterations[histogram.id][histogram.title][files.BACKGROUND_ONE_KEY] \
                        or histogram.background_end != self.__alterations[histogram.id][histogram.title][files.BACKGROUND_TWO_KEY] \
                        or histogram.time_zero != self.__alterations[histogram.id][histogram.title][files.T0_KEY] \
                        or histogram.good_bin_start != self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_ONE_KEY] \
                        or histogram.good_bin_end != self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_TWO_KEY]:
                    altered_run_ids.append(histogram.id)
                else:
                    continue

                histogram.background_start = self.__alterations[histogram.id][histogram.title][files.BACKGROUND_ONE_KEY]
                histogram.background_end = self.__alterations[histogram.id][histogram.title][files.BACKGROUND_TWO_KEY]
                histogram.time_zero = self.__alterations[histogram.id][histogram.title][files.T0_KEY]
                histogram.good_bin_start = self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_ONE_KEY]
                histogram.good_bin_end = self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_TWO_KEY]

        self.__run_service.recalculate_asymmetries(altered_run_ids)

    def _editing_checked(self):
        self.__editing = self._view.is_editing()
        self._view.set_enabled(True, self.__multiple, self.__editing)

    def _see_file_clicked(self):
        run = self.__run_service.get_runs_by_ids([self.__current_histogram.id])[0]
        filename = run.file.file_path

        with open(filename) as f:
            file_content = f.read()

        FileDisplayDialog.launch([filename, file_content])

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
            bkgd1 = val

        if input_box == "bkgd2" and val > bkgd1:
            self._view.set_new_lines(bkg2=val)
            bkgd2 = val

        if input_box == "t0" and val > 0:
            self._view.set_new_lines(t0=val)
            t0 = val

        if input_box == "goodbin1" and val < goodbin2:
            self._view.set_new_lines(goodbin1=val)
            goodbin1 = val

        if input_box == "goodbin2" and val > goodbin1:
            self._view.set_new_lines(goodbin2=val)
            goodbin2 = val

        for histogram in self._view.support_panel.tree.get_selected_histograms():
            self.__alterations[histogram.id][histogram.title][files.BACKGROUND_ONE_KEY] = bkgd1
            self.__alterations[histogram.id][histogram.title][files.BACKGROUND_TWO_KEY] = bkgd2
            self.__alterations[histogram.id][histogram.title][files.T0_KEY] = t0
            self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_ONE_KEY] = goodbin1
            self.__alterations[histogram.id][histogram.title][files.GOOD_BIN_TWO_KEY] = goodbin2

