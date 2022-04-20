import logging
import re
from collections import OrderedDict
from concurrent import futures
import functools

import darkdetect
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from app.resources import resources
from app.gui.dialogs.dialog_misc import WarningMessageDialog, LoadingDialog
from app.gui.dialogs.dialog_write_fit import WriteFitDialog
from app.util import qt_widgets, qt_constants, report
from app.model import objects, fit, files, services
from app.gui.gui import PanelPresenter, Panel


class FittingPanel(Panel):
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
                    menu.addAction(action[0], functools.partial(action[1], self.selectedItems(), self))

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

                data = []
                while iterator.value():
                    if isinstance(iterator.value().model, objects.Fit) or isinstance(iterator.value().model,
                                                                                     objects.FitDataset):
                        data.append(iterator.value().model)
                    iterator += 1
                return data

            def get_parent_of_selected_data(self):
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Selected)

                data = set()
                while iterator.value():
                    if isinstance(iterator.value().model, objects.Fit):
                        data.add(iterator.value().parent().model)
                    iterator += 1
                return data

            def set_colors(self, colors):
                iterator = QtWidgets.QTreeWidgetItemIterator(self)
                while iterator.value():
                    if isinstance(iterator.value().model, objects.Fit):
                        run_id = iterator.value().model.run_id
                        if run_id in colors:
                            iterator.value().set_color(colors[run_id])
                        else:
                            iterator.value().set_color('#FFFFFF')
                    iterator += 1

                self.repaint()

        class TreeManager(PanelPresenter):
            def __init__(self, view):
                super().__init__(view)
                self.__view = view
                self.__logger = logging.getLogger(__name__)
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
                super().__init__([dataset.title])
                self.model = dataset
                self.__selected_items = None
                self.__fit_service = services.FitService()
                self.__parent = None
                self.setFlags(self.flags() | qt_constants.ItemIsEditable)
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

            def set_color(self, color):
                pixmap = QtGui.QPixmap(100, 100)
                pixmap.fill(QtGui.QColor(color))
                qicon = QtGui.QIcon(pixmap)
                qcolor = QtWidgets.QToolButton()
                qcolor.setIcon(qicon)
                self.setIcon(0, qicon)

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

                expressions = set([i.model.string_expression for i in items])

                if len(expressions) > 1:
                    WarningMessageDialog.launch("Can not save collection of fits with more then one fit expression at "
                                                "the same time.")
                    return

                dataset.expression = expressions.pop()

                WriteFitDialog.launch(dataset=dataset)

        def __init__(self):
            super().__init__()
            self.tree = FittingPanel.SupportPanel.Tree()
            self.setTitleBarWidget(QtWidgets.QWidget())
            main_layout = QtWidgets.QVBoxLayout()

            self.new_button = qt_widgets.StyleTwoButton("New Empty Fit")
            self.reset_button = qt_widgets.StyleOneButton("Reset")
            self.save_button = qt_widgets.StyleOneButton("Save")
            self.button_lookup_folder = qt_widgets.StyleTwoButton("Folder")

            self.new_button.setToolTip('Create a new empty fit')
            self.save_button.setToolTip("Save the currently highlighted fits")
            self.button_lookup_folder.setToolTip('Select folder')

            self.input_file_name = QtWidgets.QLineEdit()
            self.input_folder_name = QtWidgets.QLineEdit()

            self.group_save_results = QtWidgets.QGroupBox("Save")

            self.button_lookup_folder.setFixedWidth(60)

            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(self.new_button)
            hbox.addWidget(self.save_button)
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
            self.__system_service = services.SystemService()
            self._draw_pending = True
            self._is_drawing = True
            self._settings = settings

            FigureCanvas.__init__(self, Figure())
            axes = self.figure.subplots(1, 1)
            self.axes_time = axes

            self._style = self.set_stylesheet()
            self.set_blank()

        def set_stylesheet(self):
            style = self.__system_service.get_theme_preference()
            if style == self.__system_service.Themes.DEFAULT:
                if darkdetect.isDark():
                    style = self.__system_service.Themes.DARK
                else:
                    style = self.__system_service.Themes.LIGHT
            if style == self.__system_service.Themes.DARK:
                self.figure.set_facecolor(resources.DARK_COLOR)
                self.axes_time.set_facecolor(resources.DARK_COLOR)
            elif style == self.__system_service.Themes.LIGHT:
                self.figure.set_facecolor(resources.LIGHT_COLOR)
                self.axes_time.set_facecolor(resources.LIGHT_COLOR)
            self.axes_time.figure.canvas.draw()
            self._style = style
            return style

        def set_blank(self):
            tick_color = resources.LIGHT_COLOR
            text_color = resources.DARK_COLOR
            if self._style == self.__system_service.Themes.DARK:
                tick_color = resources.DARK_COLOR
                text_color = resources.LIGHT_COLOR
            self.axes_time.clear()
            title_font_size = 12
            self.axes_time.spines['right'].set_visible(False)
            self.axes_time.spines['top'].set_visible(False)
            self.axes_time.spines['left'].set_visible(False)
            self.axes_time.spines['bottom'].set_visible(False)
            self.axes_time.set_xlabel("Select runs to see live asymmetry and fit.",
                                      fontsize=title_font_size)
            self.axes_time.xaxis.label.set_color(text_color)
            self.axes_time.tick_params(axis='x', colors=tick_color)
            self.axes_time.tick_params(axis='y', colors=tick_color)
            self.axes_time.set_facecolor(tick_color)

        def set_style(self):
            tick_color = resources.DARK_COLOR
            background_color = resources.LIGHT_COLOR
            if self._style == self.__system_service.Themes.DARK:
                tick_color = resources.LIGHT_COLOR
                background_color = resources.DARK_COLOR
            self.axes_time.tick_params(axis='x', colors=tick_color)
            self.axes_time.tick_params(axis='y', colors=tick_color)

            title_font_size = 12
            self.axes_time.spines['right'].set_visible(False)
            self.axes_time.spines['top'].set_visible(False)
            self.axes_time.spines['left'].set_visible(True)
            self.axes_time.spines['bottom'].set_visible(True)
            self.axes_time.spines['left'].set_color(tick_color)
            self.axes_time.spines['bottom'].set_color(tick_color)
            self.axes_time.set_xlabel("Time (" + chr(956) + "s)", fontsize=title_font_size)
            self.axes_time.set_ylabel("Asymmetry", fontsize=title_font_size)
            self.axes_time.xaxis.label.set_color(tick_color)
            self.axes_time.yaxis.label.set_color(tick_color)
            self.axes_time.set_facecolor(background_color)
            self.axes_time.legend(loc='upper right')
            self.axes_time.figure.canvas.draw()
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
            y_min = min_asymmetry - abs(min_asymmetry * 0.1)
            y_max = max_asymmetry + abs(max_asymmetry * 0.1)
            self.axes_time.set_ylim(y_min, y_max)

            try:
                x_min = self._settings.get_min_time()
                x_max = self._settings.get_max_time()
            except ValueError:
                WarningMessageDialog.launch(["Invalid asymmetry limits."])
                return
            self.axes_time.set_xlim(x_min, x_max)

        def finish_plotting(self, remove_legend=False):
            self.set_style()
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
            self._label_slider_bin = QtWidgets.QLabel('')
            self._label_input_bin = QtWidgets.QLabel('Time Bins (ns)')

            self.slider_bin = QtWidgets.QSlider(qt_constants.Horizontal)
            self.input_bin = QtWidgets.QLineEdit()

            self.slider_bin.setToolTip('Time bins (ns)')

            self._label_time = QtWidgets.QLabel('Time')
            self._label_time_xmin = QtWidgets.QLabel('XMin')
            self._label_time_xmax = QtWidgets.QLabel('XMax')

            self.input_time_xmin = QtWidgets.QLineEdit()
            self.input_time_xmax = QtWidgets.QLineEdit()

            self._set_widget_attributes()
            self._set_widget_tooltips()
            self._set_widget_dimensions()
            self._set_widget_layout()

        def _set_widget_attributes(self):
            self.input_time_xmin.setText("0")
            self.input_time_xmax.setText("8")

            self.slider_bin.setMinimum(0)
            self.slider_bin.setMaximum(500)
            self.slider_bin.setValue(150)
            self.slider_bin.setTickPosition(QtWidgets.QSlider.TicksBothSides)
            self.slider_bin.setTickInterval(20)

            self.input_bin.setText(str(self.slider_bin.value()))
            self.input_bin.returnPressed.connect(lambda: self._update_bin(False))
            self.slider_bin.sliderMoved.connect(lambda: self._update_bin(True))

        def _set_widget_tooltips(self):
            self.input_time_xmin.setToolTip('The minimum time bound of the asymmetry to be used in the fit')
            self.input_time_xmax.setToolTip('The maximum time bound of the asymmetry to be used in the fit')
            self.slider_bin.setToolTip('The bin size of the asymmetry you would like to use in the fit')
            self.input_bin.setToolTip('The bin size of the asymmetry you would like to use in the fit')

        def _set_widget_dimensions(self):
            box_size = 80
            self.input_time_xmin.setMaximumWidth(box_size)
            self.input_time_xmax.setMaximumWidth(box_size)
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

            self.setLayout(main_layout)

        def _update_bin(self, slider_is_most_accurate):
            if slider_is_most_accurate:
                self.input_bin.setText(str(self.slider_bin.value()))
            else:
                try:
                    self.slider_bin.setValue(int(float(self.input_bin.text())))
                except ValueError:
                    pass

        def get_max_time(self):
            return float(self.input_time_xmax.text())

        def get_min_time(self):
            return float(self.input_time_xmin.text())

        def get_bin_from_input(self):
            return float(self.input_bin.text())

        def get_bin_from_slider(self):
            return float(self.slider_bin.value())

        def set_max_time(self, value):
            self.input_time_xmax.setText('{0:.3f}'.format(value))

        def set_min_time(self, value):
            self.input_time_xmin.setText('{0:.3f}'.format(value))

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
        OUTPUT_VALUE_COLUMN = 0
        UNCERTAINTY_COLUMN = 1

        def __init__(self):
            super(FittingPanel.ParameterTable, self).__init__()
            self.config_table = QtWidgets.QTableWidget()
            self.batch_table = QtWidgets.QTableWidget()
            self.output_table = QtWidgets.QTableWidget()
            self.goodness_display = QtWidgets.QLineEdit()

            self.addTab(self.config_table, "Config")
            self.addTab(self.batch_table, "Batch")

            output_widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(self.output_table)
            goodness_row = QtWidgets.QHBoxLayout()
            goodness_row.addWidget(QtWidgets.QLabel("Reduced \u03C7\u00B2"))
            goodness_row.addWidget(self.goodness_display)
            layout.addLayout(goodness_row)
            output_widget.setLayout(layout)
            self.addTab(output_widget, "Output")

            self._set_attributes()
            self._set_tooltips()

        def _set_attributes(self):
            self.config_table.setColumnCount(4)
            self.config_table.setHorizontalHeaderLabels(['Value', 'Min', 'Max', 'Fixed'])
            self.config_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            self.config_table.horizontalHeader().setSectionResizeMode(self.VALUE_COLUMN,
                                                                      QtWidgets.QHeaderView.Stretch)
            self.config_table.horizontalHeader().setSectionResizeMode(self.MIN_COLUMN, QtWidgets.QHeaderView.Stretch)
            self.config_table.horizontalHeader().setSectionResizeMode(self.MAX_COLUMN, QtWidgets.QHeaderView.Stretch)
            self.config_table.horizontalHeader().setSectionResizeMode(self.FIXED_COLUMN, QtWidgets.QHeaderView.Stretch)

            self.batch_table.setColumnCount(2)
            self.batch_table.setHorizontalHeaderLabels(['Global', 'Run-Specific'])
            self.batch_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
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

            self.goodness_display.setEnabled(False)

        def _set_tooltips(self):
            self.config_table.horizontalHeaderItem(0).setToolTip("The starting value of a parameter")
            self.config_table.horizontalHeaderItem(1).setToolTip("The lower bound for this parameter")
            self.config_table.horizontalHeaderItem(2).setToolTip("The upper bound for this parameter")
            self.config_table.horizontalHeaderItem(3).setToolTip("If checked, this parameter will be fixed at the value specified")

            self.batch_table.horizontalHeaderItem(0).setToolTip("If checked, this parameter will be fit as a single parameter across all datasets")
            self.batch_table.horizontalHeaderItem(1).setToolTip("If checked, you can independently specify the values in the config table for this parameter for each dataset")

            self.output_table.horizontalHeaderItem(0).setToolTip("The output of the fit for this parameter. If * then multiple fits with different values are selected")
            self.output_table.horizontalHeaderItem(1).setToolTip("The uncertainty of the fit for this parameter. If * then multiple fits with different values are selected")

            self.goodness_display.setToolTip(f"The reduced {fit.CHI}{fit.SQUARE} value for this fit")

    def __init__(self):
        super(FittingPanel, self).__init__()
        self.__logger = logging.getLogger(__name__)

        self.support_panel = FittingPanel.SupportPanel()

        self.parameter_table = self.ParameterTable()

        self.mathematical_font = QtGui.QFont()
        self.mathematical_font.setFamily("Georgia")

        self.input_fit_equation = QtWidgets.QLineEdit()
        self.input_user_equation = QtWidgets.QLineEdit()
        self.input_user_equation_name = QtWidgets.QLineEdit()
        self.option_preset_fit_equations = QtWidgets.QComboBox()
        self.option_user_fit_equations = QtWidgets.QComboBox()
        self.option_run_ordering = QtWidgets.QComboBox()
        self.option_ascending = QtWidgets.QComboBox()

        self.fit_spectrum_settings = FittingPanel.PlotControl()
        self.fit_display = FittingPanel.PlotDisplay(self.fit_spectrum_settings)
        self.special_characters = qt_widgets.CollapsibleBox("Special Characters", background='#FFFFFF')
        self.special_characters.toggle_button.released.connect(self.special_characters.on_pressed)

        self.table_parameters = QtWidgets.QTableWidget()
        self.run_list = qt_widgets.ListWidget()

        self.button_fit = qt_widgets.StyleThreeButton("Fit")
        self.button_insert_preset_equation = qt_widgets.StyleTwoButton("Insert")
        self.button_insert_user_equation = qt_widgets.StyleTwoButton("Insert")
        self.button_save_user_equation = qt_widgets.StyleTwoButton("Save")
        self.button_plot = qt_widgets.StyleTwoButton("Plot")

        self.label_global_plus = QtWidgets.QLabel("Global+")
        self.label_ordering = QtWidgets.QLabel("Order by")
        self.label_use_previous = QtWidgets.QLabel("Use Previous Run")
        self.label_expression_start = QtWidgets.QLabel("A(t) = ")
        self.label_batch = QtWidgets.QLabel("Sequential")

        self.check_batch_fit = QtWidgets.QCheckBox()

        self.insert_phi = qt_widgets.StyleTwoButton(fit.PHI)
        self.insert_alpha = qt_widgets.StyleTwoButton(fit.ALPHA)
        self.insert_sigma = qt_widgets.StyleTwoButton(fit.SIGMA)
        self.insert_naught = qt_widgets.StyleTwoButton(fit.NAUGHT)
        self.insert_lambda = qt_widgets.StyleTwoButton(fit.LAMBDA)
        self.insert_delta = qt_widgets.StyleTwoButton(fit.DELTA)
        self.insert_beta = qt_widgets.StyleTwoButton(fit.BETA)
        self.insert_pi = qt_widgets.StyleOneButton(fit.PI)
        self.insert_nu = qt_widgets.StyleOneButton(fit.NU)

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
        self._set_tooltips()

        self._presenter = FitTabPresenter(self)
        self._line_edit_style = self.input_fit_equation.styleSheet()

    def _set_tooltips(self):
        self.button_fit.setToolTip('Run fit')
        self.button_insert_preset_equation.setToolTip('Insert predefined function')
        self.button_insert_user_equation.setToolTip('Insert user defined function')
        self.button_save_user_equation.setToolTip('Save user defined function')
        self.button_plot.setToolTip('Plot data')

        self.input_fit_equation.setToolTip('Type the equation you would like to use for the fit here')
        self.input_user_equation.setToolTip('You can save an equation here for future use')
        self.input_user_equation_name.setToolTip('You must specify a name for your equation')
        self.option_preset_fit_equations.setToolTip('A list of pre defined equations you can use in your fit equation')
        self.option_user_fit_equations.setToolTip('A list of equations you have saved')
        self.option_run_ordering.setToolTip('If you are running the fit sequentially, this will specify the value that will determine the order of the fits')
        self.option_ascending.setToolTip('If you are running the fit sequentially, you can control whether the fits should be done in ascending or descending order')

        self.run_list.setToolTip('Here you can select the runs to be included in this fit')

        self.check_batch_fit.setToolTip('If checked, the fits will be run sequentially with the output of the previous fit being used as the input for the next')
        self.label_batch.setToolTip('If checked, the fits will be run sequentially with the output of the previous fit being used as the input for the next')

        self.insert_phi.setToolTip('Phi')
        self.insert_alpha.setToolTip('Alpha')
        self.insert_sigma.setToolTip('Sigma')
        self.insert_naught.setToolTip('Naught')
        self.insert_lambda.setToolTip('Lambda')
        self.insert_delta.setToolTip('Delta')
        self.insert_beta.setToolTip('Beta')
        self.insert_pi.setToolTip('Pi')
        self.insert_nu.setToolTip('Nu')

    def _set_widget_attributes(self):
        # self.run_list.setSelectionMode(qt_constants.ExtendedSelection)
        # self.run_list.setContextMenuPolicy(qt_constants.CustomContextMenu)

        self.option_preset_fit_equations.addItems(list(fit.EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItems(list(fit.USER_EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItem("None")
        self.option_run_ordering.addItems([files.FIELD_KEY, files.TEMPERATURE_KEY, files.RUN_NUMBER_KEY])
        self.option_ascending.addItems(['Ascending', 'Descending'])

        self.input_user_equation_name.setPlaceholderText("Function Name")
        self.input_user_equation.setPlaceholderText("Function (e.g. \"\u03B2 * (t + \u03BB)\")")
        self.input_fit_equation.setPlaceholderText("Fit Equation")

        self.insert_phi.setFont(self.mathematical_font)
        self.insert_alpha.setFont(self.mathematical_font)
        self.insert_sigma.setFont(self.mathematical_font)
        self.insert_naught.setFont(self.mathematical_font)
        self.insert_lambda.setFont(self.mathematical_font)
        self.insert_delta.setFont(self.mathematical_font)
        self.insert_beta.setFont(self.mathematical_font)
        self.insert_pi.setFont(self.mathematical_font)
        self.insert_nu.setFont(self.mathematical_font)
        self.input_fit_equation.setFont(self.mathematical_font)
        self.label_expression_start.setFont(self.mathematical_font)
        self.input_user_equation.setFont(self.mathematical_font)

        self.option_ascending.setEnabled(False)
        self.option_run_ordering.setEnabled(False)
        self.label_global_plus.setEnabled(True)
        self.label_ordering.setEnabled(False)
        self.label_use_previous.setEnabled(False)

    def _set_widget_dimensions(self):
        self.button_fit.setFixedWidth(60)
        self.button_fit.setFixedHeight(60)
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
        self.insert_nu.setFixedWidth(30)

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
        row.addWidget(self.input_user_equation, 2)
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
        row.addWidget(self.label_expression_start)
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
        row.addWidget(self.insert_nu)
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

    def get_row(self, j):
        item_symbol = self.parameter_table.config_table.verticalHeaderItem(j)
        if item_symbol is None:
            return None
        symbol = self.parameter_table.config_table.verticalHeaderItem(j).text()

        try:
            # Get the value of the parameter from the table as a float
            item_value = self.parameter_table.config_table.item(j, self.parameter_table.VALUE_COLUMN)
            if item_value is None:
                return None
            else:
                item_text = item_value.text()
                if item_text != '*':  # '*' indicates multiple unique values for selected runs
                    value = float(item_text)
                else:
                    value = '*'

            # Get the lower bound of the parameter from the table as a float
            item_min = self.parameter_table.config_table.item(j, self.parameter_table.MIN_COLUMN)
            if item_min is None:
                return None
            else:
                item_text = item_min.text()
                if item_text != '*':
                    min_value = float(item_text)
                else:
                    min_value = '*'

            # Get the upper bound of the parameter from the table as a float
            item_max = self.parameter_table.config_table.item(j, self.parameter_table.MAX_COLUMN)
            if item_max is None:
                return None
            else:
                item_text = item_max.text()
                if item_text != '*':
                    max_value = float(item_text)
                else:
                    max_value = '*'

        except ValueError:  # Indicates that the user did not provide input which could be cast to float (invalid)
            self.highlight_input_red(self.parameter_table.config_table, True)
            return None

        # Clear red outline of table (if last input was invalid)
        self.highlight_input_red(self.parameter_table.config_table, False)

        # Get the boolean indicating if the parameter is fixed from the table
        item_fixed = self.parameter_table.config_table.cellWidget(j, self.parameter_table.FIXED_COLUMN)
        if item_fixed is None:
            return None
        else:
            # Check if the box is partially checked (indicating there are conflicting values)
            check_state = item_fixed.findChild(QtWidgets.QCheckBox).checkState()
            is_fixed = check_state == qt_constants.Checked if check_state != qt_constants.PartiallyChecked else '*'

        return symbol, value, min_value, max_value, is_fixed

    def createSupportPanel(self) -> QtWidgets.QDockWidget:
        return self.support_panel

    def _create_check_box_for_table(self, checked=None, connect=None, partial=None):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        check = QtWidgets.QCheckBox()

        if connect:
            check.stateChanged.connect(connect)

        check_state = qt_constants.Checked if checked else qt_constants.Unchecked

        if partial:
            check_state = qt_constants.PartiallyChecked

        check.setCheckState(check_state)
        layout.addWidget(check)
        layout.setAlignment(qt_constants.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        return widget

    def add_parameter(self, symbol, config_value=None, config_lower=None,
                      config_upper=None, config_fixed=None, batch_global=None,
                      batch_run_dependent=None, batch_value: float = None, output_value=None,
                      output_uncertainty=None, run_id: str = None):

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
                    item_value.setText(config_value) if config_value == '*' else item_value.setText(
                        '{:.5f}'.format(float(config_value)))
                    self.parameter_table.config_table.setItem(i, self.ParameterTable.VALUE_COLUMN, item_value)

                if config_lower is not None:
                    item_lower = QtWidgets.QTableWidgetItem()
                    item_lower.setText(config_lower) if config_lower == '*' else item_lower.setText(
                        '{:.5f}'.format(float(config_lower)))
                    self.parameter_table.config_table.setItem(i, self.ParameterTable.MIN_COLUMN, item_lower)

                if config_upper is not None:
                    item_upper = QtWidgets.QTableWidgetItem()
                    item_upper.setText(config_upper) if config_upper == '*' else item_upper.setText(
                        '{:.5f}'.format(float(config_upper)))
                    self.parameter_table.config_table.setItem(i, self.ParameterTable.MAX_COLUMN, item_upper)

                if config_fixed is not None:
                    if config_fixed == '*':
                        item_fixed = self._create_check_box_for_table(
                            connect=self._presenter.update_parameter_table_states,
                            partial=True)
                    else:
                        item_fixed = self._create_check_box_for_table(checked=config_fixed,
                                                                      connect=self._presenter.update_parameter_table_states)

                    self.parameter_table.config_table.setCellWidget(i, self.ParameterTable.FIXED_COLUMN, item_fixed)

        if not in_table:
            self.parameter_table.config_table.setRowCount(n + 1)

            item_symbol = QtWidgets.QTableWidgetItem()
            item_symbol.setText(symbol)
            self.parameter_table.config_table.setVerticalHeaderItem(n, item_symbol)

            if config_value is not None:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText(config_value) if config_value == '*' else item_value.setText(
                    '{:.5f}'.format(float(config_value)))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.VALUE_COLUMN, item_value)
            else:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText('1')
                self.parameter_table.config_table.setItem(n, self.ParameterTable.VALUE_COLUMN, item_value)

            if config_lower is not None:
                item_lower = QtWidgets.QTableWidgetItem()
                item_lower.setText(config_lower) if config_lower == '*' else item_lower.setText(
                    '{:.5f}'.format(float(config_lower)))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MIN_COLUMN, item_lower)
            else:
                item_lower = QtWidgets.QTableWidgetItem()
                item_lower.setText(str(-np.inf))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MIN_COLUMN, item_lower)

            if config_upper is not None:
                item_upper = QtWidgets.QTableWidgetItem()
                item_upper.setText(config_upper) if config_upper == '*' else item_upper.setText(
                    '{:.5f}'.format(float(config_upper)))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MAX_COLUMN, item_upper)
            else:
                item_upper = QtWidgets.QTableWidgetItem()
                item_upper.setText(str(np.inf))
                self.parameter_table.config_table.setItem(n, self.ParameterTable.MAX_COLUMN, item_upper)

            if config_fixed is not None:
                if config_fixed == '*':
                    item_fixed = self._create_check_box_for_table(connect=self._presenter.update_parameter_table_states,
                                                                  partial=True)
                else:
                    item_fixed = self._create_check_box_for_table(checked=config_fixed,
                                                                  connect=self._presenter.update_parameter_table_states)

                self.parameter_table.config_table.setCellWidget(n, self.ParameterTable.FIXED_COLUMN, item_fixed)
            else:
                item_fixed = self._create_check_box_for_table(False, self._presenter.update_parameter_table_states)
                self.parameter_table.config_table.setCellWidget(n, self.ParameterTable.FIXED_COLUMN, item_fixed)

        n = self.parameter_table.batch_table.verticalHeader().count()

        in_table = False
        for i in range(n - 1, -1, -1):
            item = self.parameter_table.batch_table.verticalHeaderItem(i)

            if item is None:
                continue

            if symbol == item.text():
                in_table = True

                if batch_global is not None:
                    item_global = self._create_check_box_for_table(batch_global,
                                                                   connect=self._presenter._update_batch_table)
                    self.parameter_table.batch_table.setCellWidget(i, self.ParameterTable.GLOBAL_COLUMN, item_global)

                if batch_run_dependent is not None:
                    item_fixed = self._create_check_box_for_table(batch_run_dependent,
                                                                  connect=self._presenter._update_batch_table)
                    self.parameter_table.batch_table.setCellWidget(i, self.ParameterTable.FIXED_RUN_COLUMN, item_fixed)

        if not in_table:
            self.parameter_table.batch_table.setRowCount(n + 1)

            item_symbol = QtWidgets.QTableWidgetItem()
            item_symbol.setText(symbol)
            self.parameter_table.batch_table.setVerticalHeaderItem(n, item_symbol)

            if batch_global is not None:
                item_global = self._create_check_box_for_table(batch_global,
                                                               connect=self._presenter._update_batch_table)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.GLOBAL_COLUMN, item_global)
            else:
                item_global = self._create_check_box_for_table(False, connect=self._presenter._update_batch_table)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.GLOBAL_COLUMN, item_global)

            if batch_run_dependent is not None:
                item_fixed = self._create_check_box_for_table(batch_run_dependent,
                                                              connect=self._presenter._update_batch_table)
                self.parameter_table.batch_table.setCellWidget(n, self.ParameterTable.FIXED_RUN_COLUMN, item_fixed)
            else:
                item_fixed = self._create_check_box_for_table(False, connect=self._presenter._update_batch_table)
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
                item_value.setText(output_value) if output_value == '*' else item_value.setText(
                    '{:.5f}'.format(float(output_value)))
                self.parameter_table.output_table.setItem(n, self.ParameterTable.OUTPUT_VALUE_COLUMN, item_value)

            if output_uncertainty is not None:
                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText(output_uncertainty) if output_uncertainty == '*' else item_value.setText(
                    '{:.5f}'.format(float(output_uncertainty)))
                self.parameter_table.output_table.setItem(n, self.ParameterTable.UNCERTAINTY_COLUMN, item_value)

    def clear_parameters(self, symbols=None):
        n = self.parameter_table.config_table.verticalHeader().count()

        for i in range(n - 1, -1, -1):
            item = self.parameter_table.config_table.verticalHeaderItem(i)

            if item is None or (symbols is not None and item.text() in symbols):
                continue

            self.parameter_table.config_table.removeRow(i)

        n = self.parameter_table.batch_table.verticalHeader().count()

        for i in range(n - 1, -1, -1):
            item = self.parameter_table.batch_table.verticalHeaderItem(i)

            if item is None or (symbols is not None and item.text() in symbols):
                continue

            self.parameter_table.batch_table.removeRow(i)

        n = self.parameter_table.output_table.verticalHeader().count()

        for i in range(n - 1, -1, -1):
            item = self.parameter_table.output_table.verticalHeaderItem(i)

            if item is None or (symbols is not None and item.text() in symbols):
                continue

            self.parameter_table.output_table.removeRow(i)

    def set_output_uncertainty_for_symbol(self, symbol, output, uncertainty):
        for i in range(self.parameter_table.output_table.verticalHeader().count()):
            item = self.parameter_table.output_table.verticalHeaderItem(i)

            if item is None:
                continue

            if symbol == item.text():
                if output is not None:
                    item_value = QtWidgets.QTableWidgetItem()
                    item_value.setText(output) if output == '*' else item_value.setText('{:.5f}'.format(float(output)))
                    self.parameter_table.output_table.setItem(i, self.ParameterTable.OUTPUT_VALUE_COLUMN, item_value)

                if uncertainty is not None:
                    item_value = QtWidgets.QTableWidgetItem()
                    item_value.setText(uncertainty) if uncertainty == '*' else item_value.setText(
                        '{:.5f}'.format(float(uncertainty)))
                    self.parameter_table.output_table.setItem(i, self.ParameterTable.UNCERTAINTY_COLUMN, item_value)

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

    def get_batch_ordering(self):
        return self.option_run_ordering.currentText(), self.option_ascending.currentText() == 'Ascending'

    def get_expression(self):
        return self.input_fit_equation.text()

    def set_goodness(self, goodness):
        try:
            self.parameter_table.goodness_display.setText("{:.4f}".format(goodness))
        except ValueError:
            self.parameter_table.goodness_display.setText(str(goodness))

    def is_run_dependent(self):
        is_run_dependent = False

        for i in range(self.parameter_table.batch_table.rowCount()):
            item_fixed = self.parameter_table.batch_table.cellWidget(i, self.parameter_table.FIXED_RUN_COLUMN)
            is_run_dependent = is_run_dependent or (
                        item_fixed is not None and item_fixed.findChild(QtWidgets.QCheckBox).checkState() > 0)

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
            if self.support_panel.tree.topLevelItem(i).model.title == dataset_id:
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


