import logging
import re
from collections import OrderedDict
from concurrent import futures
from functools import partial

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from app.gui.dialogs.dialog_misc import WarningMessageDialog, LoadingDialog
from app.gui.dialogs.dialog_write_fit import WriteFitDialog
from app.util import qt_widgets, qt_constants
from app.model import objects, fit, files, services
from app.gui.gui import PanelPresenter, Panel


class FittingPanel(Panel):
    # __NAME_COLUMN = 0
    __VALUE_COLUMN = 0
    __LOWER_COLUMN = 1
    __UPPER_COLUMN = 2
    __FIXED_COLUMN = 3
    __GLOBAL_COLUMN = 4

    class SupportPanel(QtWidgets.QDockWidget):
        class Tree(QtWidgets.QTreeWidget):
            def __init__(self):
                super().__init__()
                self.__manager = FittingPanel.SupportPanel.TreeManager(self)
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

                actions = item.get_actions(self.selectedItems())
                menu = QtWidgets.QMenu()

                for action in actions:
                    menu.addAction(action[0], partial(action[1], self.selectedItems(), self))

                menu.exec_(self.mapToGlobal(point))

            def set_tree(self, tree):
                self.clear()
                self.addTopLevelItems(tree)

            def get_run_ids(self):
                # Suppressing inspection because it doesn't recognize 'self' as a QTreeWidget
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Checked)

                ids = []
                while iterator.value():
                    if isinstance(iterator.value().model, objects.FitDataset):
                        ids.append(iterator.value().model.id)

                    iterator += 1

                return ids

            def get_names(self):
                # Suppressing inspection because it doesn't recognize 'self' as a QTreeWidget
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Checked)

                ids = []
                while iterator.value():
                    if isinstance(iterator.value().model, objects.FitDataset):
                        ids.append(iterator.value().model.id)

                    iterator += 1

                return ids

            def get_selected_data(self):
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Selected)

                while iterator.value():
                    if isinstance(iterator.value().model, objects.Fit) or isinstance(iterator.value().model, objects.FitDataset):
                        return iterator.value().model
                    iterator += 1

        class TreeManager(PanelPresenter):
            def __init__(self, view):
                super().__init__(view)
                self.__view = view
                self.__logger = logging.getLogger("FittingPanelTreeManager")
                self.__run_service = services.RunService()
                self.__fit_service = services.FitService()
                self.__file_service = services.FileService()
                self.__run_service.signals.added.connect(self.update)
                self.__fit_service.signals.added.connect(self.update)
                self.__run_service.signals.changed.connect(self.update)
                self.__fit_service.signals.changed.connect(self.update)
                self.__view.itemChanged.connect(self._item_renamed)

            def _item_renamed(self, node, index):
                node.model.title = node.text(index)

            def _create_tree_model(self, fit_datasets):
                fit_dataset_nodes = []
                for dataset in fit_datasets:
                    fit_dataset_nodes.append(FittingPanel.SupportPanel.FitDatasetNode(dataset))
                return fit_dataset_nodes

            @QtCore.pyqtSlot()
            def update(self):
                fit_datasets = self.__fit_service.get_fit_datasets()
                tree = self._create_tree_model(fit_datasets)
                self.__view.set_tree(tree)

        class FitDatasetNode(QtWidgets.QTreeWidgetItem):
            def __init__(self, dataset):
                super().__init__([dataset.id])
                self.model = dataset
                self.__selected_items = None
                self.__fit_service = services.FitService()
                self.__parent = None
                self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)
                if isinstance(dataset, objects.FitDataset):
                    for fit_data in dataset.fits.values():
                        self.addChild(FittingPanel.SupportPanel.FitNode(fit_data))

            def get_actions(self, items):
                actions = [
                    ("Rename", self._action_rename),
                    ("Remove", self._action_remove),
                    # ("Expand", self._action_expand)
                ]

                if len(items) == 1:
                    actions.append(("Save", self._action_save))

                return actions

            def _action_rename(self, _, parent):
                parent.editItem(self)

            def _action_save(self, items, parent):
                WriteFitDialog.launch(dataset=items[0].model)

            def _action_remove(self, items, _):
                self.__fit_service.remove_dataset([item.model.id for item in items])

            def _action_expand(self, items, _):
                for item in items:
                    item.setExpanded(not self.isExpanded())

        class FitNode(QtWidgets.QTreeWidgetItem):
            def __init__(self, fit_data):
                super().__init__([fit_data.title])
                self.model = fit_data

                self.setFlags(self.flags() | QtCore.Qt.ItemFlag.ItemIsEditable)

            def get_actions(self, items):
                actions = [
                    ("Rename", self._action_rename)
                ]

                if len({id(item.parent()) for item in items}) == 1:
                    actions.append(("Save", self._action_save))

                return actions

            def _action_rename(self, items, parent):
                parent.editItem(self)

            def _action_save(self, items, parent):

                dataset = objects.FitDataset()
                dataset.fits = {i.model.id: i.model for i in items}
                dataset.flags = items[0].parent().model.flags

                WriteFitDialog.launch(dataset=dataset)

        def __init__(self):
            super().__init__()
            # TODO How to set it up?
            #   we want to be able to save a set of fits using some meta attribute as a prefix.
            #   just have two dialogs that come up when it is a single fit vs a set of fits.
            #   When saving fit dataset they should have an option of four formats to save the set as
            #   short, verbose, all to a directory with prefix, same but in a zip. Maybe we could have a
            #   window which gives a preview.
            # TODO We need to do a similar thing with everything else because the current write button doesn't
            #   contextually make much sense so lets just have right-click save options for all items in the
            #   support panels.

            self.tree = FittingPanel.SupportPanel.Tree()
            self.setTitleBarWidget(QtWidgets.QWidget())
            main_layout = QtWidgets.QVBoxLayout()

            self.new_button = qt_widgets.StyleTwoButton("New Empty Fit")
            self.reset_button = qt_widgets.StyleOneButton("Reset")
            self.button_lookup_folder = qt_widgets.StyleTwoButton("Folder")

            self.new_button.setToolTip('Create a new empty fit')
            self.button_lookup_folder.setToolTip('Select folder')

            self.input_file_name = QtWidgets.QLineEdit()
            self.input_folder_name = QtWidgets.QLineEdit()

            self.group_save_results = QtWidgets.QGroupBox("Save")

            self.button_lookup_folder.setFixedWidth(60)

            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(self.new_button)
            main_layout.addLayout(hbox)

            main_layout.addWidget(self.tree)
            temp = QtWidgets.QWidget()
            temp.setLayout(main_layout)
            self.setWidget(temp)

    class FitCanvas(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.canvas_axes = self.figure.add_subplot()

    class PlotDisplay(FigureCanvas):
        def __init__(self, settings):
            self._draw_pending = True
            self._is_drawing = True
            self._settings = settings

            FigureCanvas.__init__(self, Figure())
            axes = self.figure.subplots(1, 1)
            self.figure.set_facecolor("#ffffff")
            self.axes_time = axes

            self.set_blank()

        def set_blank(self):
            self.axes_time.clear()
            title_font_size = 12
            self.axes_time.spines['right'].set_visible(False)
            self.axes_time.spines['top'].set_visible(False)
            self.axes_time.spines['left'].set_visible(False)
            self.axes_time.spines['bottom'].set_visible(False)
            self.axes_time.set_xlabel("Select runs to see live asymmetry and fit.",
                                      fontsize=title_font_size)
            self.axes_time.xaxis.label.set_color("#c0c0c0")
            self.axes_time.tick_params(axis='x', colors='white')
            self.axes_time.tick_params(axis='y', colors='white')
            self.axes_time.set_facecolor("#ffffff")

        def set_style(self, remove_legend):
            self.axes_time.tick_params(axis='x', colors='black')
            self.axes_time.tick_params(axis='y', colors='black')

            title_font_size = 12
            self.axes_time.spines['right'].set_visible(False)
            self.axes_time.spines['top'].set_visible(False)
            self.axes_time.spines['left'].set_visible(True)
            self.axes_time.spines['bottom'].set_visible(True)
            self.axes_time.set_xlabel("Time (" + chr(956) + "s)", fontsize=title_font_size)
            self.axes_time.set_ylabel("Asymmetry", fontsize=title_font_size)
            self.axes_time.xaxis.label.set_color("#000000")
            self.axes_time.set_facecolor("#ffffff")
            self.axes_time.legend(loc='upper right')
            self.figure.tight_layout()

        def plot_asymmetry(self, time, asymmetry, uncertainty, fit, color, marker_color, line_color, errorbar_color,
                           fit_color, linestyle, marker, errorbar_style, fillstyle, line_width, marker_size,
                           errorbar_width,
                           fit_linestyle, label):

            marker_color = color if marker_color == 'Default' else marker_color
            line_color = color if line_color == 'Default' else line_color
            errorbar_color = color if errorbar_color == 'Default' else errorbar_color
            marker_face_color = marker_color if fillstyle != 'none' else 'none'
            fit_color = color if fit_color == 'Default' else fit_color

            if uncertainty is not None:
                self.axes_time.errorbar(time, asymmetry, uncertainty, mfc=marker_face_color, mec=marker_color,
                                        color=color, linestyle=linestyle, marker=marker, fillstyle=fillstyle,
                                        linewidth=line_width, markersize=marker_size,
                                        elinewidth=errorbar_width,
                                        ecolor=errorbar_color)

            else:
                self.axes_time.plot(time, asymmetry, mfc=marker_face_color, mec=marker_color, color=color,
                                    linestyle=linestyle, marker=marker, fillstyle=fillstyle,
                                    linewidth=line_width,
                                    markersize=marker_size, label=label)

        def set_asymmetry_plot_limits(self, max_asymmetry, min_asymmetry):
            if not self._settings.is_asymmetry_auto():
                try:
                    y_min = self._settings.get_min_asymmetry()
                    y_max = self._settings.get_max_asymmetry()
                except ValueError:
                    WarningMessageDialog.launch(["Invalid asymmetry limits."])
                    return
                self.axes_time.set_ylim(y_min, y_max)
            else:
                y_min = min_asymmetry - abs(min_asymmetry * 0.1)
                y_max = max_asymmetry + abs(max_asymmetry * 0.1)
                self.axes_time.set_ylim(y_min, y_max)
                self._settings.set_min_asymmetry(y_min)
                self._settings.set_max_asymmetry(y_max)

            try:
                x_min = self._settings.get_min_time()
                x_max = self._settings.get_max_time()
            except ValueError:
                WarningMessageDialog.launch(["Invalid asymmetry limits."])
                return
            self.axes_time.set_xlim(x_min, x_max)

        def finish_plotting(self, remove_legend=False):
            self.set_style(remove_legend)
            self.axes_time.figure.canvas.draw()

        def start_plotting(self):
            self.axes_time.clear()

        def set_full_blank(self):
            self.setEnabled(False)
            self.set_blank()
            self.axes_time.figure.canvas.draw()

    class PlotControl(QtWidgets.QWidget):
        def __init__(self):
            QtWidgets.QWidget.__init__(self)
            # self.setTitleBarWidget(QtWidgets.QWidget())

            # self._full_widget = QtWidgets.QWidget()

            self._label_slider_bin = QtWidgets.QLabel('')
            self._label_input_bin = QtWidgets.QLabel('Time Bins (ns)')

            self.slider_bin = QtWidgets.QSlider(qt_constants.Horizontal)
            self.input_bin = QtWidgets.QLineEdit()

            self.slider_bin.setToolTip('Time bins (ns)')

            self._label_time = QtWidgets.QLabel('Time')
            self._label_time_xmin = QtWidgets.QLabel('XMin')
            self._label_time_xmax = QtWidgets.QLabel('XMax')
            self._label_time_ymin = QtWidgets.QLabel('YMin')
            self._label_time_ymax = QtWidgets.QLabel('YMax')
            self._label_time_yauto = QtWidgets.QLabel('Auto Y')

            self.input_time_xmin = QtWidgets.QLineEdit()
            self.input_time_xmax = QtWidgets.QLineEdit()

            self.input_time_ymin = QtWidgets.QLineEdit()
            self.input_time_ymax = QtWidgets.QLineEdit()
            self.check_time_yauto = QtWidgets.QCheckBox()

            self._set_widget_attributes()
            self._set_widget_tooltips()
            self._set_widget_dimensions()
            self._set_widget_layout()

            # self.setWidget(self._full_widget)

        def _set_widget_attributes(self):
            self.check_time_yauto.setChecked(True)

            self.input_time_xmin.setText("0")
            self.input_time_xmax.setText("8")
            self.input_time_ymin.setText("-0.3")
            self.input_time_ymax.setText("-0.5")

            self.input_time_ymin.setEnabled(False)
            self.input_time_ymax.setEnabled(False)

            self.slider_bin.setMinimum(0)
            self.slider_bin.setMaximum(500)
            self.slider_bin.setValue(150)
            self.slider_bin.setTickPosition(QtWidgets.QSlider.TicksBothSides)
            self.slider_bin.setTickInterval(20)

            self.input_bin.setText(str(self.slider_bin.value()))
            self.input_bin.returnPressed.connect(lambda: self._update_bin(False))
            self.slider_bin.sliderMoved.connect(lambda: self._update_bin(True))

        def _set_widget_tooltips(self):
            pass

        def _set_widget_dimensions(self):
            box_size = 80
            self.input_time_xmin.setMaximumWidth(box_size)
            self.input_time_xmax.setMaximumWidth(box_size)
            self.input_time_ymin.setMaximumWidth(box_size)
            self.input_time_ymax.setMaximumWidth(box_size)
            self.input_bin.setFixedWidth(50)

        def _set_widget_layout(self):
            main_layout = QtWidgets.QVBoxLayout()

            row_1 = QtWidgets.QHBoxLayout()
            row_1.addWidget(self._label_time_xmin)
            row_1.addWidget(self.input_time_xmin)
            row_1.addWidget(self._label_time_xmax)
            row_1.addWidget(self.input_time_xmax)
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

            editor_layout = QtWidgets.QHBoxLayout()
            editor_layout.addWidget(time_form)

            self.setLayout(main_layout)

        def _update_bin(self, slider_is_most_accurate):
            if slider_is_most_accurate:
                self.input_bin.setText(str(self.slider_bin.value()))
            else:
                self.slider_bin.setValue(int(float(self.input_bin.text())))

        def get_max_time(self):
            return float(self.input_time_xmax.text())

        def get_min_time(self):
            return float(self.input_time_xmin.text())

        def get_max_asymmetry(self):
            return float(self.input_time_ymax.text())

        def get_min_asymmetry(self):
            return float(self.input_time_ymin.text())

        def get_bin_from_input(self):
            return float(self.input_bin.text())

        def get_bin_from_slider(self):
            return float(self.slider_bin.value())

        def is_asymmetry_auto(self):
            return self.check_time_yauto.isChecked()

        def set_enabled_asymmetry_auto(self, enabled):
            self.input_time_ymin.setEnabled(enabled)
            self.input_time_ymax.setEnabled(enabled)

        def set_max_time(self, value):
            self.input_time_xmax.setText('{0:.3f}'.format(value))

        def set_min_time(self, value):
            self.input_time_xmin.setText('{0:.3f}'.format(value))

        def set_max_asymmetry(self, value):
            self.input_time_ymax.setText('{0:.3f}'.format(value))

        def set_min_asymmetry(self, value):
            self.input_time_ymin.setText('{0:.3f}'.format(value))

        def set_bin_input(self, value):
            self.input_bin.setText(str(value))

        def set_bin_slider(self, value):
            self.slider_bin.setValue(int(value))

    class ParameterTable(QtWidgets.QTabWidget):
        VALUE_COLUMN = 0
        MIN_COLUMN = 1
        MAX_COLUMN = 2
        FIXED_COLUMN = 3
        GLOBAL_COLUMN = 0
        FIXED_RUN_COLUMN = 1
        FIXED_VALUE_COLUMN = 2
        OUTPUT_VALUE_COLUMN = 0
        UNCERTAINTY_COLUMN = 1

        def __init__(self):
            super(FittingPanel.ParameterTable, self).__init__()
            self.config_table = QtWidgets.QTableWidget()
            self.batch_table = QtWidgets.QTableWidget()
            self.output_table = QtWidgets.QTableWidget()

            self.addTab(self.config_table, "Config")
            self.addTab(self.batch_table, "Batch")
            self.addTab(self.output_table, "Output")

            self._set_attributes()

        def _set_attributes(self):
            self.config_table.setColumnCount(4)
            self.config_table.setHorizontalHeaderLabels(['Value', 'Min', 'Max', 'Fixed'])
            self.config_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.config_table.horizontalHeader().setSectionResizeMode(self.VALUE_COLUMN,
                                                                      QtWidgets.QHeaderView.Stretch)
            self.config_table.horizontalHeader().setSectionResizeMode(self.MIN_COLUMN, QtWidgets.QHeaderView.Stretch)
            self.config_table.horizontalHeader().setSectionResizeMode(self.MAX_COLUMN, QtWidgets.QHeaderView.Stretch)
            self.config_table.horizontalHeader().setSectionResizeMode(self.FIXED_COLUMN, QtWidgets.QHeaderView.Stretch)

            self.batch_table.setColumnCount(3)
            self.batch_table.setHorizontalHeaderLabels(['Global', 'Fixed - Run Dep.', 'Value'])
            self.batch_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.batch_table.horizontalHeader().setSectionResizeMode(self.FIXED_VALUE_COLUMN,
                                                                      QtWidgets.QHeaderView.Stretch)
            self.batch_table.horizontalHeader().setSectionResizeMode(self.GLOBAL_COLUMN,
                                                                     QtWidgets.QHeaderView.Stretch)
            self.batch_table.horizontalHeader().setSectionResizeMode(self.FIXED_RUN_COLUMN,
                                                                     QtWidgets.QHeaderView.Stretch)

            self.output_table.setColumnCount(2)
            self.output_table.setHorizontalHeaderLabels(['Value', 'Uncertainty'])
            self.output_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.output_table.horizontalHeader().setSectionResizeMode(self.OUTPUT_VALUE_COLUMN,
                                                                      QtWidgets.QHeaderView.Stretch)
            self.output_table.horizontalHeader().setSectionResizeMode(self.UNCERTAINTY_COLUMN,
                                                                      QtWidgets.QHeaderView.Stretch)
            self.output_table.setEditTriggers(qt_constants.NoEditTriggers)

    def __init__(self):
        super(FittingPanel, self).__init__()
        self.__batch_table_states = {}
        self.__update_states = True
        self.__logger = logging.getLogger('QtFitting')

        self.support_panel = FittingPanel.SupportPanel()

        self.parameter_table = self.ParameterTable()

        self.input_fit_equation = QtWidgets.QLineEdit()
        self.input_user_equation = QtWidgets.QLineEdit()
        self.input_user_equation_name = QtWidgets.QLineEdit()
        self.input_spectrum_min = QtWidgets.QLineEdit()
        self.input_spectrum_max = QtWidgets.QLineEdit()
        self.input_packing = QtWidgets.QLineEdit()
        self.option_preset_fit_equations = QtWidgets.QComboBox()
        self.option_user_fit_equations = QtWidgets.QComboBox()
        self.option_run_ordering = QtWidgets.QComboBox()
        self.option_ascending = QtWidgets.QComboBox()

        self.fit_spectrum_settings = FittingPanel.PlotControl()
        self.fit_display = FittingPanel.PlotDisplay(self.fit_spectrum_settings)
        self.special_characters = qt_widgets.CollapsibleBox("Special Characters", background='#FFFFFF')
        self.special_characters.toggle_button.released.connect(self.special_characters.on_pressed)

        self.table_parameters = QtWidgets.QTableWidget()
        self.run_list = QtWidgets.QListWidget()

        self.button_check_equation = qt_widgets.StyleOneButton("Check")
        self.button_fit = qt_widgets.StyleThreeButton("Fit")
        self.button_insert_preset_equation = qt_widgets.StyleTwoButton("Insert")
        self.button_insert_user_equation = qt_widgets.StyleTwoButton("Insert")
        self.button_save_user_equation = qt_widgets.StyleTwoButton("Save")
        self.button_plot = qt_widgets.StyleTwoButton("Plot")

        self.button_fit.setToolTip('Run fit')
        self.button_insert_preset_equation.setToolTip('Insert predefined function')
        self.button_insert_user_equation.setToolTip('Insert user defined function')
        self.button_save_user_equation.setToolTip('Save user defined function')
        self.button_plot.setToolTip('Plot data')

        self.label_global_plus = QtWidgets.QLabel("Global+")
        self.label_ordering = QtWidgets.QLabel("Order by")
        self.label_use_previous = QtWidgets.QLabel("Use Previous Run")
        self.label_batch = QtWidgets.QLabel("Batch")

        self.check_batch_fit = QtWidgets.QCheckBox()
        self.check_global_plus = QtWidgets.QCheckBox()
        self.check_use_previous = QtWidgets.QCheckBox()

        self.insert_phi = qt_widgets.StyleTwoButton(fit.PHI)
        self.insert_alpha = qt_widgets.StyleTwoButton(fit.ALPHA)
        self.insert_sigma = qt_widgets.StyleTwoButton(fit.SIGMA)
        self.insert_naught = qt_widgets.StyleTwoButton(fit.NAUGHT)
        self.insert_lambda = qt_widgets.StyleTwoButton(fit.LAMBDA)
        self.insert_delta = qt_widgets.StyleTwoButton(fit.DELTA)
        self.insert_beta = qt_widgets.StyleTwoButton(fit.BETA)
        self.insert_pi = qt_widgets.StyleOneButton(fit.PI)

        self.group_preset_functions = QtWidgets.QGroupBox("Predefined Functions")
        self.group_user_functions = QtWidgets.QGroupBox("User Defined Functions")
        self.group_special_characters = QtWidgets.QGroupBox("")
        self.group_batch_options = QtWidgets.QGroupBox("Options")
        self.group_spectrum_options = QtWidgets.QGroupBox("Spectrum")
        self.group_table_parameters = QtWidgets.QGroupBox("Parameters")
        self.group_table_runs = QtWidgets.QGroupBox("Runs")
        self.group_function = QtWidgets.QGroupBox("Function")

        self._set_widget_layout()
        self._set_widget_attributes()
        self._set_widget_dimensions()

        self._presenter = FitTabPresenter(self)
        self._line_edit_style = self.input_fit_equation.styleSheet()

    def _set_widget_attributes(self):
        self.parameter_table.batch_table.itemChanged.connect(self._update_batch_table_states)
        self.run_list.itemChanged.connect(self._update_batch_table_states)
        self.run_list.itemSelectionChanged.connect(self._update_batch_table)
        self.check_batch_fit.stateChanged.connect(self._update_batch_options)
        self.check_global_plus.stateChanged.connect(self._update_batch_options)

        # TODO We could possibly handle multiple selection, but we would have to put a '*' in fixed value in the batch
        #   table (because you could be selecting some with different initial values that you want to set to the same)
        #   which may be more trouble then it is worth but I will leave this note here for future reference.
        # self.run_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)

        self.option_preset_fit_equations.addItems(list(fit.EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItems(list(fit.USER_EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItem("None")
        self.option_run_ordering.addItems([files.FIELD_KEY, files.TEMPERATURE_KEY, files.RUN_NUMBER_KEY])
        self.option_ascending.addItems(['Ascending', 'Descending'])

        self.input_user_equation_name.setPlaceholderText("Function Name")
        self.input_user_equation.setPlaceholderText("Function (e.g. \"\u03B2 * (t + \u03BB)\")")
        self.input_fit_equation.setPlaceholderText("Fit Equation")

        self.option_ascending.setEnabled(False)
        self.check_global_plus.setEnabled(True)
        self.option_run_ordering.setEnabled(False)
        self.label_global_plus.setEnabled(True)
        self.label_ordering.setEnabled(False)
        self.label_use_previous.setEnabled(False)

    def _set_widget_dimensions(self):
        self.button_fit.setFixedWidth(60)
        self.button_fit.setFixedHeight(60)
        self.button_check_equation.setFixedWidth(60)
        self.button_insert_user_equation.setFixedWidth(60)
        self.button_insert_preset_equation.setFixedWidth(60)
        self.button_save_user_equation.setFixedWidth(60)
        self.button_plot.setFixedWidth(60)

        self.option_user_fit_equations.setFixedWidth(200)
        self.option_preset_fit_equations.setFixedWidth(200)

        self.group_table_parameters.setMaximumWidth(380)
        self.group_table_runs.setMaximumWidth(380)
        self.group_batch_options.setMaximumWidth(380)
        self.group_batch_options.setMaximumHeight(110)

        self.insert_pi.setFixedWidth(30)
        self.insert_phi.setFixedWidth(30)
        self.insert_beta.setFixedWidth(30)
        self.insert_alpha.setFixedWidth(30)
        self.insert_delta.setFixedWidth(30)
        self.insert_lambda.setFixedWidth(30)
        self.insert_naught.setFixedWidth(30)
        self.insert_sigma.setFixedWidth(30)

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()

        grid = QtWidgets.QGridLayout()

        # Create and add GroupBox for predefined fit equations
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.option_preset_fit_equations)
        row.addWidget(self.button_insert_preset_equation)
        layout = QtWidgets.QFormLayout()
        layout.addRow(row)
        self.group_preset_functions.setLayout(layout)
        grid.addWidget(self.group_preset_functions, 0, 0, 1, 1)

        # Create and add GroupBox for user defined fit equations
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.option_user_fit_equations)
        row.addWidget(self.button_insert_user_equation)
        row.addSpacing(20)
        row.addWidget(self.input_user_equation_name)
        row.addWidget(self.input_user_equation,2)
        row.addWidget(self.button_save_user_equation)
        row.addSpacing(10)
        layout = QtWidgets.QFormLayout()
        layout.addRow(row)
        self.group_user_functions.setLayout(layout)
        grid.addWidget(self.group_user_functions, 0, 1, 1, 5)

        # Add our top row of layouts (the loaded fit functions)
        main_layout.addLayout(grid)

        # Create a row for our fit function (the input and special character keys)
        row = QtWidgets.QHBoxLayout()
        row.addSpacing(20)
        row.addWidget(QtWidgets.QLabel("A(t) = "))
        row.addSpacing(5)
        row.addWidget(self.input_fit_equation)
        row.addSpacing(20)
        row.addWidget(self.insert_pi)
        row.addWidget(self.insert_alpha)
        row.addWidget(self.insert_beta)
        row.addWidget(self.insert_delta)
        row.addWidget(self.insert_lambda)
        row.addWidget(self.insert_phi)
        row.addWidget(self.insert_sigma)
        row.addWidget(self.insert_naught)
        row.addSpacing(15)
        self.group_function.setLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.group_function)
        main_layout.addLayout(row)

        # Create and add GroupBox for batch options
        layout = QtWidgets.QFormLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_batch_fit)
        row.addWidget(self.label_batch)
        row.addStretch()
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.label_ordering)
        row2.addSpacing(2)
        row2.addWidget(self.option_run_ordering)
        row2.addWidget(self.option_ascending)
        row2.addStretch()
        row.addLayout(row2)
        layout.addRow(row)
        self.group_batch_options.setLayout(layout)

        # Create and add GroupBox for table parameters
        left_side = QtWidgets.QVBoxLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.parameter_table)
        self.group_table_parameters.setLayout(row)
        left_side.addWidget(self.group_table_parameters)

        # Create and add GroupBox for run list
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.run_list)
        self.group_table_runs.setLayout(row)
        left_side.addWidget(self.group_table_runs)
        left_side.addWidget(self.group_batch_options)

        # Create and add layout for plot display and controls
        right_side = QtWidgets.QVBoxLayout()
        right_side.addWidget(self.fit_display, 2)
        hbox = QtWidgets.QHBoxLayout()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.button_plot)
        vbox.addWidget(self.button_fit)
        hbox.addLayout(vbox)
        hbox.addWidget(self.fit_spectrum_settings)
        right_side.addLayout(hbox)

        # And put it all together
        row = QtWidgets.QHBoxLayout()
        row.addLayout(left_side)
        row.addSpacing(10)
        row.addLayout(right_side)
        row.addSpacing(10)
        main_layout.addLayout(row)

        self.setLayout(main_layout)

    def _update_batch_options(self):
        self.label_ordering.setEnabled(self.check_batch_fit.isChecked() or self.check_global_plus.isChecked())
        self.option_run_ordering.setEnabled(self.check_batch_fit.isChecked() or self.check_global_plus.isChecked())
        self.option_ascending.setEnabled(self.check_batch_fit.isChecked() or self.check_global_plus.isChecked())

    def _update_batch_table(self):
        self.__update_states = False
        for j in range(self.parameter_table.config_table.rowCount()):  # Iterate over every symbol in table
            symbol = self.parameter_table.config_table.verticalHeaderItem(j).text()

            if len(self.get_selected_run_ids()) > 0 \
                    and symbol in self.__batch_table_states.keys() \
                    and self.get_selected_run_ids()[0] in self.__batch_table_states[symbol].keys():
                value = self.__batch_table_states[symbol][self.get_selected_run_ids()[0]][2]
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText(str(value))
                self.parameter_table.batch_table.setItem(j, self.parameter_table.FIXED_VALUE_COLUMN, item_value)
        self.__update_states = True

    def _update_batch_table_states(self):
        if not self.__update_states:
            return

        self.__update_states = False
        for j in range(self.parameter_table.config_table.rowCount()):  # Iterate over every symbol in table
            symbol = self.parameter_table.config_table.verticalHeaderItem(j).text()
            item_fixed_run = self.parameter_table.batch_table.cellWidget(j, self.parameter_table.FIXED_RUN_COLUMN)
            item_fixed_run_value = self.parameter_table.batch_table.item(j, self.parameter_table.FIXED_VALUE_COLUMN)

            if item_fixed_run_value is None:
                item_fixed_run_value = QtWidgets.QTableWidgetItem()
                item_fixed_run_value.setText('')
            else:
                try:
                    float(item_fixed_run_value.text())
                except ValueError:
                    self.highlight_input_red(self.parameter_table.batch_table, True)
                    self.__update_states = True
                    return  # This way the state can only be updated to good values.
            self.highlight_input_red(self.parameter_table.batch_table, False)

            if item_fixed_run is None:  # Sometimes this happens with QTableWidgets, just skip.
                continue

            selected_titles = self.get_selected_run_ids()
            self.__batch_table_states[symbol] = {
                run_id: (
                    symbol,
                    item_fixed_run.findChild(QtWidgets.QCheckBox).checkState() > 0,
                    item_fixed_run_value.text() if (run_id in selected_titles and item_fixed_run_value.text() != '')
                    else self.parameter_table.config_table.item(j, self.parameter_table.VALUE_COLUMN).text() if (symbol not in self.__batch_table_states.keys() or run_id not in self.__batch_table_states[symbol].keys())
                    else self.__batch_table_states[symbol][run_id][2]
                ) for run_id in self.get_all_run_ids()
            }

            if len(self.get_selected_run_ids()) > 0:
                value = self.__batch_table_states[symbol][self.get_selected_run_ids()[0]][2]
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText(str(value))
                self.parameter_table.batch_table.setItem(j, self.parameter_table.FIXED_VALUE_COLUMN, item_value)

        self.__update_states = True

    def createSupportPanel(self) -> QtWidgets.QDockWidget:
        return self.support_panel

    def _create_check_box_for_table(self, checked=None, connect=None):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        check = QtWidgets.QCheckBox()
        if connect:
            check.stateChanged.connect(connect)
        check.setCheckState(qt_constants.Checked if checked else qt_constants.Unchecked)
        layout.addWidget(check)
        layout.setAlignment(qt_constants.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def add_parameter(self, symbol: str, config_value: float = None, config_lower: float = None,
                      config_upper: float = None, config_fixed: bool = None, batch_global: bool = None,
                      batch_run_dependent: bool = None, batch_value: float = None, output_value: float = None,
                      output_uncertainty: float = None, run_id: str = None):
        n = self.parameter_table.config_table.verticalHeader().count()

        in_table = False
        for i in range(n - 1, -1, -1):
            item = self.parameter_table.config_table.verticalHeaderItem(i)

            if item is None:
                continue

            if symbol == item.text():
                in_table = True
                if config_value is not None:
                    item_value = QtWidgets.QTableWidgetItem()
                    item_value.setText('{:.5f}'.format(float(config_value)))
                    self.parameter_table.config_table.setItem(i, self.ParameterTable.VALUE_COLUMN, item_value)

                if config_lower is not None:
                    item_lower = QtWidgets.QTableWidgetItem()
                    item_lower.setText('{:.5f}'.format(float(config_lower)))
                    self.parameter_table.config_table.setItem(i, self.ParameterTable.MIN_COLUMN, item_lower)

                if config_upper is not None:
                    item_upper = QtWidgets.QTableWidgetItem()
                    item_upper.setText('{:.5f}'.format(float(config_upper)))
                    self.parameter_table.config_table.setItem(i, self.ParameterTable.MAX_COLUMN, item_upper)

                if config_fixed is not None:
                    item_fixed = self._create_check_box_for_table(config_fixed)
                    self.parameter_table.config_table.setCellWidget(i, self.ParameterTable.FIXED_COLUMN, item_fixed)

        if not in_table:
            self.parameter_table.config_table.setRowCount(n + 1)

            item_symbol = QtWidgets.QTableWidgetItem()
            item_symbol.setText(symbol)
            self.parameter_table.config_table.setVerticalHeaderItem(n, item_symbol)

            if config_value is not None:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('{:.5f}'.format(float(config_value)))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.VALUE_COLUMN, item_value)
            else:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('1')
                self.parameter_table.config_table.setItem(n, self.ParameterTable.VALUE_COLUMN, item_value)

            if config_lower is not None:
                item_lower = QtWidgets.QTableWidgetItem()
                item_lower.setText('{:.5f}'.format(float(config_lower)))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MIN_COLUMN, item_lower)
            else:
                item_lower = QtWidgets.QTableWidgetItem()
                item_lower.setText(str(-np.inf))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MIN_COLUMN, item_lower)

            if config_upper is not None:
                item_upper = QtWidgets.QTableWidgetItem()
                item_upper.setText('{:.5f}'.format(float(config_upper)))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MAX_COLUMN, item_upper)
            else:
                item_upper = QtWidgets.QTableWidgetItem()
                item_upper.setText(str(np.inf))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MAX_COLUMN, item_upper)

            if config_fixed is not None:
                item_fixed = self._create_check_box_for_table(config_fixed)
                self.parameter_table.config_table.setCellWidget(n, self.ParameterTable.FIXED_COLUMN, item_fixed)
            else:
                item_fixed = self._create_check_box_for_table(False)
                self.parameter_table.config_table.setCellWidget(n, self.ParameterTable.FIXED_COLUMN, item_fixed)

        n = self.parameter_table.batch_table.verticalHeader().count()

        in_table = False
        for i in range(n - 1, -1, -1):
            item = self.parameter_table.batch_table.verticalHeaderItem(i)

            if item is None:
                continue

            if symbol == item.text():
                if run_id:
                    self.__batch_table_states[run_id] = (batch_value, batch_global, batch_run_dependent)

                in_table = True
                if batch_value is not None:
                    item_value = QtWidgets.QTableWidgetItem()
                    item_value.setText('{:.5f}'.format(float(batch_value)))
                    self.parameter_table.batch_table.setItem(i, self.ParameterTable.FIXED_VALUE_COLUMN, item_value)

                if batch_global is not None:
                    item_global = self._create_check_box_for_table(batch_global)
                    self.parameter_table.batch_table.setCellWidget(i, self.ParameterTable.GLOBAL_COLUMN, item_global)

                if batch_run_dependent is not None:
                    item_fixed = self._create_check_box_for_table(batch_run_dependent, self._update_batch_table_states)
                    self.parameter_table.batch_table.setCellWidget(i, self.ParameterTable.FIXED_RUN_COLUMN, item_fixed)

        if not in_table:
            if run_id:
                self.__batch_table_states[run_id] = (batch_value, batch_global, batch_run_dependent)

            self.parameter_table.batch_table.setRowCount(n + 1)

            item_symbol = QtWidgets.QTableWidgetItem()
            item_symbol.setText(symbol)
            self.parameter_table.batch_table.setVerticalHeaderItem(n, item_symbol)

            if batch_value is not None:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('{:.5f}'.format(float(batch_value)))
                self.parameter_table.batch_table.setItem(n, self.ParameterTable.FIXED_VALUE_COLUMN, item_value)
            else:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('1')
                self.parameter_table.batch_table.setItem(n, self.ParameterTable.FIXED_VALUE_COLUMN, item_value)

            if batch_global is not None:
                item_global = self._create_check_box_for_table(batch_global)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.GLOBAL_COLUMN, item_global)
            else:
                item_global = self._create_check_box_for_table(False)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.GLOBAL_COLUMN, item_global)

            if batch_run_dependent is not None:
                item_fixed = self._create_check_box_for_table(batch_run_dependent, self._update_batch_table_states)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.FIXED_RUN_COLUMN, item_fixed)
            else:
                item_fixed = self._create_check_box_for_table(False, self._update_batch_table_states)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.FIXED_RUN_COLUMN, item_fixed)

        n = self.parameter_table.output_table.verticalHeader().count()

        in_table = False
        for i in range(n - 1, -1, -1):
            item = self.parameter_table.output_table.verticalHeaderItem(i)

            if item is None:
                continue

            if symbol == item.text():
                in_table = True
                if output_value is not None:
                    item_value = QtWidgets.QTableWidgetItem()
                    item_value.setText('{:.5f}'.format(float(output_value)))
                    self.parameter_table.output_table.setItem(i, self.ParameterTable.OUTPUT_VALUE_COLUMN, item_value)

                if output_uncertainty is not None:
                    item_value = QtWidgets.QTableWidgetItem()
                    item_value.setText('{:.5f}'.format(float(output_uncertainty)))
                    self.parameter_table.output_table.setItem(i, self.ParameterTable.UNCERTAINTY_COLUMN, item_value)

        if not in_table:
            self.parameter_table.output_table.setRowCount(n + 1)

            item_symbol = QtWidgets.QTableWidgetItem()
            item_symbol.setText(symbol)
            self.parameter_table.output_table.setVerticalHeaderItem(n, item_symbol)

            if output_value is not None:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('{:.5f}'.format(float(output_value)))
                self.parameter_table.output_table.setItem(n, self.ParameterTable.OUTPUT_VALUE_COLUMN, item_value)

            if output_uncertainty is not None:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('{:.5f}'.format(float(output_uncertainty)))
                self.parameter_table.output_table.setItem(n, self.ParameterTable.UNCERTAINTY_COLUMN, item_value)

        self._update_batch_table_states()

    def clear_parameters(self, symbols):
        n = self.parameter_table.config_table.verticalHeader().count()

        for i in range(n - 1, -1, -1):
            item = self.parameter_table.config_table.verticalHeaderItem(i)

            if item is None or item.text() in symbols:
                continue

            self.parameter_table.config_table.removeRow(i)

        n = self.parameter_table.batch_table.verticalHeader().count()

        for i in range(n - 1, -1, -1):
            item = self.parameter_table.batch_table.verticalHeaderItem(i)

            if item is None or item.text() in symbols:
                continue

            self.parameter_table.batch_table.removeRow(i)

        n = self.parameter_table.output_table.verticalHeader().count()

        for i in range(n - 1, -1, -1):
            item = self.parameter_table.output_table.verticalHeaderItem(i)

            if item is None or item.text() in symbols:
                continue

            self.parameter_table.output_table.removeRow(i)

    def get_checked_run_titles(self):
        titles = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.checkState():
                titles.append(item.text())
        return titles

    def get_checked_run_ids(self):
        ids = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.checkState():
                ids.append(item.identifier)
        return ids

    def get_selected_run_titles(self):
        titles = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.isSelected():
                titles.append(item.text())
        return titles

    def get_selected_run_ids(self):
        ids = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.isSelected():
                ids.append(item.identifier)
        return ids

    def get_all_run_titles(self):
        titles = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            titles.append(item.text())
        return titles

    def get_all_run_ids(self):
        ids = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            ids.append(item.identifier)
        return ids

    def get_parameters(self):
        parameters = []
        for i in range(self.parameter_table.config_table.rowCount()):
            item_symbol = self.parameter_table.config_table.verticalHeaderItem(i)
            item_value = self.parameter_table.config_table.item(i, self.parameter_table.VALUE_COLUMN)
            item_min = self.parameter_table.config_table.item(i, self.parameter_table.MIN_COLUMN)
            item_max = self.parameter_table.config_table.item(i, self.parameter_table.MAX_COLUMN)
            item_fixed = self.parameter_table.config_table.cellWidget(i, self.parameter_table.FIXED_COLUMN)
            item_global = self.parameter_table.batch_table.cellWidget(i, self.parameter_table.GLOBAL_COLUMN)
            item_output_value = self.parameter_table.output_table.item(i, self.parameter_table.OUTPUT_VALUE_COLUMN)
            item_output_uncertainty = self.parameter_table.output_table.item(i, self.parameter_table.UNCERTAINTY_COLUMN)

            if item_symbol is None:
                continue

            symbol = item_symbol.text()
            value = 1 if item_value is None or item_value.text() == '' else float(item_value.text())
            value_min = -np.inf if item_min is None or item_min.text() == '' else float(item_min.text())
            value_max = np.inf if item_max is None or item_max.text() == '' else float(item_max.text())
            value_output = None if item_output_value is None or item_output_value.text() == '' else float(item_output_value.text())
            value_uncertainty = None if item_output_uncertainty is None or item_output_uncertainty.text() == '' else float(item_output_uncertainty.text())
            is_fixed = item_fixed is not None and item_fixed.findChild(QtWidgets.QCheckBox).checkState() > 0
            is_global = item_global is not None and item_global.findChild(QtWidgets.QCheckBox).checkState() > 0

            parameters.append((symbol, value, value_min, value_max, value_output, value_uncertainty, is_fixed, is_global,
                               self.__batch_table_states[symbol]))

        return parameters

    def get_batch_ordering(self):
        return self.option_run_ordering.currentText(), self.option_ascending.currentText() == 'Ascending'

    def get_expression(self):
        return self.input_fit_equation.text()

    def is_run_dependent(self):
        is_run_dependent = False

        for i in range(self.parameter_table.batch_table.rowCount()):
            item_fixed = self.parameter_table.batch_table.cellWidget(i, self.parameter_table.FIXED_RUN_COLUMN)
            is_run_dependent = is_run_dependent or (item_fixed is not None and item_fixed.findChild(QtWidgets.QCheckBox).checkState() > 0)

        return is_run_dependent

    def highlight_input_red(self, box, red):
        if red:
            box.setStyleSheet("border: 1px solid red;")
        else:
            box.setStyleSheet(self._line_edit_style)

    def update_run_table(self, runs):
        self.run_list.clear()

        for run in runs:
            run_item = qt_widgets.IdentifiableListWidgetItem(run.id, run.meta[files.TITLE_KEY], self.run_list)
            run_item.setFlags(run_item.flags() | qt_constants.ItemIsUserCheckable)
            run_item.setCheckState(qt_constants.Unchecked)

    def copy_loaded_function_to_cursor(self):
        self.input_fit_equation.insert(fit.EQUATION_DICTIONARY[self.option_preset_fit_equations.currentText()])

    def copy_user_function_to_cursor(self):
        if self.option_user_fit_equations.currentText() == 'None':
            return

        self.input_fit_equation.insert(fit.USER_EQUATION_DICTIONARY[self.option_user_fit_equations.currentText()])

    def copy_character_to_cursor(self, char):
        self.input_fit_equation.insert(char)

    def select_first_fit_from_dataset(self, dataset_id):
        for i in range(self.support_panel.tree.topLevelItemCount()):
            if self.support_panel.tree.topLevelItem(i).text(0) == dataset_id:
                self.support_panel.tree.topLevelItem(i).setExpanded(True)
                self.support_panel.tree.topLevelItem(i).child(0).setSelected(True)

    def select_top_child_run(self, dataset_id):
        index = 0
        for i in range(self.support_panel.tree.topLevelItemCount()):
            if self.support_panel.tree.topLevelItem(i).model.id == dataset_id:
                index = i
        run_id = self.support_panel.tree.topLevelItem(index).child(0).model.run_id
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.identifier == run_id:
                item.setCheckState(qt_constants.Checked)
            else:
                item.setCheckState(qt_constants.Unchecked)

    def clear(self):
        self.input_fit_equation.clear()
        for i in range(self.table_parameters.rowCount()):
            self.table_parameters.removeRow(0)
        for i in range(self.run_list.count()):
            self.run_list.item(i).setCheckState(qt_constants.Unchecked)
        self.table_parameters.setEnabled(True)
        self.run_list.setEnabled(True)
        self.fit_display.set_full_blank()

    @staticmethod
    def launch(args):
        dialog = FittingPanel(args)
        return dialog.exec()


