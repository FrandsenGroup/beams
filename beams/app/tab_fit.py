
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np

from app.util import widgets
from app.model import mufyt


# noinspection PyArgumentList
class FitDialog(QtWidgets.QWidget):
    class FitCanvas(FigureCanvas):
        def __init__(self):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.canvas_axes = self.figure.add_subplot(111, label='Canvas')

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

    def __init__(self):
        super(FitDialog, self).__init__()

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

        self.fit_display = FitDialog.FitCanvas()
        self.special_characters = widgets.CollapsibleBox("Special Characters")

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

        self.label_global_plus = QtWidgets.QLabel("Global+")
        self.label_ordering = QtWidgets.QLabel("Order by")
        self.label_use_previous = QtWidgets.QLabel("Use Previous Run")

        self.check_batch_fit = QtWidgets.QCheckBox()
        self.check_global_plus = QtWidgets.QCheckBox()
        self.check_use_previous = QtWidgets.QCheckBox()

        self.insert_phi = widgets.StyleTwoButton(mufyt.PHI)
        self.insert_alpha = widgets.StyleTwoButton(mufyt.ALPHA)
        self.insert_sigma = widgets.StyleTwoButton(mufyt.SIGMA)
        self.insert_naught = widgets.StyleTwoButton(mufyt.NAUGHT)
        self.insert_lambda = widgets.StyleTwoButton(mufyt.LAMBDA)
        self.insert_delta = widgets.StyleTwoButton(mufyt.DELTA)
        self.insert_beta = widgets.StyleTwoButton(mufyt.BETA)
        self.insert_pi = widgets.StyleOneButton(mufyt.PI)

        self.group_preset_functions = QtWidgets.QGroupBox("Loaded Functions")
        self.group_user_functions = QtWidgets.QGroupBox("User Functions")
        self.group_special_characters = QtWidgets.QGroupBox("Special Characters")
        self.group_batch_options = QtWidgets.QGroupBox("Batch")
        self.group_spectrum_options = QtWidgets.QGroupBox("Spectrum")
        self.group_save_results = QtWidgets.QGroupBox("Save")

        self._set_widget_layout()
        self._set_widget_attributes()
        self._set_widget_dimensions()

    def _set_widget_attributes(self):
        self.option_preset_fit_equations.addItems(list(mufyt.EQUATION_DICTIONARY.keys()))
        self.option_user_fit_equations.addItem("None")
        self.option_run_ordering.addItems(['Field', 'Temp', 'Run'])

        self.input_user_equation_name.setPlaceholderText("Function Name")
        self.input_user_equation.setPlaceholderText("Function (e.g. \"\u03B2 * (t + \u03BB)\")")
        self.input_fit_equation.setPlaceholderText("Fit Equation")

        self.table_parameters.setColumnCount(6)
        self.table_parameters.setRowCount(2)
        header = self.table_parameters.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)
        self.table_parameters.setHorizontalHeaderLabels(['Name', 'Value', 'Step', '<', '>', 'Global'])
        item = QtWidgets.QTableWidgetItem()
        item.setText(mufyt.LAMBDA)
        self.table_parameters.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        item.setText(mufyt.PHI)
        self.table_parameters.setVerticalHeaderItem(1, item)
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        check = QtWidgets.QCheckBox()
        layout.addWidget(check)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        self.table_parameters.setCellWidget(0, 5, widget)
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        check = QtWidgets.QCheckBox()
        layout.addWidget(check)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        self.table_parameters.setCellWidget(1, 5, widget)

        file_item = QtWidgets.QListWidgetItem('006515 | Cu2IrO3 LF=1KG T=7K', self.run_list)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)
        file_item = QtWidgets.QListWidgetItem('006516 | Cu2IrO3 LF=200G T=.05K', self.run_list)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)
        file_item = QtWidgets.QListWidgetItem('006517 | Cu2IrO3 LF=200G T=.125K', self.run_list)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)
        file_item = QtWidgets.QListWidgetItem('006518 | Cu2IrO3 LF=200G T=.5K ', self.run_list)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)
        file_item = QtWidgets.QListWidgetItem('006519 | Cu2IrO3 LF=200G T=1K ', self.run_list)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)

        self.input_fit_equation.setText("exp(-\u03BB*t) * cos(2*\u03C0*v*t + \u03C0*\u03D5/180) + exp(-\u03BB*t)")

        self.check_use_previous.setEnabled(False)
        self.check_global_plus.setEnabled(False)
        self.option_run_ordering.setEnabled(False)
        self.label_global_plus.setEnabled(False)
        self.label_ordering.setEnabled(False)
        self.label_use_previous.setEnabled(False)

        x = np.linspace(0, 10)
        self.fit_display.canvas_axes.plot(x, np.sin(x) + np.random.randn(50), label='006515 | Cu2IrO3 LF=1KG T=7K', linestyle='None', marker='.')
        self.fit_display.canvas_axes.plot(x, np.sin(x) + 2*np.random.randn(50), label='006516 | Cu2IrO3 LF=200G T=.05K', linestyle='None', marker='.')
        self.fit_display.canvas_axes.plot(x, np.sin(x) + 3*np.random.randn(50), label='006517 | Cu2IrO3 LF=200G T=.125K', linestyle='None', marker='.')
        # Number of accent colors in the color scheme
        # self.fit_display.canvas_axes.legend(loc='upper right')

    def _set_widget_dimensions(self):
        self.button_done.setFixedWidth(60)
        self.button_fit.setFixedWidth(60)
        # self.button_save_results.setFixedWidth(60)
        self.button_check_equation.setFixedWidth(60)
        self.button_insert_user_equation.setFixedWidth(60)
        self.button_insert_preset_equation.setFixedWidth(60)
        self.button_lookup_folder.setFixedWidth(60)
        self.button_save_user_equation.setFixedWidth(60)

        self.option_run_ordering.setFixedWidth(80)
        self.option_user_fit_equations.setFixedWidth(120)
        self.option_preset_fit_equations.setFixedWidth(120)

        self.input_user_equation_name.setFixedWidth(80)
        self.input_user_equation.setMinimumWidth(160)
        self.input_packing.setFixedWidth(60)
        self.input_spectrum_min.setFixedWidth(60)
        self.input_spectrum_max.setFixedWidth(60)

        self.table_parameters.setFixedWidth(300)
        self.run_list.setFixedWidth(300)
        self.group_spectrum_options.setFixedWidth(120)
        self.group_batch_options.setFixedWidth(160)
        self.group_batch_options.setMaximumHeight(110)
        self.group_save_results.setMaximumHeight(110)
        self.group_spectrum_options.setMaximumHeight(110)

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

        main_layout.addSpacing(10)

        row = QtWidgets.QHBoxLayout()
        row.addSpacing(20)
        row.addWidget(QtWidgets.QLabel("A(t) = "))
        row.addSpacing(5)
        row.addWidget(self.input_fit_equation)
        row.addWidget(self.button_check_equation)
        row.addSpacing(20)
        main_layout.addLayout(row)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.insert_pi)
        row.addWidget(self.insert_alpha)
        row.addWidget(self.insert_beta)
        row.addWidget(self.insert_delta)
        row.addWidget(self.insert_lambda)
        row.addWidget(self.insert_phi)
        row.addWidget(self.insert_sigma)
        row.addWidget(self.insert_naught)
        layout = QtWidgets.QFormLayout()
        layout.addRow(row)
        self.group_special_characters.setLayout(layout)
        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.group_special_characters)
        self.special_characters.setContentLayout(box)
        main_layout.addWidget(self.special_characters)

        main_layout.addSpacing(10)

        left_side = QtWidgets.QVBoxLayout()
        left_side.addWidget(self.table_parameters)
        left_side.addWidget(self.run_list)
        left_side.setStretch(5, 5)

        right_side = QtWidgets.QVBoxLayout()
        right_side.setStretch(5,5)
        right_side.addWidget(self.fit_display)

        row = QtWidgets.QHBoxLayout()
        row.addLayout(left_side)
        row.addLayout(right_side)
        row.setStretch(5, 5)
        main_layout.addLayout(row)

        layout = QtWidgets.QFormLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_batch_fit)
        row.addWidget(QtWidgets.QLabel("Batch Fit"))
        row.addStretch()
        layout.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_global_plus)
        row.addWidget(self.label_global_plus)
        row.addStretch()
        layout.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.check_use_previous)
        row.addWidget(self.label_use_previous)
        row.addStretch()
        layout.addRow(row)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.label_ordering)
        row.addSpacing(2)
        row.addWidget(self.option_run_ordering)
        row.addStretch()
        layout.addRow(row)
        self.group_batch_options.setLayout(layout)

        full_row = QtWidgets.QHBoxLayout()
        full_row.addWidget(self.group_batch_options)

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

        full_row.addWidget(self.group_spectrum_options)

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

        full_row.addWidget(self.group_save_results)

        full_row.addSpacing(8)
        column = QtWidgets.QVBoxLayout()
        column.addStretch()
        column.addWidget(self.button_fit)
        column.addSpacing(4)
        column.addWidget(self.button_done)
        column.addStretch()
        full_row.addLayout(column)
        full_row.addSpacing(8)

        main_layout.addLayout(full_row)

        self.setLayout(main_layout)

    @staticmethod
    def launch(args):
        dialog = FitDialog(args)
        return dialog.exec()