class FitTabPresenter(PanelPresenter):
    def __init__(self, view: FittingPanel):
        super().__init__(view)

        self.__parameter_table_states = {}
        self.__update_states = True

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
        self.__logger = logging.getLogger(__name__)

    def _set_callbacks(self):
        self._view.parameter_table.config_table.itemChanged.connect(self._on_config_table_changed)
        self._view.run_list.itemChanged.connect(self._on_run_list_changed)
        self._view.run_list.itemSelectionChanged.connect(self._on_run_list_selection_changed)
        self._view.check_batch_fit.stateChanged.connect(self._on_batch_options_changed)

        self._view.support_panel.tree.itemSelectionChanged.connect(self._on_fit_selection_changed)
        self._view.support_panel.save_button.released.connect(self._on_save_clicked)
        self._view.input_fit_equation.textChanged.connect(self._on_function_input_changed)
        self._view.button_insert_preset_equation.released.connect(self._on_insert_pre_defined_function_clicked)
        self._view.button_insert_user_equation.released.connect(self._on_insert_user_defined_function_clicked)
        self._view.button_save_user_equation.released.connect(self._on_save_user_defined_function_clicked)
        self._view.insert_sigma.released.connect(lambda: self._on_insert_character_clicked(fit.SIGMA))
        self._view.insert_pi.released.connect(lambda: self._on_insert_character_clicked(fit.PI))
        self._view.insert_phi.released.connect(lambda: self._on_insert_character_clicked(fit.PHI))
        self._view.insert_naught.released.connect(lambda: self._on_insert_character_clicked(fit.NAUGHT))
        self._view.insert_lambda.released.connect(lambda: self._on_insert_character_clicked(fit.LAMBDA))
        self._view.insert_delta.released.connect(lambda: self._on_insert_character_clicked(fit.DELTA))
        self._view.insert_alpha.released.connect(lambda: self._on_insert_character_clicked(fit.ALPHA))
        self._view.insert_beta.released.connect(lambda: self._on_insert_character_clicked(fit.BETA))
        self._view.insert_nu.released.connect(lambda: self._on_insert_character_clicked(fit.NU))
        self._view.fit_spectrum_settings.input_time_xmax.returnPressed.connect(self._on_spectrum_settings_changed)
        self._view.fit_spectrum_settings.input_time_xmin.returnPressed.connect(self._on_spectrum_settings_changed)
        self._view.fit_spectrum_settings.input_bin.returnPressed.connect(self._on_spectrum_settings_changed)
        self._view.fit_spectrum_settings.slider_bin.sliderMoved.connect(self._on_spectrum_settings_changed)
        self._view.button_plot.released.connect(self._on_plot_clicked)
        self._view.parameter_table.config_table.itemChanged.connect(self._on_parameter_table_changed)
        self._view.parameter_table.batch_table.itemChanged.connect(self._on_parameter_table_changed)
        self._view.parameter_table.output_table.itemChanged.connect(self._on_parameter_table_changed)
        self._view.button_fit.released.connect(self._on_fit_clicked)
        self._view.support_panel.new_button.released.connect(self._on_new_clicked)
        self._system_service.signals.theme_changed.connect(self._on_theme_changed)

    @QtCore.pyqtSlot()
    def _on_save_clicked(self):
        items = self._view.support_panel.tree.get_selected_data()
        if len(items) == 0:
            WarningMessageDialog.launch(["No fits selected."])
            return

        types = set([type(i) for i in items])

        if len(types) > 1:
            WarningMessageDialog.launch(["Invalid selection, please select a parent node or group of children nodes."])
            return

        if types.pop() == objects.FitDataset:  # we won't check if multiple are selected, just save the first.
            WriteFitDialog.launch(dataset=items[0])
            return

        parent = self._view.support_panel.tree.get_parent_of_selected_data().pop()

        dataset = objects.FitDataset()
        dataset.fits = {model.id: model for model in items}
        dataset.flags = parent.flags

        expressions = set([model.string_expression for model in items])

        if len(expressions) > 1:
            WarningMessageDialog.launch(["Can not save collection of fits with more then one fit expression at "
                                         "the same time."])
            return

        dataset.expression = expressions.pop()

        WriteFitDialog.launch(dataset=dataset)

    @QtCore.pyqtSlot()
    def _on_function_input_changed(self):
        if not self.__update_if_table_changes:
            return
        self.__update_if_table_changes = False

        expression = self._view.get_expression()

        if fit.is_accepted_expression(expression):
            self.__update_states = False
            self._view.highlight_input_red(self._view.input_fit_equation, False)

            variables = fit.parse(expression)
            variables.append(fit.ALPHA)

            self._view.clear_parameters(variables)

            pre_defined_function_name = self._check_if_pre_defined_function()
            for var in variables:
                if pre_defined_function_name is not None and var != fit.ALPHA:
                    self._view.add_parameter(symbol=var, config_value=fit.DEFAULT_VALUES[pre_defined_function_name][var])
                else:
                    self._view.add_parameter(symbol=var)

            self.__update_states = True
            self.update_parameter_table_states()
            self.__update_if_table_changes = True
            self._plot_fit()
        else:
            self.update_parameter_table_states()
            self.__update_if_table_changes = True
            self._view.highlight_input_red(self._view.input_fit_equation, True)

    @QtCore.pyqtSlot()
    def _on_save_user_defined_function_clicked(self):
        function_name = self._view.input_user_equation_name.text()

        if function_name == "":
            self._view.highlight_input_red(self._view.input_user_equation_name, True)
            return
        else:
            self._view.highlight_input_red(self._view.input_user_equation_name, False)

        function = self._view.input_user_equation.text()

        if fit.is_accepted_expression(function):
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

    @QtCore.pyqtSlot()
    def _on_spectrum_settings_changed(self):
        self._update_display()

    @QtCore.pyqtSlot()
    def _on_plot_clicked(self):
        self._plot_fit(force_update=True)

    @QtCore.pyqtSlot()
    def _on_new_clicked(self):
        self.__expression = None
        self.__variable_groups = []
        self._view.clear()

    @QtCore.pyqtSlot()
    def _on_fit_selection_changed(self):
        self.__update_if_table_changes = False

        selected_data = self._view.support_panel.tree.get_selected_data()
        if len(selected_data) == 0:
            self.__update_if_table_changes = True
            return

        for i in range(self._view.run_list.count()):
            item = self._view.run_list.item(i)
            item.setCheckState(qt_constants.Unchecked)

        new_table_state = {}
        self.__expression = None
        self.__variable_groups = {}
        goodness = None

        outputs = dict()
        for data in selected_data:
            if type(data) == objects.Fit:
                # We want to make sure all selected fits have the same expression, otherwise we break out
                if self.__expression and self.__expression != data.expression:
                    self.__expression = None
                    self.__variable_groups = {}
                    self._view.parameter_table.goodness_display.setText('*')
                    return
                else:
                    # We want to keep track of expression and variable groups for updating the display
                    self.__variable_groups[data.run_id] = data.parameters
                    self.__expression = data.expression

                    if goodness:
                        goodness = 'Multiple Selected'
                    else:
                        goodness = data.goodness

                # Check the box next to the run for this fit
                for i in range(self._view.run_list.count()):
                    item = self._view.run_list.item(i)
                    if item.identifier == data.run_id:
                        item.setCheckState(qt_constants.Checked)

                # Update the config table state with this fit. We will pass this up to the view
                new_table_state[data.run_id] = [(parameter.symbol,
                                                 parameter.value,
                                                 parameter.lower,
                                                 parameter.upper,
                                                 parameter.is_fixed,
                                                 parameter.is_global,
                                                 parameter.is_run_specific)
                                                for parameter in data.parameters.values()]

                for par in data.parameters.values():
                    if par.symbol not in outputs.keys():
                        outputs[par.symbol] = set()
                    outputs[par.symbol].add((par.output, par.uncertainty))

                # Fits loaded from a file may not have a run associated with them at the moment. This could happen
                #   because a fit was done and then the runs were removed
                try:
                    self._run_service.get_runs_by_ids([data.run_id])[0]
                except KeyError:
                    data.run_id = 'UNLINKED' + data.run_id if 'UNLINKED' not in data.run_id else data.run_id

            elif type(data) == objects.FitDataset:
                # If the selected data is a set of fits, just add those fits to the list we are iterating over
                for f in data.fits.values():
                    selected_data.append(f)

        # We will need to get parameters to add to table. Clear old table. Same for expression and variable groups
        self.set_parameter_table_states(new_table_state)
        self._view.input_fit_equation.setText(str(self.__expression))
        self._view.set_goodness(goodness)

        # Set the output and uncertainties in the output table
        for symbol, out_sets in outputs.items():
            if len(out_sets) > 1:
                self._view.set_output_uncertainty_for_symbol(symbol, '*', '*')
            else:
                out_set = out_sets.pop()
                self._view.set_output_uncertainty_for_symbol(symbol, out_set[0], out_set[1])

        self._update_display()

        self.__update_if_table_changes = True

    @QtCore.pyqtSlot()
    def _on_insert_character_clicked(self, character):
        self._view.copy_character_to_cursor(character)

    @QtCore.pyqtSlot()
    def _on_parameter_table_changed(self):
        self.update_parameter_table_states()
        self._plot_fit()

    @QtCore.pyqtSlot()
    def _on_run_list_changed(self):
        self.update_parameter_table_states()

    @QtCore.pyqtSlot()
    def _on_run_list_selection_changed(self):
        self._update_parameter_table()

    # def _launch_menu(self, point):
    #     index = self._view.run_list.indexAt(point)
    #
    #     if not index.isValid():
    #         return
    #
    #     menu = QtWidgets.QMenu()
    #     clicked_item = self._view.run_list.itemFromIndex(index)
    #     new_check_state = qt_constants.Checked if clicked_item.checkState() == qt_constants.Unchecked else qt_constants.Unchecked
    #     action_name = "Check selected" if new_check_state == qt_constants.Checked else "Uncheck selected"
    #     menu.addAction(action_name, lambda: self._action_toggle_all_selected(new_check_state))
    #
    #     menu.exec_(self._view.run_list.mapToGlobal(point))
    #
    # def _action_toggle_all_selected(self, new_check_state):
    #     for i in range(self._view.run_list.count()):
    #         if self._view.run_list.item(i).isSelected():
    #             self._view.run_list.item(i).setCheckState(new_check_state)

    @QtCore.pyqtSlot()
    def _on_batch_options_changed(self):
        self._update_batch_options()

    @QtCore.pyqtSlot()
    def _on_config_table_changed(self):
        self.update_parameter_table_states()

    @QtCore.pyqtSlot()
    def _on_fit_clicked(self):
        self.__update_if_table_changes = False
        config = fit.FitConfig()

        # Check user input on fit equation and update config
        expression = self._view.get_expression()
        if not fit.is_accepted_expression(expression):
            WarningMessageDialog.launch(["Fit equation is invalid."])
            self._view.highlight_input_red(self._view.input_fit_equation, True)
            self.__update_if_table_changes = True
            return
        else:
            self._view.highlight_input_red(self._view.input_fit_equation, False)
        config.expression = expression

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

        # Check user input on parameters
        try:
            parameters = self.get_parameters()
        except ValueError:
            WarningMessageDialog.launch(["Parameter input is invalid."])
            self.__update_if_table_changes = True
            return

        for run_id in run_ids:
            for symbol, value, value_min, value_max, _, _, _ in parameters[run_id]:
                if value_min > value_max:
                    WarningMessageDialog.launch([
                        "Lower bound is greater then upper bound for {}. ({:.5f} > {:.5f})".format(
                            symbol, value_min, value_max)])
                    self.__update_if_table_changes = True
                    return
                elif value < value_min:
                    WarningMessageDialog.launch([
                        "Bounds for {} and its initial value are incompatible. ({:.5f} < {:.5f})".format(
                            symbol, value, value_min)])
                    self.__update_if_table_changes = True
                    return
                elif value > value_max:
                    WarningMessageDialog.launch([
                        "Bounds for {} and its initial value are incompatible. ({:.5f} > {:.5f})".format(
                            symbol, value, value_max)])
                    self.__update_if_table_changes = True
                    return

        variables = {}
        fit_titles = {}
        data = OrderedDict()  # Ordered dict is important for fits where we want to fit runs in a certain order.
        for run_id in run_ids:
            for run in self._runs:
                if run.id == run_id:
                    fit_titles[run.id] = run.meta[files.TITLE_KEY]
                    if run.id in self._asymmetries.keys():
                        data[run.id] = (self._asymmetries[run.id].time, self._asymmetries[run.id],
                                        self._asymmetries[run.id].uncertainty, run.meta)
                    else:
                        min_time = self._view.fit_spectrum_settings.get_min_time()
                        max_time = self._view.fit_spectrum_settings.get_max_time()
                        bin_size = self._view.fit_spectrum_settings.get_bin_from_input()
                        raw_asymmetry = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].raw().bin(bin_size).cut(
                            min_time=min_time, max_time=max_time)
                        self._asymmetries[run.id] = raw_asymmetry
                        data[run.id] = (self._asymmetries[run.id].time, self._asymmetries[run.id],
                                        self._asymmetries[run.id].uncertainty, run.meta)

                    run_parameters = {}
                    for symbol, value, value_min, value_max, is_fixed, is_global, is_run_specific in parameters[run.id]:
                        run_parameters[symbol] = fit.FitParameter(symbol=symbol, value=value, lower=value_min,
                                                                  upper=value_max, is_global=is_global,
                                                                  is_fixed=is_fixed, is_run_specific=is_run_specific)
                    variables[run.id] = run_parameters

        config.data = data
        config.batch = self._view.check_batch_fit.isChecked()
        config.parameters = variables
        config.titles = fit_titles
        config.set_flags(0)
        report.log_info(str(config).encode("utf-8"))

        # Fit to spec
        worker = FitWorker(config)
        worker.signals.result.connect(self._update_fit_changes)

        def handle_error(e):
            report.report_exception(e)
            WarningMessageDialog.launch(f"An error occurred during your fit. The message reads \'{str(e)}\'")

        worker.signals.error.connect(lambda error_message: handle_error(error_message))
        self._threadpool.start(worker)

        LoadingDialog.launch("Your fit is running!", worker)

    @QtCore.pyqtSlot()
    def _on_insert_user_defined_function_clicked(self):
        self._view.copy_user_function_to_cursor()

    @QtCore.pyqtSlot()
    def _on_insert_pre_defined_function_clicked(self):
        self._view.copy_loaded_function_to_cursor()

    @QtCore.pyqtSlot()
    def _on_theme_changed(self):
        self._view.fit_display.set_stylesheet()
        if self._view.fit_display.axes_time.lines:
            self._view.fit_display.set_style()
        else:
            self._view.fit_display.set_blank()

    def _update_display(self):
        run_ids = self._view.get_checked_run_ids()

        runs = self._runs
        checked_run_ids = ['default']
        checked_run_ids.extend(self._view.get_checked_run_ids())

        self._view.fit_display.start_plotting()

        max_asymmetry = -1
        min_asymmetry = 1

        try:
            min_time = self._view.fit_spectrum_settings.get_min_time()
            max_time = self._view.fit_spectrum_settings.get_max_time()
            bin_size = self._view.fit_spectrum_settings.get_bin_from_input()
        except ValueError:
            WarningMessageDialog.launch(["Invalid values specified for spectrum limits or bin size."])

        styles = self._style_service.get_styles()
        unavailable_colors = [styles[run.id][self._style_service.Keys.DEFAULT_COLOR] for run in runs]
        available_colors = [c for c in self._style_service.color_options_values.values() if c not in unavailable_colors]
        colors = {run.id: styles[run.id][self._style_service.Keys.DEFAULT_COLOR] for run in runs if
                  run.id in checked_run_ids}
        self._view.support_panel.tree.set_colors(colors)
        colors['default'] = '#888888'

        alphas = dict()

        # Plot the fit lines
        for i, (run_id, parameters) in enumerate(self.__variable_groups.items()):
            if (run_id == 0 or 'UNLINKED' not in run_id) and run_id not in checked_run_ids:
                continue

            parameters = self.__variable_groups[run_id]
            alphas[run_id] = parameters[fit.ALPHA].value
            time = objects.Time(input_array=None, bin_size_ns=(max_time - min_time) * 1000 / 200, length=200,
                                time_zero_bin=min_time)

            try:
                fit_asymmetry = self.__expression(time,
                                                  **{symbol: par.get_value() for symbol, par in parameters.items()})
            except ValueError:
                continue

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
                color = available_colors[-i]
                colors[run_id] = color
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

            raw_asymmetry = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].raw().bin(bin_size).cut(
                min_time=min_time,
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

        self._update_tree_colors(colors)
        self._view.fit_display.set_asymmetry_plot_limits(max_asymmetry, min_asymmetry)
        self._view.fit_display.finish_plotting(False)

    def _update_tree_colors(self, ids_to_colors):
        self._view.support_panel.tree.set_colors(ids_to_colors)

    def _plot_fit(self, force_update=False):
        if not self.__update_if_table_changes:
            return

        expression, parameters = self._get_expression_and_values(get_default=True)

        if expression == self.__expression and self.__variable_groups == parameters and not force_update:
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
            parameters = self.get_parameters()
            expression = self._view.get_expression()
        except ValueError:
            # self._view.highlight_input_red(self._view.parameter_table, True)
            return None, {}
        # self._view.highlight_input_red(self._view.parameter_table, False)

        final_parameters = {}
        run_dependent = False

        greater_than_one = False
        for run in self._runs:
            run_parameters = {}
            for symbol, value, value_min, value_max, is_fixed, is_global, is_run_specific in parameters[run.id]:
                if symbol != fit.ALPHA:
                    greater_than_one = True

                run_parameters[symbol] = fit.FitParameter(symbol=symbol, value=value, lower=value_min, upper=value_max,
                                                          is_fixed=is_fixed, is_global=is_global)
                run_dependent = run_dependent or (is_run_specific and symbol != fit.ALPHA)
            final_parameters[run.id] = run_parameters

        if get_default and not run_dependent:
            run_parameters = {}
            for symbol, value, value_min, value_max, is_fixed, is_global, is_run_specific in parameters['default']:
                if symbol != fit.ALPHA:
                    greater_than_one = True

                run_parameters[symbol] = fit.FitParameter(symbol=symbol, value=value, lower=value_min, upper=value_max,
                                                          is_fixed=is_fixed, is_global=is_global)
            final_parameters['default'] = run_parameters

        if fit.is_accepted_expression(expression) and greater_than_one:
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

    def _update_fit_changes(self, dataset):
        # Check if fit did not converge
        for fit_data in dataset.fits.values():
            if not fit_data.converged:
                WarningMessageDialog.launch(["Fit failed to converge."])
                break

        self._fit_service.add_dataset([dataset])
        self._update_alphas(dataset)
        self.__update_if_table_changes = False
        self._view.select_first_fit_from_dataset(dataset.title)
        self._view.select_top_child_run(dataset.title)
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

    def _update_batch_table(self):
        for j in range(self._view.parameter_table.batch_table.rowCount()):
            item_run_specific = self._view.parameter_table.batch_table.cellWidget(j,
                                                                                  self._view.parameter_table.FIXED_RUN_COLUMN)
            item_global = self._view.parameter_table.batch_table.cellWidget(j, self._view.parameter_table.GLOBAL_COLUMN)

            if item_run_specific is None or item_global is None:
                continue

            is_global = item_global.findChild(QtWidgets.QCheckBox).checkState() == qt_constants.Checked
            is_run_specific = item_run_specific.findChild(QtWidgets.QCheckBox).checkState() == qt_constants.Checked

            item_run_specific.findChild(QtWidgets.QCheckBox).setEnabled(not is_global)
            item_global.findChild(QtWidgets.QCheckBox).setEnabled(not is_run_specific)

            if not is_run_specific:
                row_values = self._view.get_row(j)
                if row_values is None:
                    continue
                for run_id in self.__parameter_table_states[row_values[0]].keys():
                    self.__parameter_table_states[row_values[0]][run_id] = row_values

    def update_parameter_table_states(self):
        """
        This method is called when the content of the config table is changed.
        """

        if not self.__update_states:
            return

        # We are creating a dictionary in this loop to keep track of the table states (if the user wants a run specific
        #   parameter this means we need to keep track of the specified values as he clicks between runs).

        # State dictionary looks like: {symbol : {run_id : (symbol, value, min, max, fixed)}} so you can think of it
        #   like we keep the state of a row in the config table for each run.
        current_symbols = set()
        for j in range(self._view.parameter_table.config_table.rowCount()):  # Iterate over all symbols (rows)
            row_values = self._view.get_row(j)
            if row_values is None:
                continue
            symbol, value, min_value, max_value, is_fixed = row_values
            current_symbols.add(symbol)

            # Get the boolean indicating whether the parameter is run specific
            item_run_specific = self._view.parameter_table.batch_table.cellWidget(j,
                                                                                  self._view.parameter_table.FIXED_RUN_COLUMN)
            if item_run_specific is None:
                continue
            else:
                is_run_specific = item_run_specific.findChild(QtWidgets.QCheckBox).checkState() == qt_constants.Checked

            if is_run_specific:
                # If the parameter is run specific, we want to update the states of the table for every run
                selected_run_ids = self._view.get_selected_run_ids()
                all_run_ids = self._view.get_all_run_ids()

                updated_states = {run_id: (symbol,
                                           value if value != '*' and (
                                                   run_id in selected_run_ids or not_state_exists) else 1.0 if not_state_exists else
                                           self.__parameter_table_states[symbol][run_id][1],
                                           min_value if min_value != '*' and (
                                                   run_id in selected_run_ids or not_state_exists) else 1.0 if not_state_exists else
                                           self.__parameter_table_states[symbol][run_id][2],
                                           max_value if max_value != '*' and (
                                                   run_id in selected_run_ids or not_state_exists) else 1.0 if not_state_exists else
                                           self.__parameter_table_states[symbol][run_id][3],
                                           is_fixed if is_fixed != '*' and (
                                                   run_id in selected_run_ids or not_state_exists) else 1.0 if not_state_exists else
                                           self.__parameter_table_states[symbol][run_id][4])
                                  for run_id, not_state_exists in zip(all_run_ids, [
                        r not in self.__parameter_table_states[symbol].keys() for r in all_run_ids])}

                if symbol not in self.__parameter_table_states.keys():
                    self.__parameter_table_states[symbol] = {}

                self.__parameter_table_states[symbol].update(updated_states)
            else:
                # Otherwise, we will want to set the state of all runs to the current state of the table.
                self.__parameter_table_states[symbol] = {run_id: (symbol, value, min_value, max_value, is_fixed)
                                                         for run_id in self._view.get_all_run_ids()}

        for symbol in current_symbols.symmetric_difference(self.__parameter_table_states.keys()):
            if symbol not in current_symbols:
                self.__parameter_table_states.pop(symbol)

    def _update_parameter_table(self):
        """
        This method is called when the run selection of the user is changed.
        """

        # Don't want to update the states needlessly since we are the ones updating the table (from the state info)
        self.update_parameter_table_states()
        self.__update_states = False

        selected_run_ids = self._view.get_selected_run_ids()
        for j in range(self._view.parameter_table.config_table.rowCount()):  # Iterate over every symbol in table
            symbol = self._view.parameter_table.config_table.verticalHeaderItem(j).text()

            # We use a set simply so we know if we are dealing with 0, 1 or multiple conflicting states.
            collective_states_set = {self.__parameter_table_states[symbol][run_id] for run_id in selected_run_ids}

            if len(collective_states_set) == 0:
                continue  # not sure we can even get here

            elif len(collective_states_set) == 1:
                # If the user has one run selected (or multiple with the same state), then simply populate the table
                #   with the state for that run.
                state = collective_states_set.pop()

                item_value = QtWidgets.QTableWidgetItem()
                item_value.setText(str(state[1]))

                item_min = QtWidgets.QTableWidgetItem()
                item_min.setText(str(state[2]))

                item_max = QtWidgets.QTableWidgetItem()
                item_max.setText(str(state[3]))

                item_fixed = self._view._create_check_box_for_table(state[4], self.update_parameter_table_states)
            else:
                # If the user has multiple runs selected with conflicting states then we will check which parts of the
                #   the state conflict and put '*''s into those cells.
                value_set = set([s[1] for s in collective_states_set])
                min_set = set([s[2] for s in collective_states_set])
                max_set = set([s[3] for s in collective_states_set])
                fixed_set = set([s[4] for s in collective_states_set])

                item_value = QtWidgets.QTableWidgetItem()
                if len(value_set) == 1:
                    item_value.setText(str(value_set.pop()))
                else:
                    item_value.setText('*')

                item_min = QtWidgets.QTableWidgetItem()
                if len(min_set) == 1:
                    item_min.setText(str(min_set.pop()))
                else:
                    item_min.setText('*')

                item_max = QtWidgets.QTableWidgetItem()
                if len(max_set) == 1:
                    item_max.setText(str(max_set.pop()))
                else:
                    item_max.setText('*')

                if len(fixed_set) == 1:
                    item_fixed = self._view._create_check_box_for_table(checked=fixed_set.pop(),
                                                                        connect=self.update_parameter_table_states)
                else:
                    # Puts a partial checkmark in the box since we have both fixed and unfixed selected.
                    item_fixed = self._view._create_check_box_for_table(connect=self.update_parameter_table_states,
                                                                        partial=True)

            self._view.parameter_table.config_table.setItem(j, self._view.parameter_table.VALUE_COLUMN, item_value)
            self._view.parameter_table.config_table.setItem(j, self._view.parameter_table.MIN_COLUMN, item_min)
            self._view.parameter_table.config_table.setItem(j, self._view.parameter_table.MAX_COLUMN, item_max)
            self._view.parameter_table.config_table.setCellWidget(j, self._view.parameter_table.FIXED_COLUMN,
                                                                  item_fixed)

        self.__update_states = True

    def set_parameter_table_states(self, states):
        self.__update_states = False
        self._view.clear_parameters()

        self.__parameter_table_states = {}
        is_globals = {}
        is_run_specifics = {}

        for run_id, parameters in states.items():
            for symbol, value, minimum, maximum, is_fixed, is_global, is_run_specific in parameters:
                if symbol not in self.__parameter_table_states.keys():
                    self.__parameter_table_states[symbol] = {}

                try:
                    value = float(value)
                except ValueError:
                    value = 1.0

                try:
                    minimum = float(minimum)
                except ValueError:
                    minimum = 1.0

                try:
                    maximum = float(maximum)
                except ValueError:
                    maximum = 1.0

                is_globals[symbol] = is_global
                is_run_specifics[symbol] = is_run_specific

                self.__parameter_table_states[symbol][run_id] = (symbol, value, minimum, maximum, is_fixed)

        for symbol, run_parameters in self.__parameter_table_states.items():
            collective_states_set = {self.__parameter_table_states[symbol][run_id] for run_id in states.keys()}

            if len(collective_states_set) == 0:
                continue
            elif len(collective_states_set) == 1:
                _, value, minimum, maximum, is_fixed = collective_states_set.pop()
            else:
                value_set = set([s[1] for s in collective_states_set])
                min_set = set([s[2] for s in collective_states_set])
                max_set = set([s[3] for s in collective_states_set])
                fixed_set = set([s[4] for s in collective_states_set])

                value = '*' if len(value_set) > 1 else value_set.pop()
                minimum = '*' if len(min_set) > 1 else min_set.pop()
                maximum = '*' if len(max_set) > 1 else max_set.pop()
                is_fixed = '*' if len(fixed_set) > 1 else fixed_set.pop()

            self._view.add_parameter(symbol, value, minimum, maximum, is_fixed, is_globals[symbol],
                                     is_run_specifics[symbol])

        self.__update_states = True

        self.update_parameter_table_states()

    def _update_batch_options(self):
        self._view.label_ordering.setEnabled(
            self._view.check_batch_fit.isChecked() or self._view.check_global_plus.isChecked())
        self._view.option_run_ordering.setEnabled(
            self._view.check_batch_fit.isChecked() or self._view.check_global_plus.isChecked())
        self._view.option_ascending.setEnabled(
            self._view.check_batch_fit.isChecked() or self._view.check_global_plus.isChecked())

    def get_parameters(self):
        default = []
        is_globals = {}
        is_run_specific = {}
        for i in range(self._view.parameter_table.config_table.rowCount()):
            item_symbol = self._view.parameter_table.config_table.verticalHeaderItem(i)
            item_value = self._view.parameter_table.config_table.item(i, self._view.parameter_table.VALUE_COLUMN)
            item_min = self._view.parameter_table.config_table.item(i, self._view.parameter_table.MIN_COLUMN)
            item_max = self._view.parameter_table.config_table.item(i, self._view.parameter_table.MAX_COLUMN)
            item_fixed = self._view.parameter_table.config_table.cellWidget(i, self._view.parameter_table.FIXED_COLUMN)
            item_global = self._view.parameter_table.batch_table.cellWidget(i, self._view.parameter_table.GLOBAL_COLUMN)

            if item_symbol is None:
                continue

            symbol = item_symbol.text()
            value = 1 if item_value is None or item_value.text() == '' else float(item_value.text())
            value_min = -np.inf if item_min is None or item_min.text() == '' else float(item_min.text())
            value_max = np.inf if item_max is None or item_max.text() == '' else float(item_max.text())
            is_fixed = item_fixed is not None and item_fixed.findChild(QtWidgets.QCheckBox).checkState() > 0
            is_global = item_global is not None and item_global.findChild(QtWidgets.QCheckBox).checkState() > 0

            default.append((symbol, value, value_min, value_max, is_fixed, is_global, False))

            item_run_specific = self._view.parameter_table.batch_table.cellWidget(i,
                                                                                  self._view.parameter_table.FIXED_RUN_COLUMN)

            if item_symbol is None:
                continue

            is_globals[symbol] = item_global is not None and item_global.findChild(QtWidgets.QCheckBox).checkState() > 0
            is_run_specific[symbol] = item_run_specific is not None and item_run_specific.findChild(
                QtWidgets.QCheckBox).checkState() > 0

        run_ids = self._view.get_all_run_ids()
        final_parameters = {run_id: [] for run_id in run_ids}

        for symbol, states in self.__parameter_table_states.items():
            for run_id in run_ids:
                final_parameters[run_id].append(
                    self.__parameter_table_states[symbol][run_id] + (is_globals[symbol], is_run_specific[symbol],))

        final_parameters['default'] = default
        return final_parameters

    def _check_if_pre_defined_function(self):
        for name, function in fit.EQUATION_DICTIONARY.items():
            if function == self._view.get_expression():
                return name
        return None

    def update(self):
        runs = []
        for run in self._run_service.get_loaded_runs():
            if run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] is not None:
                runs.append(run)
        self._runs = runs

        self.__update_states = False
        self._view.update_run_table(runs)
        self.__update_states = True
        self.update_parameter_table_states()


class FitWorker(QtCore.QRunnable):
    def __init__(self, config: fit.FitConfig):
        super(FitWorker, self).__init__()
        self.config = config
        self.signals = FitSignals()
        self.__logger = logging.getLogger(__name__)
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
            report.report_exception(e)
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