class FitTabPresenter:
    def __init__(self, view: FittingPanel):
        self._view = view
        self._run_service = services.RunService()
        self._fit_service = services.FitService()
        self._system_service = services.SystemService()
        self._style_service = services.StyleService()
        self._set_callbacks()

        fit.USER_EQUATION_DICTIONARY = self._system_service.get_user_defined_functions()
        view.option_user_fit_equations.addItems(fit.USER_EQUATION_DICTIONARY.keys())

        self._run_service.signals.added.connect(self.update)
        self._run_service.signals.changed.connect(self.update)
        self._run_service.signals.loaded.connect(self.update)
        self._fit_service.signals.added.connect(self.update)
        self._fit_service.signals.changed.connect(self.update)

        self._runs = []
        self._asymmetries = {}
        self._threadpool = QtCore.QThreadPool()

        self.__update_if_table_changes = True
        self.__variable_groups = {}
        self.__expression = None
        self.__logger = logging.getLogger('FittingPanelPresenter')

    def _set_callbacks(self):
        self._view.support_panel.tree.itemSelectionChanged.connect(self._selection_changed)
        self._view.input_fit_equation.textChanged.connect(self._function_input_changed)
        self._view.button_insert_preset_equation.released.connect(self._view.copy_loaded_function_to_cursor)
        self._view.button_insert_user_equation.released.connect(self._view.copy_user_function_to_cursor)
        self._view.button_save_user_equation.released.connect(self._save_user_function)
        self._view.insert_sigma.released.connect(lambda: self._view.copy_character_to_cursor(fit.SIGMA))
        self._view.insert_pi.released.connect(lambda: self._view.copy_character_to_cursor(fit.PI))
        self._view.insert_phi.released.connect(lambda: self._view.copy_character_to_cursor(fit.PHI))
        self._view.insert_naught.released.connect(lambda: self._view.copy_character_to_cursor(fit.NAUGHT))
        self._view.insert_lambda.released.connect(lambda: self._view.copy_character_to_cursor(fit.LAMBDA))
        self._view.insert_delta.released.connect(lambda: self._view.copy_character_to_cursor(fit.DELTA))
        self._view.insert_alpha.released.connect(lambda: self._view.copy_character_to_cursor(fit.ALPHA))
        self._view.insert_beta.released.connect(lambda: self._view.copy_character_to_cursor(fit.BETA))
        self._view.fit_spectrum_settings.input_time_xmax.returnPressed.connect(self._update_display)
        self._view.fit_spectrum_settings.input_time_xmin.returnPressed.connect(self._update_display)
        self._view.fit_spectrum_settings.input_bin.returnPressed.connect(self._update_display)
        self._view.fit_spectrum_settings.slider_bin.sliderMoved.connect(self._update_display)
        self._view.button_plot.released.connect(self._update_display)
        self._view.parameter_table.config_table.itemChanged.connect(self._plot_fit)
        self._view.parameter_table.batch_table.itemChanged.connect(self._plot_fit)
        self._view.parameter_table.output_table.itemChanged.connect(self._plot_fit)
        self._view.button_fit.released.connect(self._fit)
        self._view.support_panel.new_button.released.connect(self._new_empty_fit)

    def _function_input_changed(self):
        if not self.__update_if_table_changes:
            return
        self.__update_if_table_changes = False

        expression = "A(t) = " + self._view.get_expression()

        if fit.is_valid_expression(expression):
            self._view.highlight_input_red(self._view.input_fit_equation, False)

            variables = fit.parse(fit.split_expression(expression)[1])
            variables.discard(fit.INDEPENDENT_VARIABLE)
            variables.add(fit.ALPHA)

            self._view.clear_parameters(variables)

            self._view.add_parameter(symbol=fit.ALPHA)
            for var in variables:
                self._view.add_parameter(symbol=var)

        else:
            self._view.highlight_input_red(self._view.input_fit_equation, True)
        self.__update_if_table_changes = True
        self._plot_fit()

    def _save_user_function(self):
        function_name = self._view.input_user_equation_name.text()

        if function_name == "":
            self._view.highlight_input_red(self._view.input_user_equation_name, True)
            return
        else:
            self._view.highlight_input_red(self._view.input_user_equation_name, False)

        function = "A(t) = " + self._view.input_user_equation.text()

        if fit.is_valid_expression(function):
            self._view.highlight_input_red(self._view.input_user_equation, False)
        else:
            self._view.highlight_input_red(self._view.input_user_equation, True)

        if function_name not in fit.USER_EQUATION_DICTIONARY.keys():
            self._view.option_user_fit_equations.addItem(function_name)
            self._system_service.add_user_defined_function(function_name, self._view.input_user_equation.text())
            fit.USER_EQUATION_DICTIONARY[function_name] = self._view.input_user_equation.text()

        self._view.option_user_fit_equations.setCurrentText(function_name)
        self._view.input_user_equation_name.clear()
        self._view.input_user_equation.clear()

    def _update_display(self):
        run_ids = self._view.get_checked_run_ids()

        runs = self._runs

        self._view.fit_display.start_plotting()

        max_asymmetry = -1
        min_asymmetry = 1
        min_time = self._view.fit_spectrum_settings.get_min_time()
        max_time = self._view.fit_spectrum_settings.get_max_time()
        bin_size = self._view.fit_spectrum_settings.get_bin_from_input()

        colors = {}
        available_colors = list(self._style_service.color_options_values.values())

        styles = self._style_service.get_styles()
        colors = {run.id: styles[run.id][self._style_service.Keys.DEFAULT_COLOR] for run in runs}
        # colors = {run.id: available_colors[i % len(available_colors)] for i, run in enumerate(runs)}
        colors[0] = '#000000'

        checked_run_ids = [0]
        checked_run_ids.extend(self._view.get_checked_run_ids())
        alphas = dict()

        # Plot the fit lines
        for i, (run_id, parameters) in enumerate(self.__variable_groups.items()):
            if (run_id == 0 or 'UNLINKED' not in run_id) and run_id not in checked_run_ids:
                continue

            parameters = self.__variable_groups[run_id]
            alphas[run_id] = parameters[fit.ALPHA].value
            time = objects.Time(input_array=None, bin_size=(max_time - min_time) * 1000 / 200, length=200,
                                time_zero=min_time)
            fit_asymmetry = self.__expression(time, **{symbol: par.get_value() for symbol, par in parameters.items()})

            try:
                if len(fit_asymmetry) == 1:
                    fit_asymmetry = [fit_asymmetry for _ in time]
            except TypeError:
                fit_asymmetry = [fit_asymmetry for _ in time]

            if len(run_ids) == 0 or len(runs) == 0:
                frac_start = float(min_time) / (time[len(time) - 1] - time[0])
                frac_end = float(max_time) / (time[len(time) - 1] - time[0])
                start_index = int(np.floor(len(fit_asymmetry) * frac_start))
                end_index = int(np.floor(len(fit_asymmetry) * frac_end))
                local_max = np.max(fit_asymmetry[start_index:end_index])
                max_asymmetry = local_max if local_max > max_asymmetry else max_asymmetry
                local_min = np.min(fit_asymmetry[start_index:end_index])
                min_asymmetry = local_min if local_min < min_asymmetry else min_asymmetry

            if run_id != 0 and 'UNLINKED' in run_id:
                color = list(self._style_service.color_options_values.values())[-i]
            else:
                color = colors[run_id]

            self._view.fit_display.plot_asymmetry(time, fit_asymmetry, None, None,
                                                  color=color,
                                                  marker='.',
                                                  linestyle='-',
                                                  fillstyle='none',
                                                  marker_color=color,
                                                  marker_size=1,
                                                  line_color=color,
                                                  line_width=1,
                                                  errorbar_color=color,
                                                  errorbar_style='none',
                                                  errorbar_width=1,
                                                  fit_color=color,
                                                  fit_linestyle='none',
                                                  label=None)

        # Plot the asymmetries
        for i, run in enumerate(runs):
            if run.id not in run_ids:
                continue

            asymmetry = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].bin(bin_size).cut(min_time=min_time,
                                                                                             max_time=max_time)
            if len(asymmetry) == 0:
                return

            if run.id in alphas:
                asymmetry = asymmetry.correct(alphas[run.id])

            raw_asymmetry = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].raw().bin(bin_size).cut(min_time=min_time,
                                                                                                       max_time=max_time)
            self._asymmetries[run.id] = raw_asymmetry
            time = asymmetry.time
            uncertainty = asymmetry.uncertainty

            # We have to do this logic because Matplotlib is not good at setting good default plot limits
            frac_start = float(min_time) / (time[len(time) - 1] - time[0])
            frac_end = float(max_time) / (time[len(time) - 1] - time[0])
            start_index = int(np.floor(len(asymmetry) * frac_start))
            end_index = int(np.floor(len(asymmetry) * frac_end))
            local_max = np.max(asymmetry[start_index:end_index])
            max_asymmetry = local_max if local_max > max_asymmetry else max_asymmetry
            local_min = np.min(asymmetry[start_index:end_index])
            min_asymmetry = local_min if local_min < min_asymmetry else min_asymmetry

            self._view.fit_display.plot_asymmetry(time, asymmetry, uncertainty, None,
                                                  color=colors[run.id],
                                                  marker='.',
                                                  linestyle='none',
                                                  fillstyle='none',
                                                  marker_color=colors[run.id],
                                                  marker_size=5,
                                                  line_color=colors[run.id],
                                                  line_width=1,
                                                  errorbar_color=colors[run.id],
                                                  errorbar_style='none',
                                                  errorbar_width=1,
                                                  fit_color=colors[run.id],
                                                  fit_linestyle='none',
                                                  label=run.meta[files.TITLE_KEY])

        self._view.fit_display.set_asymmetry_plot_limits(max_asymmetry, min_asymmetry)

        self._view.fit_display.finish_plotting(False)

    def _plot_fit(self):
        if not self.__update_if_table_changes:
            return

        expression, parameters = self._get_expression_and_values(get_default=True)

        if expression == self.__expression and self.__variable_groups == parameters:
            return

        if len(parameters) == 0:
            self.__expression = expression
            self.__variable_groups = {}
            return

        self.__expression = expression
        self.__variable_groups = parameters
        self._update_display()

    def _get_expression_and_values(self, get_default=False):
        try:
            parameters = self._view.get_parameters()
            expression = self._view.get_expression()
        except ValueError:
            self._view.highlight_input_red(self._view.parameter_table, True)
            return None, {}
        self._view.highlight_input_red(self._view.parameter_table, False)

        final_parameters = {}
        run_dependent = False
        for run in self._runs:
            run_parameters = {}
            for symbol, value, value_min, value_max, value_output, value_uncertainty, \
                    is_fixed, is_global, fixed_run_dict in parameters:
                run_parameters[symbol] = fit.FitParameter(symbol=symbol, value=value, lower=value_min, upper=value_max,
                                                          is_global=is_global, is_fixed=is_fixed, is_fixed_run=fixed_run_dict[run.id][1],
                                                          fixed_value=float(fixed_run_dict[run.id][2]))
                run_dependent = run_dependent or run_parameters[symbol].is_fixed_run
            final_parameters[run.id] = run_parameters

        if get_default and not run_dependent:
            run_parameters = {}
            for symbol, value, value_min, value_max, value_output, value_uncertainty, \
                    is_fixed, is_global, fixed_run_dict in parameters:
                run_parameters[symbol] = fit.FitParameter(symbol=symbol, value=value, lower=value_min, upper=value_max,
                                                          is_global=is_global, is_fixed=is_fixed, is_fixed_run=False,
                                                          fixed_value=0)
            final_parameters[0] = run_parameters

        if fit.is_valid_expression("A(t) = " + expression) and len(parameters) > 1:
            lambda_expression = fit.FitExpression(expression)
            return lambda_expression, final_parameters
        else:
            return None, {}

    def _get_ordered_run_ids(self):
        numeric_const_pattern = r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"

        def field_key_func(run_id):
            for run in self._runs:
                if run.id == run_id:
                    try:
                        return float(re.findall(numeric_const_pattern, run.meta[files.FIELD_KEY])[0])
                    except IndexError:
                        return 0
            return 0

        def temp_key_func(run_id):
            for run in self._runs:
                if run.id == run_id:
                    try:
                        return float(re.findall(numeric_const_pattern, run.meta[files.TEMPERATURE_KEY])[0])
                    except IndexError:
                        return 0
            return 0

        def number_key_func(run_id):
            for run in self._runs:
                if run.id == run_id:
                    return float(re.findall(numeric_const_pattern, run.meta[files.RUN_NUMBER_KEY])[0])
            return 0

        keys = {
            files.FIELD_KEY: field_key_func,
            files.TEMPERATURE_KEY: temp_key_func,
            files.RUN_NUMBER_KEY: number_key_func
        }

        meta_key, ascending = self._view.get_batch_ordering()
        run_ids = self._view.get_checked_run_ids()

        return sorted(run_ids, key=keys[meta_key], reverse=not ascending)

    def _fit(self):
        self.__update_if_table_changes = False
        config = fit.FitConfig()

        # Check user input on fit equation and update config
        expression = self._view.get_expression()
        if not fit.is_valid_expression("A(t) = " + expression):
            WarningMessageDialog.launch(["Fit equation is invalid."])
            self._view.highlight_input_red(self._view.input_fit_equation, True)
            self.__update_if_table_changes = True
            return
        else:
            self._view.highlight_input_red(self._view.input_fit_equation, False)
        config.expression = expression

        # Check user input on parameters
        try:
            parameters = self._view.get_parameters()
        except ValueError:
            WarningMessageDialog.launch(["Parameter input is invalid."])
            self.__update_if_table_changes = True
            return

        for symbol, value, value_min, value_max, _, _, _, _, _ in parameters:
            if value_min > value_max:
                WarningMessageDialog.launch(["Lower bound is greater then upper bound for {}. ({:.5f} > {:.5f})".format(symbol, value_min, value_max)])
                self.__update_if_table_changes = True
                return
            elif value < value_min:
                WarningMessageDialog.launch(["Bounds for {} and its initial value are incompatible. ({:.5f} < {:.5f})".format(symbol, value, value_min)])
                self.__update_if_table_changes = True
                return
            elif value > value_max:
                WarningMessageDialog.launch(["Bounds for {} and its initial value are incompatible. ({:.5f} > {:.5f})".format(symbol, value, value_max)])
                self.__update_if_table_changes = True
                return

        # Check user input on runs and update config
        if self._view.check_batch_fit.isChecked():
            run_ids = self._get_ordered_run_ids()
        else:
            run_ids = self._view.get_checked_run_ids()

        if len(run_ids) == 0:  # User needs to select a run to fit
            WarningMessageDialog.launch(["Must select at least one run to fit to."])
            self._view.highlight_input_red(self._view.run_list, True)
            self.__update_if_table_changes = True
            return
        else:
            self._view.highlight_input_red(self._view.run_list, False)

        variables = {}
        fit_titles = {}
        data = OrderedDict()  # Ordered dict is important.
        for run_id in run_ids:
            for run in self._runs:
                if run.id == run_id:
                    fit_titles[run.id] = run.meta[files.TITLE_KEY]
                    if run.id in self._asymmetries.keys():
                        # We have to store references to all three instead of just the asymmetry because the
                        #   new process won't pick up those references.
                        data[run.id] = (self._asymmetries[run.id].time, self._asymmetries[run.id], self._asymmetries[run.id].uncertainty, run.meta)
                    else:
                        min_time = self._view.fit_spectrum_settings.get_min_time()
                        max_time = self._view.fit_spectrum_settings.get_max_time()
                        bin_size = self._view.fit_spectrum_settings.get_bin_from_input()
                        raw_asymmetry = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].raw().bin(bin_size).cut(min_time=min_time, max_time=max_time)
                        self._asymmetries[run.id] = raw_asymmetry
                        data[run.id] = (self._asymmetries[run.id].time, self._asymmetries[run.id], self._asymmetries[run.id].uncertainty, run.meta)

                    run_parameters = {}
                    for symbol, value, value_min, value_max, value_output, value_uncertainty, is_fixed, \
                            is_global, run_dependent_dict in parameters:

                        is_fixed_run, fixed_value = (run_dependent_dict[run.id][1],
                                                     run_dependent_dict[run.id][2])

                        run_parameters[symbol] = fit.FitParameter(symbol=symbol, value=value, lower=value_min, upper=value_max,
                                                                  is_global=is_global, is_fixed=is_fixed, is_fixed_run=is_fixed_run,
                                                                  fixed_value=fixed_value)
                    variables[run.id] = run_parameters

        config.data = data
        config.batch = self._view.check_batch_fit.isChecked()
        config.parameters = variables
        config.titles = fit_titles
        config.set_flags(0)
        self.__logger.info(str(config))

        # Fit to spec
        worker = FitWorker(config)
        worker.signals.result.connect(self._update_fit_changes)
        worker.signals.error.connect(lambda e: self.__logger.error(e))
        worker.signals.error.connect(lambda error_message: WarningMessageDialog.launch([error_message]))
        self._threadpool.start(worker)

        LoadingDialog.launch("Your fit is running!", worker)

    def _new_empty_fit(self):
        self.__expression = None
        self.__variable_groups = []
        self._view.clear()

    def _selection_changed(self):
        self.__update_if_table_changes = False

        selected_data = self._view.support_panel.tree.get_selected_data()
        if selected_data is None:
            self.__update_if_table_changes = True
            return

        if type(selected_data) == objects.Fit:
            for i in range(self._view.run_list.count()):
                item = self._view.run_list.item(i)
                if item.identifier == selected_data.run_id:
                    item.setCheckState(qt_constants.Checked)
                else:
                    item.setCheckState(qt_constants.Unchecked)

            self._view.clear_parameters(selected_data.parameters.keys())
            for symbol, parameter in selected_data.parameters.items():
                self._view.add_parameter(symbol=parameter.symbol, config_value=parameter.value,
                                         config_lower=parameter.lower, config_upper=parameter.upper,
                                         config_fixed=parameter.is_fixed, batch_global=parameter.is_global,
                                         batch_run_dependent=parameter.is_fixed_run, batch_value=parameter.fixed_value,
                                         output_value=parameter.output, output_uncertainty=parameter.uncertainty,
                                         run_id=selected_data.run_id)

            # Fits loaded from a file may not have a run associated with them yet.
            run = None if 'UNLINKED' in selected_data.run_id else self._run_service.get_runs_by_ids([selected_data.run_id])[0]

            try:
                self._view.support_panel.input_file_name.setText('{}_fit.txt'.format(run.meta[files.RUN_NUMBER_KEY]))
            except (KeyError, AttributeError):
                self._view.support_panel.input_file_name.setText('{}_fit.txt'.format(selected_data.title))

            self._view.support_panel.input_folder_name.setText(self._system_service.get_last_used_directory())
            self.__expression = selected_data.expression
            self.__variable_groups = {selected_data.run_id: selected_data.parameters}
            self._view.input_fit_equation.setText(str(selected_data.string_expression))
            self._update_display()

        elif type(selected_data) == objects.FitDataset:
            for i in range(self._view.run_list.count()):
                item = self._view.run_list.item(i)
                if item.identifier in selected_data.fits.keys():
                    item.setCheckState(qt_constants.Checked)
                else:
                    item.setCheckState(qt_constants.Unchecked)

            for run_id, f in selected_data.fits.items():
                self._view.clear_parameters(f.parameters.keys())
                for symbol, parameter in f.parameters.items():
                    self._view.add_parameter(symbol=parameter.symbol, config_value=parameter.value,
                                             config_lower=parameter.lower, config_upper=parameter.upper,
                                             config_fixed=parameter.is_fixed, batch_global=parameter.is_global,
                                             batch_run_dependent=parameter.is_fixed_run, batch_value=parameter.fixed_value,
                                             output_value=parameter.output, output_uncertainty=parameter.uncertainty,
                                             run_id=run_id)

            fits = list(selected_data.fits.values())
            self._view.support_panel.input_file_name.setText('{}_fit.txt'.format(selected_data.id))
            self._view.support_panel.input_folder_name.setText(self._system_service.get_last_used_directory())
            self._view.input_fit_equation.setText(str(fits[0].string_expression))
            self.__expression = fits[0].expression
            self.__variable_groups = {f.run_id: f.parameters for f in fits}
            self._update_display()

        else:
            self._view.run_list.setEnabled(True)
            self._view.table_parameters.setEnabled(True)

        self.__update_if_table_changes = True

    def _update_fit_changes(self, dataset):
        self._fit_service.add_dataset([dataset])
        self._update_alphas(dataset)
        self.__update_if_table_changes = False
        self._view.select_first_fit_from_dataset(dataset.id)
        self.__update_if_table_changes = False
        self._view.select_top_child_run(dataset.id)
        self.__update_if_table_changes = True
        self._update_display()

    def _update_alphas(self, dataset):
        ids = []
        alphas = []
        for run_id, f in dataset.fits.items():
            ids.append(run_id)
            alphas.append(f.parameters[fit.ALPHA].value)

        if len(ids) > 0:
            self._run_service.update_alphas(ids, alphas)

    def update(self):
        runs = []
        for run in self._run_service.get_loaded_runs():
            if run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] is not None:
                runs.append(run)
        self._runs = runs
        self._view.update_run_table(runs)


class FitWorker(QtCore.QRunnable):
    def __init__(self, config: fit.FitConfig):
        super(FitWorker, self).__init__()
        self.config = config
        self.signals = FitSignals()
        self.__engine = fit.FitEngine()
        self.__pool = futures.ProcessPoolExecutor()
        self.__process = None

    @QtCore.pyqtSlot()
    def run(self):
        try:
            # Start a separate process to run fits
            self.__process = self.__pool.submit(self.__engine.fit, self.config)

            # Wait on process to finish
            x = futures.wait([self.__process], return_when=futures.ALL_COMPLETED)

            dataset = x.done.pop().result()

            for run_id, fit_data in dataset.fits.items():
                fit_data.expression = fit.FitExpression(fit_data.string_expression)

        except Exception as e:
            self.signals.error.emit("Error Running Fit: ({})".format(str(e)))
        else:
            self.signals.result.emit(dataset)
        finally:
            self.signals.finished.emit()


class FitSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    result = QtCore.pyqtSignal(objects.FitDataset)
    error = QtCore.pyqtSignal(str)
    progress = QtCore.pyqtSignal(int)
