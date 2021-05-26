import warnings

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np

from app.gui.plottingpanel import PlotModel
from app.gui.dialogs.dialog_misc import WarningMessageDialog
from app.util import widgets
from app.model import domain, fit, files
from app.gui.gui import PanelPresenter, Panel


# noinspection PyArgumentList
class FittingPanel(Panel):
    __NAME_COLUMN = 0
    __VALUE_COLUMN = 1
    __LOWER_COLUMN = 2
    __UPPER_COLUMN = 3
    __FIXED_COLUMN = 4
    __GLOBAL_COLUMN = 5

    class SupportPanel(QtWidgets.QDockWidget):
        class Tree(QtWidgets.QTreeWidget):
            def __init__(self):
                super().__init__()
                self.__manager = FittingPanel.SupportPanel.TreeManager(self)
                self.setHeaderHidden(True)
                self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
                self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
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

            def get_run_ids(self):
                # Suppressing inspection because it doesn't recognize 'self' as a QTreeWidget
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Checked)

                ids = []
                while iterator.value():
                    if isinstance(iterator.value().model, fit.FitDataset):
                        ids.append(iterator.value().model.id)

                    iterator += 1

                return ids

            def get_selected_data(self):
                # noinspection PyTypeChecker
                iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Selected)

                while iterator.value():
                    if isinstance(iterator.value().model, fit.Fit) or isinstance(iterator.value().model, fit.FitDataset):
                        return iterator.value().model
                    iterator += 1

        class TreeManager:
            def __init__(self, view):
                self.__view = view
                self.__run_service = domain.RunService()
                self.__fit_service = domain.FitService()
                self.__fit_service.register(domain.FitService.FITS_ADDED, self)
                self.__file_service = domain.FileService()
                self.__run_service.register(domain.RunService.RUNS_ADDED, self)

            def _create_tree_model(self, fit_datasets):
                fit_dataset_nodes = []
                for dataset in fit_datasets:
                    fit_dataset_nodes.append(FittingPanel.SupportPanel.FitDatasetNode(dataset))
                return fit_dataset_nodes

            def update(self):
                fit_datasets = self.__fit_service.get_fit_datasets()
                tree = self._create_tree_model(fit_datasets)
                self.__view.set_tree(tree)

        class FitDatasetNode(QtWidgets.QTreeWidgetItem):
            def __init__(self, dataset):
                super().__init__([dataset.id])
                self.model = dataset
                self.__selected_items = None

                if isinstance(dataset, fit.FitDataset):
                    for fit_data in dataset.fits.values():
                        self.addChild(FittingPanel.SupportPanel.FitNode(fit_data))

            def menu(self, items):
                self.__selected_items = items
                menu = QtWidgets.QMenu()
                menu.addAction("Rename", self._action_rename)
                menu.addAction("Save", self._action_save)
                menu.addSeparator()
                menu.addAction("Expand", self._action_expand)
                return menu

            def _action_rename(self):
                pass

            def _action_save(self):
                pass

            def _action_expand(self):
                pass

        class FitNode(QtWidgets.QTreeWidgetItem):
            def __init__(self, fit_data):
                super().__init__([fit_data.title])
                self.model = fit_data
                self.__selected_items = None

            def menu(self, items):
                self.__selected_items = items
                menu = QtWidgets.QMenu()
                menu.addAction("Rename", self._action_rename)
                menu.addAction("Save", self._action_save)
                return menu

            def _action_rename(self):
                pass

            def _action_save(self):
                pass

        def __init__(self):
            super().__init__()
            self.tree = FittingPanel.SupportPanel.Tree()
            self.setTitleBarWidget(QtWidgets.QWidget())
            # self.setFixedWidth(350)
            self.setMinimumHeight(500)
            layout = QtWidgets.QVBoxLayout()

            self.new_button = widgets.StyleTwoButton("New Empty Fit")
            self.reset_button = widgets.StyleOneButton("Reset")
            self.save_button = widgets.StyleTwoButton("Save")

            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(self.new_button)
            # hbox.addWidget(self.reset_button)
            hbox.addWidget(self.save_button)
            layout.addLayout(hbox)

            layout.addWidget(self.tree)
            temp = QtWidgets.QWidget()
            temp.setLayout(layout)
            self.setWidget(temp)

    class FitCanvas(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.canvas_axes = self.figure.add_subplot()

    class FitToolbar(NavigationToolbar2QT):
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

            if uncertainty is not None and errorbar_style != 'none':
                self.axes_time.errorbar(time, asymmetry, uncertainty, mfc=marker_face_color, mec=marker_color,
                                        color=color, linestyle=linestyle, marker=marker, fillstyle=fillstyle,
                                        linewidth=line_width, markersize=marker_size,
                                        elinewidth=errorbar_width,
                                        ecolor=errorbar_color, capsize=errorbar_style)

            else:
                self.axes_time.plot(time, asymmetry, mfc=marker_face_color, mec=marker_color, color=color,
                                    linestyle=linestyle, marker=marker, fillstyle=fillstyle,
                                    linewidth=line_width,
                                    markersize=marker_size, label=label)

            if fit is not None:
                self.axes_time.plot(time, fit, color=fit_color, linestyle=fit_linestyle,
                                    marker='None')

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

            self.slider_bin = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.input_bin = QtWidgets.QLineEdit()

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

            self._label_freq = QtWidgets.QLabel('Frequency')
            self._label_freq_xmin = QtWidgets.QLabel('XMin')
            self._label_freq_xmax = QtWidgets.QLabel('XMax')
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
            self.input_bin.returnPressed.connect(lambda: self._update_bin(False))
            self.slider_bin.sliderMoved.connect(lambda: self._update_bin(True))

        def _set_widget_tooltips(self):
            pass

        def _set_widget_dimensions(self):
            box_size = 80
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
            # editor_layout.addWidget(freq_form)

            # main_layout.addLayout(editor_layout)
            # main_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
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

        def get_max_freq(self):
            return float(self.input_freq_xmax.text())

        def get_min_freq(self):
            return float(self.input_freq_xmin.text())

        def get_max_asymmetry(self):
            return float(self.input_time_ymax.text())

        def get_min_asymmetry(self):
            return float(self.input_time_ymin.text())

        def get_max_fft(self):
            return float(self.input_freq_ymax.text())

        def get_min_fft(self):
            return float(self.input_freq_ymin.text())

        def get_bin_from_input(self):
            return float(self.input_bin.text())

        def get_bin_from_slider(self):
            return float(self.slider_bin.value())

        def is_asymmetry_auto(self):
            return self.check_time_yauto.isChecked()

        def is_fft_auto(self):
            return self.check_freq_yauto.isChecked()

        def is_freq_auto(self):
            return self.check_freq_xauto.isChecked()

        def set_enabled_asymmetry_auto(self, enabled):
            self.input_time_ymin.setEnabled(enabled)
            self.input_time_ymax.setEnabled(enabled)

        def set_enabled_frequency_auto(self, enabled):
            self.input_freq_xmin.setEnabled(enabled)
            self.input_freq_xmax.setEnabled(enabled)

        def set_enabled_fft_auto(self, enabled):
            self.input_freq_ymin.setEnabled(enabled)
            self.input_freq_ymax.setEnabled(enabled)

        def set_max_time(self, value):
            self.input_time_xmax.setText('{0:.3f}'.format(value))

        def set_min_time(self, value):
            self.input_time_xmin.setText('{0:.3f}'.format(value))

        def set_max_freq(self, value):
            self.input_freq_xmax.setText('{0:.3f}'.format(value))

        def set_min_freq(self, value):
            self.input_freq_xmin.setText('{0:.3f}'.format(value))

        def set_max_asymmetry(self, value):
            self.input_time_ymax.setText('{0:.3f}'.format(value))

        def set_min_asymmetry(self, value):
            self.input_time_ymin.setText('{0:.3f}'.format(value))

        def set_max_fft(self, value):
            self.input_freq_ymax.setText('{0:.1f}'.format(value))

        def set_min_fft(self, value):
            self.input_freq_ymin.setText('{0:.1f}'.format(value))

        def set_bin_input(self, value):
            self.input_bin.setText(str(value))

        def set_bin_slider(self, value):
            self.slider_bin.setValue(int(value))

    def __init__(self):
        super(FittingPanel, self).__init__()
        self.support_panel = FittingPanel.SupportPanel()

        self.input_fit_equation = QtWidgets.QLineEdit()
        self.input_user_equation = QtWidgets.QLineEdit()
        self.input_user_equation_name = QtWidgets.QLineEdit()
        self.input_spectrum_min = QtWidgets.QLineEdit()
        self.input_spectrum_max = QtWidgets.QLineEdit()
        self.input_packing = QtWidgets.QLineEdit()
        self.input_file_name = QtWidgets.QLineEdit()
        self.input_folder_name = QtWidgets.QLineEdit()

        self.option_preset_fit_equations = QtWidgets.QComboBox()
        self.option_user_fit_equations = QtWidgets.QComboBox()
        self.option_run_ordering = QtWidgets.QComboBox()

        self.fit_spectrum_settings = FittingPanel.PlotControl()
        self.fit_display = FittingPanel.PlotDisplay(self.fit_spectrum_settings)
        self.special_characters = widgets.CollapsibleBox("Special Characters", background='#FFFFFF')
        self.special_characters.toggle_button.released.connect(self.special_characters.on_pressed)

        self.table_parameters = QtWidgets.QTableWidget()
        self.user_functions = QtWidgets.QTableWidget()
        self.run_list = QtWidgets.QListWidget()

        self.button_check_equation = widgets.StyleOneButton("Check")
        self.button_fit = widgets.StyleOneButton("Fit")
        self.button_done = widgets.StyleOneButton("Done")
        self.button_insert_preset_equation = widgets.StyleTwoButton("Insert")
        self.button_insert_user_equation = widgets.StyleTwoButton("Insert")
        self.button_save_user_equation = widgets.StyleTwoButton("Save")
        self.button_save_results = widgets.StyleTwoButton("Save Fit")
        self.button_lookup_folder = widgets.StyleTwoButton("Folder")
        self.button_plot = widgets.StyleTwoButton("Plot")

        self.label_global_plus = QtWidgets.QLabel("Global+")
        self.label_ordering = QtWidgets.QLabel("Order by")
        self.label_use_previous = QtWidgets.QLabel("Use Previous Run")
        self.label_fit_alpha = QtWidgets.QLabel("Fit Alpha")

        self.check_batch_fit = QtWidgets.QCheckBox()
        self.check_global_plus = QtWidgets.QCheckBox()
        self.check_use_previous = QtWidgets.QCheckBox()
        self.check_fit_alpha = QtWidgets.QCheckBox()

        self.insert_phi = widgets.StyleTwoButton(fit.PHI)
        self.insert_alpha = widgets.StyleTwoButton(fit.ALPHA)
        self.insert_sigma = widgets.StyleTwoButton(fit.SIGMA)
        self.insert_naught = widgets.StyleTwoButton(fit.NAUGHT)
        self.insert_lambda = widgets.StyleTwoButton(fit.LAMBDA)
        self.insert_delta = widgets.StyleTwoButton(fit.DELTA)
        self.insert_beta = widgets.StyleTwoButton(fit.BETA)
        self.insert_pi = widgets.StyleOneButton(fit.PI)

        self.group_preset_functions = QtWidgets.QGroupBox("Loaded Functions")
        self.group_user_functions = QtWidgets.QGroupBox("User Functions")
        self.group_special_characters = QtWidgets.QGroupBox("")
        self.group_batch_options = QtWidgets.QGroupBox("Options")
        self.group_spectrum_options = QtWidgets.QGroupBox("Spectrum")
        self.group_save_results = QtWidgets.QGroupBox("Save")
        self.group_table_parameters = QtWidgets.QGroupBox("Parameters")
        self.group_table_runs = QtWidgets.QGroupBox("Runs")
        self.group_function = QtWidgets.QGroupBox("Function")

        self._set_widget_layout()
        self._set_widget_attributes()
        self._set_widget_dimensions()

        self._presenter = FitTabPresenter(self)
        self._line_edit_style = self.input_fit_equation.styleSheet()

    def _set_widget_attributes(self):
        # self.table_parameters.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.table_parameters.setColumnCount(6)
        self.table_parameters.setHorizontalHeaderLabels(['Name', 'Value', '<', '>', 'Fixed', 'Global'])
        self.table_parameters.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.table_parameters.horizontalHeader().setSectionResizeMode(self.__NAME_COLUMN, QtWidgets.QHeaderView.Stretch)
        self.table_parameters.horizontalHeader().setSectionResizeMode(self.__VALUE_COLUMN, QtWidgets.QHeaderView.Stretch)
        self.table_parameters.horizontalHeader().setSectionResizeMode(self.__LOWER_COLUMN, QtWidgets.QHeaderView.Stretch)
        self.table_parameters.horizontalHeader().setSectionResizeMode(self.__UPPER_COLUMN, QtWidgets.QHeaderView.Stretch)

        self.option_preset_fit_equations.addItems(list(fit.EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItems(list(fit.USER_EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItem("None")
        self.option_run_ordering.addItems(['Field', 'Temp', 'Run'])

        self.input_user_equation_name.setPlaceholderText("Function Name")
        self.input_user_equation.setPlaceholderText("Function (e.g. \"\u03B2 * (t + \u03BB)\")")
        self.input_fit_equation.setPlaceholderText("Fit Equation")

        self.check_fit_alpha.setCheckState(QtCore.Qt.Checked)
        self.check_use_previous.setEnabled(False)
        self.check_global_plus.setEnabled(True)
        self.option_run_ordering.setEnabled(False)
        self.label_global_plus.setEnabled(True)
        self.label_ordering.setEnabled(False)
        self.label_use_previous.setEnabled(False)
        self.check_batch_fit.setEnabled(False)

    def _set_widget_dimensions(self):
        self.button_done.setFixedWidth(60)
        self.button_fit.setFixedWidth(60)
        self.button_check_equation.setFixedWidth(60)
        self.button_insert_user_equation.setFixedWidth(60)
        self.button_insert_preset_equation.setFixedWidth(60)
        self.button_lookup_folder.setFixedWidth(60)
        self.button_save_user_equation.setFixedWidth(60)
        self.button_plot.setFixedWidth(60)

        self.option_run_ordering.setFixedWidth(80)
        self.option_user_fit_equations.setFixedWidth(120)
        self.option_preset_fit_equations.setFixedWidth(120)

        self.input_user_equation_name.setFixedWidth(100)
        self.input_user_equation.setMinimumWidth(160)
        self.input_packing.setFixedWidth(60)
        self.input_spectrum_min.setFixedWidth(60)
        self.input_spectrum_max.setFixedWidth(60)

        self.fit_display.setMinimumWidth(800)
        self.fit_spectrum_settings.setMinimumWidth(720)

        self.group_table_parameters.setFixedWidth(320)
        self.group_table_runs.setFixedWidth(320)
        self.group_spectrum_options.setFixedWidth(120)
        self.group_batch_options.setFixedWidth(320)
        # self.group_batch_options.setMaximumHeight(110)
        self.group_save_results.setMaximumHeight(110)
        # self.group_save_results.setMinimumWidth(720)
        self.group_spectrum_options.setMaximumHeight(110)

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

        full_row = QtWidgets.QHBoxLayout()
        grid = QtWidgets.QGridLayout()

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.option_preset_fit_equations)
        row.addWidget(self.button_insert_preset_equation)
        layout = QtWidgets.QFormLayout()
        layout.addRow(row)
        self.group_preset_functions.setLayout(layout)
        grid.addWidget(self.group_preset_functions, 0, 0, 1, 2)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.option_user_fit_equations)
        row.addWidget(self.button_insert_user_equation)
        row.addSpacing(20)
        row.addWidget(self.input_user_equation_name)
        row.addWidget(self.input_user_equation)
        row.addWidget(self.button_save_user_equation)
        layout = QtWidgets.QFormLayout()
        layout.addRow(row)
        self.group_user_functions.setLayout(layout)
        grid.addWidget(self.group_user_functions, 0, 2, 1, 5)

        # full_row.addWidget(self.group_preset_functions)
        # full_row.addSpacing(20)
        # full_row.addWidget(self.group_user_functions)
        # full_row.addStretch()
        main_layout.addLayout(grid)

        row = QtWidgets.QHBoxLayout()
        row.addSpacing(20)
        row.addWidget(QtWidgets.QLabel("A(t) = "))
        row.addSpacing(5)
        row.addWidget(self.input_fit_equation)
        # row.addWidget(self.button_check_equation)
        row.addSpacing(20)
        row.addWidget(self.insert_pi)
        row.addWidget(self.insert_alpha)
        row.addWidget(self.insert_beta)
        row.addWidget(self.insert_delta)
        row.addWidget(self.insert_lambda)
        row.addWidget(self.insert_phi)
        row.addWidget(self.insert_sigma)
        row.addWidget(self.insert_naught)
        self.group_function.setLayout(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.group_function)
        main_layout.addLayout(row)

        layout = QtWidgets.QFormLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_batch_fit)
        x = QtWidgets.QLabel("Batch Fit")
        x.setEnabled(False)
        row.addWidget(x)
        row.addStretch()
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.label_ordering)
        row2.addSpacing(2)
        row2.addWidget(self.option_run_ordering)
        row2.addStretch()
        row.addLayout(row2)
        layout.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_global_plus)
        row.addWidget(self.label_global_plus)
        row.addStretch()
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.check_use_previous)
        row2.addWidget(self.label_use_previous)
        row2.addStretch()
        row.addLayout(row2)
        layout.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_fit_alpha)
        row.addWidget(self.label_fit_alpha)
        row.addStretch()
        layout.addRow(row)
        self.group_batch_options.setLayout(layout)

        left_side = QtWidgets.QVBoxLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.table_parameters)
        self.group_table_parameters.setLayout(row)
        left_side.addWidget(self.group_table_parameters)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.run_list)
        self.group_table_runs.setLayout(row)
        left_side.addWidget(self.group_table_runs)
        left_side.addWidget(self.group_batch_options)

        layout = QtWidgets.QFormLayout()
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("File Name: "), 0, 0, 1, 1)
        grid.addWidget(self.input_file_name, 0, 1, 1, 7)
        grid.addWidget(QtWidgets.QLabel("Save to: "), 1, 0, 1, 1)
        grid.addWidget(self.input_folder_name, 1, 1, 1, 6)
        grid.addWidget(self.button_lookup_folder, 1, 7, 1, 1)
        grid.addWidget(self.button_save_results, 2, 6, 1, 2)
        row = QtWidgets.QHBoxLayout()
        row.addLayout(grid)
        layout.addRow(row)
        self.group_save_results.setLayout(layout)
        row_save = QtWidgets.QHBoxLayout()
        row_save.addWidget(self.group_save_results)
        column = QtWidgets.QVBoxLayout()
        column.addWidget(self.button_fit)
        column.addSpacing(4)
        column.addWidget(self.button_done)
        row_save.addLayout(column)

        right_side = QtWidgets.QVBoxLayout()
        right_side.addWidget(self.fit_display)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.button_plot)
        hbox.addWidget(self.fit_spectrum_settings)
        right_side.addLayout(hbox)
        right_side.addLayout(row_save)
        # right_side.addWidget(self.fit_spectrum_settings)

        row = QtWidgets.QHBoxLayout()
        row.addLayout(left_side)
        row.addStretch()
        row.addLayout(right_side)
        row.addStretch()
        main_layout.addLayout(row)

        full_row = QtWidgets.QHBoxLayout()
        # full_row.addWidget(self.group_batch_options)

        layout = QtWidgets.QFormLayout()
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("X-Min"), 0, 0)
        grid.addWidget(self.input_spectrum_min, 0, 1)
        grid.addWidget(QtWidgets.QLabel("X-Max"), 1, 0)
        grid.addWidget(self.input_spectrum_max, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Packing"), 2, 0)
        grid.addWidget(self.input_packing, 2, 1)
        row = QtWidgets.QHBoxLayout()
        row.addLayout(grid)
        layout.addRow(row)
        self.group_spectrum_options.setLayout(layout)

        # full_row.addWidget(self.group_spectrum_options)



        # full_row.addWidget(self.group_save_results)

        # full_row.addSpacing(8)
        # column = QtWidgets.QVBoxLayout()
        # column.addWidget(self.button_fit)
        # column.addSpacing(4)
        # column.addWidget(self.button_done)
        # full_row.addLayout(column)
        # full_row.addSpacing(8)
        #
        # main_layout.addLayout(full_row)

        self.setLayout(main_layout)

    def createSupportPanel(self) -> QtWidgets.QDockWidget:
        return self.support_panel

    def _create_check_box_for_table(self, checked=None):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        check = QtWidgets.QCheckBox()
        check.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        layout.addWidget(check)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        return widget

    def get_selected_run_titles(self):
        titles = []
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.checkState():
                titles.append(item.text())
        return titles

    def get_initial_values(self):
        values = {}
        for i in range(self.table_parameters.rowCount()):
            variable_guess = self.table_parameters.item(i, self.__VALUE_COLUMN)

            if variable_guess is None or variable_guess.text() == '':
                return None

            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            try:
                variable_guess = float(variable_guess.text())
            except ValueError:
                return None

            values[variable_name] = variable_guess

        return values

    def get_names(self):
        values = {}
        for i in range(self.table_parameters.rowCount()):
            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            variable_guess = self.table_parameters.item(i, self.__NAME_COLUMN)

            if variable_guess is None:
                values[variable_name] = variable_name
                continue

            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            variable_guess = variable_guess.text()

            variable_guess = variable_name if variable_guess == '' else variable_guess

            values[variable_name] = variable_guess

        return values

    def get_fixed(self):
        values = {}
        for i in range(self.table_parameters.rowCount()):
            variable_guess = self.table_parameters.cellWidget(i, self.__FIXED_COLUMN)
            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            values[variable_name] = variable_guess.findChild(QtWidgets.QCheckBox).checkState() > 0

        return values

    def get_expression(self):
        return self.input_fit_equation.text()

    def get_lower_bounds(self):
        values = {}
        for i in range(self.table_parameters.rowCount()):
            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            variable_guess = self.table_parameters.item(i, self.__LOWER_COLUMN)

            if variable_guess is None:
                values[variable_name] = -np.inf
                continue

            variable_guess = variable_guess.text()

            try:
                variable_guess = -np.inf if variable_guess == '' else float(variable_guess)
            except ValueError:
                return None

            values[variable_name] = variable_guess

        return values

    def get_upper_bounds(self):
        values = {}
        for i in range(self.table_parameters.rowCount()):
            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            variable_guess = self.table_parameters.item(i, self.__UPPER_COLUMN)

            if variable_guess is None:
                values[variable_name] = np.inf
                continue

            variable_guess = variable_guess.text()

            try:
                variable_guess = np.inf if variable_guess == '' else float(variable_guess)
            except ValueError:
                return None

            values[variable_name] = variable_guess

        return values

    def get_check_global(self):
        values = {}
        for i in range(self.table_parameters.rowCount()):
            variable_guess = self.table_parameters.cellWidget(i, self.__GLOBAL_COLUMN)
            variable_name = self.table_parameters.verticalHeaderItem(i).text()
            values[variable_name] = variable_guess.findChild(QtWidgets.QCheckBox).checkState() > 0

        return values

    def highlight_input_red(self, box, red):
        if red:
            box.setStyleSheet("border: 1px solid red;")
        else:
            box.setStyleSheet(self._line_edit_style)

    def update_variable_table(self, variables):
        n = self.table_parameters.verticalHeader().count()

        for i in range(self.table_parameters.verticalHeader().count() - 1, -1, -1):
            item = self.table_parameters.verticalHeaderItem(i)

            if item is None:
                continue

            old_var = item.text()

            var_exists = False

            if old_var in variables:
                variables.remove(old_var)
                continue

            for new_var in variables:
                if old_var in new_var:
                    var_exists = True
                    replace_item = QtWidgets.QTableWidgetItem()
                    replace_item.setText(new_var)
                    self.table_parameters.setVerticalHeaderItem(i, replace_item)
                    old_var = new_var

            if not var_exists:
                self.table_parameters.removeRow(i)
                n -= 1
            else:
                variables.remove(old_var)

        self.table_parameters.setRowCount(len(variables) + self.table_parameters.verticalHeader().count())

        for new_var in variables:
            new_item = QtWidgets.QTableWidgetItem()
            new_item.setText(new_var)
            self.table_parameters.setVerticalHeaderItem(n, new_item)
            self.table_parameters.setCellWidget(n, self.__GLOBAL_COLUMN, self._create_check_box_for_table())
            self.table_parameters.setCellWidget(n, self.__FIXED_COLUMN, self._create_check_box_for_table())
            n += 1

    def update_run_table(self, runs):
        self.run_list.clear()

        for run in runs:
            file_item = QtWidgets.QListWidgetItem(run.meta[files.TITLE_KEY], self.run_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

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
            if self.support_panel.tree.topLevelItem(i).text(0) == dataset_id:
                index = i
        run_title = self.support_panel.tree.topLevelItem(index).child(0).text(0)
        for i in range(self.run_list.count()):
            item = self.run_list.item(i)
            if item.text() == run_title:
                item.setCheckState(QtCore.Qt.Checked)
            else:
                item.setCheckState(QtCore.Qt.Unchecked)

    def set_variable_value(self, variable, value=None, name=None, is_fixed=None, lower=None, upper=None, is_global=None):
        for i in range(self.table_parameters.rowCount()):
            if self.table_parameters.verticalHeaderItem(i).text() == variable:

                if value:
                    item = QtWidgets.QTableWidgetItem()
                    item.setText(str(value))
                    self.table_parameters.setItem(i, self.__VALUE_COLUMN, item)

                if name:
                    item = QtWidgets.QTableWidgetItem()
                    item.setText(str(name))
                    self.table_parameters.setItem(i, self.__NAME_COLUMN, item)

                if is_fixed:
                    self.table_parameters.setCellWidget(i, self.__FIXED_COLUMN, self._create_check_box_for_table(is_fixed))

                if lower:
                    item = QtWidgets.QTableWidgetItem()
                    item.setText(str(lower))
                    self.table_parameters.setItem(i, self.__LOWER_COLUMN, item)

                if upper:
                    item = QtWidgets.QTableWidgetItem()
                    item.setText(str(upper))
                    self.table_parameters.setItem(i, self.__UPPER_COLUMN, item)

                if is_global:
                    self.table_parameters.setCellWidget(i, self.__GLOBAL_COLUMN, self._create_check_box_for_table(is_global))

    def clear(self):
        self.input_fit_equation.clear()
        for i in range(self.table_parameters.rowCount()):
            self.table_parameters.removeRow(0)
        for i in range(self.run_list.count()):
            self.run_list.item(i).setCheckState(QtCore.Qt.Unchecked)
        self.table_parameters.setEnabled(True)
        self.run_list.setEnabled(True)
        self.fit_display.set_full_blank()

    @staticmethod
    def launch(args):
        dialog = FittingPanel(args)
        return dialog.exec()


# fixme when the user clicks fit the generated fit is added to the side panel
#  this happens each time the user clicks fit because we have to save a relatively
#  small amount of data which the user can then go back and for through.
#  Also, have fit datasets be the top level node and fits be sub nodes. This will
#  allow an easy way to save specific fits.

# fixme error when the asymmetry is not plotted before fitting, we need to make a
#  custom widget to send out that signal that a plot is selected and automatically populate the display. Ugh.

# fixme put everything in group boxes on this page, it might look better

# fixme, make sure display is updating only when necessary. Cause it definitely ain't right now.

# fixme, need to redo populating, in conjunction with above.

# fixme, all asymmetry displays should show corrected, but raw asymmetries need to be passed in to fits. Should we
#  show the raw asymmetry though in the fit panel? Or should we show in corrected to whatever alpha parameter is in
#  the table?

# fixme, need to create some kind of loading popup or something when it is fitting.


class FitTabPresenter(PanelPresenter):
    def __init__(self, view: FittingPanel):
        super().__init__(view)
        self._run_service = domain.RunService()
        self._fit_service = domain.FitService()
        self._set_callbacks()

        self._run_service.register(self._run_service.RUNS_ADDED, self)
        self._run_service.register(self._run_service.RUNS_LOADED, self)
        self._fit_service.register(self._fit_service.FITS_ADDED, self)

        self._runs = []
        self._asymmetries = {}
        self._plot_model = PlotModel()

        self.__update_if_table_changes = True
        self.__variable_groups = []
        self.__expression = None
        self._check_fit_alpha()

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
        self._view.table_parameters.itemChanged.connect(self._plot_fit)
        self._view.button_fit.released.connect(self._fit)
        self._view.button_save_results.released.connect(self._save_fit_results)
        self._view.support_panel.new_button.released.connect(self._new_empty_fit)
        self._view.check_fit_alpha.stateChanged.connect(self._check_fit_alpha)

    def _save_fit_results(self):
        selected_data = self._view.support_panel.tree.get_selected_data()
        if selected_data is None:
            return

        if isinstance(selected_data, fit.FitDataset):
            selected_data.write("out_file_x.txt", fit.FitOptions.SAVE_2)
        else:
            selected_data.write("out_file_x.txt")

    def _function_input_changed(self):
        if not self.__update_if_table_changes:
            return

        expression = "A(t) = " + self._view.get_expression()

        if fit.is_valid_expression(expression):
            self._view.highlight_input_red(self._view.input_fit_equation, False)
            variables = fit.parse(fit.split_expression(expression)[1])
            variables.discard(fit.INDEPENDENT_VARIABLE)

            if self._view.check_fit_alpha.isChecked():
                variables.add(fit.ALPHA)

            self._view.update_variable_table(variables=variables)
            self._view.set_variable_value(fit.ALPHA, name='Alpha', is_global=True)
        else:
            self._view.highlight_input_red(self._view.input_fit_equation, True)

    def _check_fit_alpha(self):
        expression = self._view.get_expression()
        if self._view.check_fit_alpha.isChecked():
            variables = fit.parse(expression)
            variables.discard(fit.INDEPENDENT_VARIABLE)
            variables.add(fit.ALPHA)
            self._view.update_variable_table(variables=variables)
            self._view.set_variable_value(fit.ALPHA, name='Alpha', value=1, is_global=True)
        else:
            variables = fit.parse(expression)
            variables.discard(fit.INDEPENDENT_VARIABLE)
            self._view.update_variable_table(variables=variables)

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
            fit.USER_EQUATION_DICTIONARY[function_name] = self._view.input_user_equation.text()

        self._view.option_user_fit_equations.setCurrentText(function_name)
        self._view.input_user_equation_name.clear()
        self._view.input_user_equation.clear()

    def _update_display(self):
        titles = self._view.get_selected_run_titles()

        runs = self._runs

        self._view.fit_display.start_plotting()

        max_asymmetry = -1
        min_asymmetry = 1
        min_time = self._view.fit_spectrum_settings.get_min_time()
        max_time = self._view.fit_spectrum_settings.get_max_time()
        bin_size = self._view.fit_spectrum_settings.get_bin_from_input()

        for i, run in enumerate(runs):
            if run.meta[files.TITLE_KEY] not in titles:
                continue

            asymmetry = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(bin_size).cut(min_time=min_time, max_time=max_time)
            raw_asymmetry = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].raw().bin(bin_size).cut(min_time=min_time, max_time=max_time)
            self._asymmetries[run.meta[files.TITLE_KEY]] = raw_asymmetry
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

            color = list(self._plot_model.color_options_values.values())[-i]
            self._view.fit_display.plot_asymmetry(time, asymmetry, uncertainty, None,
                                                  color=color,
                                                  marker='.',
                                                  linestyle='none',
                                                  fillstyle='none',
                                                  marker_color=color,
                                                  marker_size=5,
                                                  line_color=color,
                                                  line_width=1,
                                                  errorbar_color=color,
                                                  errorbar_style='none',
                                                  errorbar_width=1,
                                                  fit_color=color,
                                                  fit_linestyle='none',
                                                  label=run.meta[files.TITLE_KEY])

        for group in self.__variable_groups:
            if group is None:
                break
            time = domain.Time(input_array=None, bin_size=(max_time - min_time) * 1000 / 200, length=200,
                               time_zero=min_time)
            fit_asymmetry = self.__expression(time, **group)
            color = 'Black'
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

        if len(runs) > 0:
            self._view.fit_display.set_asymmetry_plot_limits(max_asymmetry, min_asymmetry)

        self._view.fit_display.finish_plotting(False)

    def _plot_fit(self):
        if not self.__update_if_table_changes:
            return

        expression, values = self._get_expression_and_values()
        self.__expression = expression
        if values is None:
            self.__variable_groups = []
            return

        self.__variable_groups = [values]
        self._update_display()

    def _get_expression_and_values(self):
        values = self._view.get_initial_values()
        expression = self._view.get_expression()

        if fit.is_valid_expression("A(t) = " + expression) and values is not None:
            variables = set(values.keys())
            variables.discard(fit.INDEPENDENT_VARIABLE)

            lambda_expression = fit.FitExpression(expression, variables)            

            return lambda_expression, values

        else:
            return None, None

    def _fit(self):
        self.__update_if_table_changes = False
        spec = fit.FitSpec()

        # Check user input on fit equation and update spec
        expression = self._view.get_expression()
        if not fit.is_valid_expression("A(t) = " + expression):
            self._view.highlight_input_red(self._view.input_fit_equation, True)
            self.__update_if_table_changes = True
            return
        else:
            self._view.highlight_input_red(self._view.input_fit_equation, False)
        spec.function = expression

        # Check user input on parameters and update spec
        try:
            guesses = self._view.get_initial_values()
            names = self._view.get_names()
            fixed = self._view.get_fixed()
            lowers = self._view.get_lower_bounds()
            uppers = self._view.get_upper_bounds()
            globs = self._view.get_check_global()
        except ValueError:
            self._view.highlight_input_red(self._view.table_parameters, True)
            self.__update_if_table_changes = True
            return

        if guesses is None:
            self._view.highlight_input_red(self._view.table_parameters, True)
            self.__update_if_table_changes = True
            return
        else:
            self._view.highlight_input_red(self._view.table_parameters, False)

        variables = {}
        for symbol in guesses.keys():
            variables[symbol] = fit.FitVar(symbol, names[symbol], guesses[symbol],
                                        fixed[symbol], lowers[symbol], uppers[symbol],
                                        globs[symbol], symbol == fit.INDEPENDENT_VARIABLE)
        spec.variables = variables

        # Check user input on runs and update spec
        titles = self._view.get_selected_run_titles()
        if len(titles) == 0:
            self._view.highlight_input_red(self._view.run_list, True)
            self.__update_if_table_changes = True
            return
        else:
            self._view.highlight_input_red(self._view.run_list, False)

        for title in titles:
            for run in self._runs:
                if run.meta[files.TITLE_KEY] == title:
                    spec.asymmetries[run.id] = self._asymmetries[title]

        spec.options[fit.FitOptions.ALPHA_CORRECT] = self._view.check_fit_alpha.isChecked()
        spec.options[fit.FitOptions.GLOBAL] = self._view.check_global_plus.isChecked()

        # Fit to spec
        engine = fit.FitEngine()
        dataset = engine.fit(spec)
        self._fit_service.add_dataset([dataset])
        self._update_alphas(dataset)
        self._update_fit_changes(dataset)
        self.__update_if_table_changes = True

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

        if type(selected_data) == fit.Fit:
            for i in range(self._view.run_list.count()):
                item = self._view.run_list.item(i)
                if item.text() == selected_data.title:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)

            self._view.update_variable_table(list(selected_data.variables.keys()))
            for symbol, variable in selected_data.variables.items():
                self._view.set_variable_value(symbol, value='{:.4f}'.format(variable.value))

            run = self._run_service.get_runs_by_ids([selected_data.run_id])[0]
            self._view.input_file_name.setText('{}_fit.txt'.format(run.meta['RunNumber']))
            self._view.input_folder_name.setText(files.load_last_used_directory())
            self._view.run_list.setEnabled(False)
            self._view.table_parameters.setEnabled(True)
            self.__expression = selected_data.expression
            self.__variable_groups = [selected_data.kwargs]
            self._view.input_fit_equation.setText(selected_data.expression_as_string)
            self._update_display()

        elif type(selected_data) == fit.FitDataset:
            titles = [f.title for f in selected_data.fits.values()]
            for i in range(self._view.run_list.count()):
                item = self._view.run_list.item(i)
                if item.text() in titles:
                    item.setCheckState(QtCore.Qt.Checked)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)

            self._view.update_variable_table(list(list(selected_data.fits.values())[0].variables.keys()))
            for symbol in list(selected_data.fits.values())[0].variables.keys():
                self._view.set_variable_value(symbol, value='*')
            self._view.input_file_name.setText('{}_fit.txt'.format(selected_data.id))
            self._view.input_folder_name.setText(files.load_last_used_directory())
            self._view.run_list.setEnabled(False)
            self._view.table_parameters.setEnabled(False)

            fits = list(selected_data.fits.values())
            self._view.input_fit_equation.setText(fits[0].expression_as_string)
            self.__expression = fits[0].expression
            self.__variable_groups = [f.kwargs for f in fits]
            self._update_display()

        else:
            self._view.run_list.setEnabled(True)
            self._view.table_parameters.setEnabled(True)

        self.__update_if_table_changes = True

    def _update_fit_changes(self, dataset):
        self.__update_if_table_changes = False
        self._view.select_first_fit_from_dataset(dataset.id)
        self.__update_if_table_changes = False
        self._view.select_top_child_run(dataset.id)
        self.__update_if_table_changes = False

        titles = self._view.get_selected_run_titles()
        for f in dataset.fits.values():
            if f.title in titles:
                for symbol, variable in f.variables.items():
                    self.__update_if_table_changes = False
                    self._view.set_variable_value(symbol, value='{:.4f}'.format(variable.value), name=variable.name,
                                                  is_fixed=variable.is_fixed, lower=variable.lower, upper=variable.upper,
                                                  is_global=variable.is_global)
                    self.__update_if_table_changes = False
        self.__update_if_table_changes = True
        self._update_display()

    def _update_alphas(self, dataset):
        ids = []
        alphas = []
        for f in dataset.fits.values():
            if fit.ALPHA in f.variables.keys():
                ids.append(f.run_id)
                alphas.append(f.variables[fit.ALPHA].value)

        if len(ids) > 0:
            self._run_service.update_alphas(ids, alphas)

    def update(self):
        runs = []
        for run in self._run_service.get_loaded_runs():
            if run.asymmetries[domain.RunDataset.FULL_ASYMMETRY] is not None:
                runs.append(run)
        self._runs = runs
        self._view.update_run_table(runs)
