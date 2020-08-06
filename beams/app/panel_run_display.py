
from PyQt5 import QtWidgets, QtCore

from app.model.model import PlotContext, MuonDataContext, FocusContext
from app.model import files, muon, mufyt
from app.dialog_misc import WarningMessageDialog, IntegrationDisplayDialog, FileDisplayDialog
from app.tab_histogram_display import HistogramDisplayTab
from app.tab_fit import FitDialog
from app.util import widgets


# noinspection PyArgumentList
class MuonRunPanel(widgets.StyleOneDockWidget):
    # noinspection PyArgumentList
    class PlotSettings(QtWidgets.QGroupBox):
        def __init__(self):
            super(MuonRunPanel.PlotSettings, self).__init__("Applies to all selected runs")

            self.all_color_options = QtWidgets.QComboBox()
            self.linestyle_options = QtWidgets.QComboBox()
            self.fit_linestyle_options = QtWidgets.QComboBox()
            self.line_color_options = QtWidgets.QComboBox()
            self.fit_color_options = QtWidgets.QComboBox()
            self.line_width_options = QtWidgets.QComboBox()
            self.marker_options = QtWidgets.QComboBox()
            self.marker_color_options = QtWidgets.QComboBox()
            self.marker_size_options = QtWidgets.QComboBox()
            self.fillstyle_options = QtWidgets.QComboBox()
            self.errorbar_style_options = QtWidgets.QComboBox()
            self.errorbar_color_options = QtWidgets.QComboBox()
            self.errorbar_width_options = QtWidgets.QComboBox()

            self._set_widget_dimensions()
            self._set_widget_attributes()
            self._set_widget_layout()

        def _set_widget_dimensions(self):
            pass

        def _set_widget_attributes(self):
            self.all_color_options.addItems(PlotContext.color_options_values.keys())
            self.fit_color_options.addItems(PlotContext.color_options_extra_values.keys())
            self.linestyle_options.addItems(PlotContext.linestyle_options_values.keys())
            self.fit_linestyle_options.addItems(PlotContext.linestyle_options_values.keys())
            self.line_color_options.addItems(PlotContext.color_options_extra_values.keys())
            self.line_width_options.addItems(PlotContext.line_width_options_values.keys())
            self.marker_options.addItems(PlotContext.marker_options_values.keys())
            self.marker_color_options.addItems(PlotContext.color_options_extra_values.keys())
            self.marker_size_options.addItems(PlotContext.marker_size_options_values.keys())
            self.fillstyle_options.addItems(PlotContext.fillstyle_options_values.keys())
            self.errorbar_style_options.addItems(PlotContext.errorbar_styles_values.keys())
            self.errorbar_color_options.addItems(PlotContext.color_options_extra_values.keys())
            self.errorbar_width_options.addItems(PlotContext.errorbar_width_values.keys())

        def _set_widget_layout(self):
            layout = QtWidgets.QGridLayout()
            layout.addWidget(QtWidgets.QLabel("Default Color"), 0, 0)
            layout.addWidget(self.all_color_options, 0, 1)
            layout.addWidget(QtWidgets.QLabel("Linestyle"), 1, 0)
            layout.addWidget(self.linestyle_options, 1, 1)
            layout.addWidget(QtWidgets.QLabel("Line Width"), 3, 0)
            layout.addWidget(self.line_width_options, 3, 1)
            layout.addWidget(QtWidgets.QLabel("Marker Style"), 4, 0)
            layout.addWidget(self.marker_options, 4, 1)
            layout.addWidget(QtWidgets.QLabel("Marker Color"), 5, 0)
            layout.addWidget(self.marker_color_options, 5, 1)
            layout.addWidget(QtWidgets.QLabel("Marker Size"), 6, 0)
            layout.addWidget(self.marker_size_options, 6, 1)
            layout.addWidget(QtWidgets.QLabel("Fillstyle"), 7, 0)
            layout.addWidget(self.fillstyle_options, 7, 1)
            layout.addWidget(QtWidgets.QLabel("Errorbar Style"), 8, 0)
            layout.addWidget(self.errorbar_style_options, 8, 1)
            layout.addWidget(QtWidgets.QLabel("Errorbar Color"), 9, 0)
            layout.addWidget(self.errorbar_color_options, 9, 1)
            layout.addWidget(QtWidgets.QLabel("Errorbar Width"), 10, 0)
            layout.addWidget(self.errorbar_width_options, 10, 1)
            layout.addWidget(QtWidgets.QLabel("Fit Line Color"), 11, 0)
            layout.addWidget(self.fit_color_options, 11, 1)
            layout.addWidget(QtWidgets.QLabel("Fit Linestyle"), 12, 0)
            layout.addWidget(self.fit_linestyle_options, 12, 1)

            form_layout = QtWidgets.QFormLayout()
            form_layout.addItem(layout)

            self.setLayout(form_layout)

    # noinspection PyArgumentList
    class DataSettings(QtWidgets.QGroupBox):
        def __init__(self):
            super(MuonRunPanel.DataSettings, self).__init__("Applies to all selected runs")

            self.see_file_button = widgets.StyleTwoButton("See File")
            self.see_histogram_button = widgets.StyleTwoButton("Histogram Controls")
            self.histogram_options = QtWidgets.QComboBox()
            self.meta_key_options = QtWidgets.QComboBox()
            self.meta_value_display = QtWidgets.QLineEdit()
            self.apply_correction_button = widgets.StyleTwoButton("Apply")
            self.fit_button = widgets.StyleTwoButton("Fit")
            self.alpha_input = QtWidgets.QLineEdit()
            self.integrate_button = widgets.StyleTwoButton("Integrate")
            self.integrate_options = QtWidgets.QComboBox()
            self.fit_control_button = widgets.StyleTwoButton('Fit Controls')

            self._set_widget_dimensions()
            self._set_widget_attributes()
            self._set_widget_layout()

        def _set_widget_dimensions(self):
            self.see_file_button.setFixedWidth(60)
            # self.see_histogram_button.setFixedWidth(60)
            self.apply_correction_button.setFixedWidth(60)
            self.meta_value_display.setMinimumWidth(80)

        def _set_widget_attributes(self):
            self.integrate_options.addItems(["Temperature", "Field"])

        def _set_widget_layout(self):
            spacing = 10
            layout = QtWidgets.QVBoxLayout()
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.meta_key_options)
            row.addSpacing(spacing)
            row.addWidget(self.meta_value_display)
            layout.addLayout(row)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(QtWidgets.QLabel("\u03b1 = "))
            row.addWidget(self.alpha_input)
            row.addSpacing(spacing)
            row.addWidget(self.apply_correction_button)
            layout.addLayout(row)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.integrate_options)
            row.addSpacing(spacing)
            row.addWidget(self.integrate_button)
            layout.addLayout(row)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            # row.addWidget(self.histogram_options)
            # row.addSpacing(spacing)
            row.addWidget(self.see_histogram_button)
            # row.addSpacing(spacing)
            # row.addWidget(self.see_file_button)
            # layout.addLayout(row)
            # layout.addSpacing(spacing)

            # layout.addWidget(self.fit_control_button)

            # row = QtWidgets.QHBoxLayout()
            # row.addWidget(self.fit_button)
            # layout.addLayout(row)
            # layout.addSpacing(spacing)

            form_layout = QtWidgets.QFormLayout()
            form_layout.addItem(layout)

            self.setLayout(form_layout)

    # noinspection PyArgumentList
    class Annotations(QtWidgets.QGroupBox):
        def __init__(self):
            super(MuonRunPanel.Annotations, self).__init__("Applies to current selected run")

    # noinspection PyArgumentList
    class FitSettings(QtWidgets.QGroupBox):
        def __init__(self):
            super(MuonRunPanel.FitSettings, self).__init__("Applies to all selected runs")

            self.expression_input = QtWidgets.QLineEdit()
            self.analyze_button = widgets.StyleTwoButton("Check")
            self.variable_table = QtWidgets.QTableWidget()
            self.fit_button = widgets.StyleOneButton("Refine")
            self.alpha_check = QtWidgets.QCheckBox()
            self.equation_choices = QtWidgets.QComboBox()
            self.plot_initial = widgets.StyleOneButton("Plot Fit")
            self.insert_sigma = widgets.StyleTwoButton(mufyt.SIGMA)
            self.insert_lambda = widgets.StyleTwoButton(mufyt.LAMBDA)
            self.insert_beta = widgets.StyleTwoButton(mufyt.BETA)
            self.insert_delta = widgets.StyleTwoButton(mufyt.DELTA)
            self.insert_alpha = widgets.StyleTwoButton(mufyt.ALPHA)
            self.insert_phi = widgets.StyleTwoButton(mufyt.PHI)
            self.insert_pi = widgets.StyleOneButton(mufyt.PI)
            self.insert_naught = widgets.StyleTwoButton(mufyt.NAUGHT)

            self._set_widget_dimensions()
            self._set_widget_attributes()
            self._set_widget_layout()

        def _set_widget_dimensions(self):
            self.analyze_button.setFixedWidth(60)

            insert_key_width = 20
            self.insert_pi.setFixedWidth(insert_key_width)
            self.insert_alpha.setFixedWidth(insert_key_width)
            self.insert_beta.setFixedWidth(insert_key_width)
            self.insert_delta.setFixedWidth(insert_key_width)
            self.insert_lambda.setFixedWidth(insert_key_width)
            self.insert_phi.setFixedWidth(insert_key_width)
            self.insert_sigma.setFixedWidth(insert_key_width)
            self.insert_naught.setFixedWidth(insert_key_width)

        def _set_widget_attributes(self):
            self.variable_table.setEnabled(False)
            self.fit_button.setEnabled(False)
            self.plot_initial.setEnabled(False)
            self.alpha_check.setChecked(True)

            self.variable_table.setColumnCount(3)
            self.variable_table.setHorizontalHeaderLabels(['Initial', '<', '>'])
            self.equation_choices.addItems(mufyt.EQUATION_DICTIONARY.keys())
            self.expression_input.setText(mufyt.EQUATION_DICTIONARY[self.equation_choices.currentText()])

            header = self.variable_table.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
            header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

            self.insert_pi.setToolTip("Pi (value, not a variable)")
            self.insert_sigma.setToolTip("Insert sigma")
            self.insert_phi.setToolTip("Insert phi")
            self.insert_lambda.setToolTip("Insert lambda")
            self.insert_delta.setToolTip("Insert delta")
            self.insert_beta.setToolTip("Insert beta")
            self.insert_alpha.setToolTip("Insert alpha")
            self.fit_button.setToolTip("Refine parameters and plot fit")
            self.plot_initial.setToolTip("Plot with initial parameters")
            self.insert_naught.setToolTip("Insert naught")
            self.analyze_button.setToolTip("Check expression is valid and pull out variables")

        def _set_widget_layout(self):
            spacing = 10
            layout = QtWidgets.QVBoxLayout()

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.alpha_check)
            row.addSpacing(5)
            row.addWidget(QtWidgets.QLabel("Include Alpha"))
            row.addStretch()
            layout.addLayout(row)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.equation_choices)
            row.addSpacing(5)
            row.addWidget(QtWidgets.QLabel(""))
            row.addStretch()
            layout.addLayout(row)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.expression_input)
            row.addSpacing(5)
            row.addWidget(self.analyze_button)
            layout.addLayout(row)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.insert_pi)
            row.addSpacing(2)
            row.addWidget(self.insert_sigma)
            row.addSpacing(2)
            row.addWidget(self.insert_phi)
            row.addSpacing(2)
            row.addWidget(self.insert_lambda)
            row.addSpacing(2)
            row.addWidget(self.insert_delta)
            row.addSpacing(2)
            row.addWidget(self.insert_beta)
            row.addSpacing(2)
            row.addWidget(self.insert_alpha)
            row.addSpacing(2)
            row.addWidget(self.insert_naught)
            layout.addLayout(row)
            layout.addSpacing(spacing)

            layout.addWidget(self.variable_table)
            layout.addSpacing(spacing)

            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.plot_initial)
            row.addSpacing(5)
            row.addWidget(self.fit_button)
            layout.addLayout(row)
            layout.addSpacing(spacing)

            form_layout = QtWidgets.QFormLayout()
            form_layout.addItem(layout)

            self.setLayout(form_layout)

    def __init__(self):
        super(MuonRunPanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())

        self.run_list = widgets.StyleOneListWidget()
        self.isolate_button = widgets.StyleOneButton("Isolate")
        self.plot_all_button = widgets.StyleOneButton("Plot All")
        self.clear_all_button = widgets.StyleTwoButton("Clear All")
        self.plot_settings = MuonRunPanel.PlotSettings()
        self.data_settings = MuonRunPanel.DataSettings()
        self.fit_settings = MuonRunPanel.FitSettings()
        self.annotations = MuonRunPanel.Annotations()

        self.data_settings_box = widgets.CollapsibleBox("Run Data Settings")
        self.plot_settings_box = widgets.CollapsibleBox("Run Plot Settings")
        self.fit_settings_box = widgets.CollapsibleBox("Fit Settings")
        self.annotations_box = widgets.CollapsibleBox("Run Annotations")

        self._scroll = QtWidgets.QScrollArea()

        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = MuonRunPanelPresenter(self)

        self.setEnabled(False)

    def _set_widget_attributes(self):
        self.run_list.setMaximumHeight(160)
        self.run_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.data_settings_box.toggle_button.pressed.connect(lambda: self._toggle_boxes('data'))
        self.plot_settings_box.toggle_button.pressed.connect(lambda: self._toggle_boxes('plot'))
        self.annotations_box.toggle_button.pressed.connect(lambda: self._toggle_boxes('annotate'))
        self.fit_settings_box.toggle_button.pressed.connect(lambda: self._toggle_boxes('fit'))

    def _toggle_boxes(self, box_id):
        if box_id != 'plot' and self.plot_settings_box.is_open():
            self.plot_settings_box.on_pressed()
        elif box_id != 'annotate' and self.annotations_box.is_open():
            self.annotations_box.on_pressed()
        elif box_id != 'data' and self.data_settings_box.is_open():
            self.data_settings_box.on_pressed()
        elif box_id != 'fit' and self.fit_settings_box.is_open():
            self.fit_settings_box.on_pressed()

        if box_id == 'plot':
            self.plot_settings_box.on_pressed()
        elif box_id == 'data':
            self.data_settings_box.on_pressed()
        elif box_id == 'fit':
            self.fit_settings_box.on_pressed()
        else:
            self.annotations_box.on_pressed()

    def _set_widget_layout(self):
        top_layout = QtWidgets.QVBoxLayout()

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.isolate_button)
        row.addWidget(self.plot_all_button)
        row.addWidget(self.clear_all_button)
        top_layout.addLayout(row)

        top_layout.addWidget(self.run_list)

        bottom_layout = QtWidgets.QVBoxLayout()

        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.data_settings)
        self.data_settings_box.setContentLayout(box)
        bottom_layout.addWidget(self.data_settings_box)

        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.fit_settings)
        self.fit_settings_box.setContentLayout(box)
        bottom_layout.addWidget(self.fit_settings_box)

        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.plot_settings)
        self.plot_settings_box.setContentLayout(box)
        bottom_layout.addWidget(self.plot_settings_box)

        box = QtWidgets.QVBoxLayout()
        box.addWidget(self.annotations)
        self.annotations_box.setContentLayout(box)
        bottom_layout.addWidget(self.annotations_box)

        bottom_layout.addStretch()

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        full_widget = QtWidgets.QWidget()
        full_widget.setLayout(layout)

        self.setWidget(full_widget)

    def setEnabled(self, enabled):
        super(MuonRunPanel, self).setEnabled(enabled)

        if enabled:
            self.data_settings_box.on_pressed()
        else:
            if self.data_settings_box.is_open():
                self.data_settings_box.on_pressed()
            elif self.plot_settings_box.is_open():
                self.plot_settings_box.on_pressed()
            elif self.annotations_box.is_open():
                self.annotations_box.on_pressed()
            elif self.fit_settings_box.is_open():
                self.fit_settings_box.on_pressed()

    def add_run_titles(self, run_titles):
        self.run_list.addItems(run_titles)

    def remove_run_titles(self, run_titles):
        for i in range(self.run_list.count()-1, -1, -1):
            if self.run_list.item(i).text() in run_titles:
                self.run_list.takeItem(i)

    def get_run_titles(self):
        return [self.run_list.item(i).text() for i in range(self.run_list.count())]

    def get_selected_titles(self):
        return [item.text() for item in self.run_list.selectedItems()]

    def get_unselected_titles(self):
        all_items = self.get_run_titles()
        selected_items = self.get_selected_titles()
        return [item for item in all_items if item not in selected_items]

    def get_meta_key(self):
        return self.data_settings.meta_key_options.currentText()

    def get_alpha(self):
        return float(self.data_settings.alpha_input.text())

    def get_histograms(self):
        items = []
        for i in range(self.data_settings.histogram_options.count()):
            items.append(self.data_settings.histogram_options.itemText(i))
        return items

    def get_histogram_label(self):
        return self.data_settings.histogram_options.currentText()

    def get_integration_type(self):
        return self.data_settings.integrate_options.currentText()

    def get_fit_expression(self):
        return self.fit_settings.expression_input.text()

    def insert_character_at_cursor(self, character):
        current_string = self.fit_settings.expression_input.text()

        if len(current_string) == 0:
            self.fit_settings.expression_input.setText(character)
            return

        position = self.fit_settings.expression_input.cursorPosition()

        if len(current_string) == position:
            current_string += character
            self.fit_settings.expression_input.setText(current_string)
            return

        new_string = ""
        for i, c in enumerate(current_string):
            if i == position:
                new_string += character
            new_string += c

        self.fit_settings.expression_input.setText(new_string)

    def get_current_equation(self):
        return self.fit_settings.equation_choices.currentText()

    def get_variable_data(self):
        variables = {}

        for i in range(self.fit_settings.variable_table.rowCount()):

            name = self.fit_settings.variable_table.verticalHeaderItem(i).text()
            initial = self.fit_settings.variable_table.item(i, 0).text()
            lower = self.fit_settings.variable_table.item(i, 1).text()
            upper = self.fit_settings.variable_table.item(i, 2).text()

            variables[name] = [initial, lower, upper]

        return variables

    def clear_titles(self):
        self.run_list.clear()

    def clear_variables(self):
        self.fit_settings.variable_table.setRowCount(0)

    def add_fit_row(self, variable):
        row_count = self.fit_settings.variable_table.rowCount()
        self.fit_settings.variable_table.insertRow(row_count)

        name = QtWidgets.QTableWidgetItem()
        initial = QtWidgets.QTableWidgetItem()
        lower_bound = QtWidgets.QTableWidgetItem()
        upper_bound = QtWidgets.QTableWidgetItem()

        name.setText(variable)
        initial.setText("1")
        lower_bound.setText("-Inf")
        upper_bound.setText("Inf")

        # self.fit_settings.variable_table.setItem(row_count, 0, name)
        self.fit_settings.variable_table.setVerticalHeaderItem(row_count, name)
        self.fit_settings.variable_table.setItem(row_count, 0, initial)
        self.fit_settings.variable_table.setItem(row_count, 1, lower_bound)
        self.fit_settings.variable_table.setItem(row_count, 2, upper_bound)

        # vertical_header = self.fit_settings.variable_table.verticalHeaderItem(row_count)
        # print(vertical_header.text())

    def set_first_selected(self):
        self.run_list.setCurrentRow(0)

    def _check_add_star(self, box, remove=False):
        for i in range(box.count()):
            if box.itemText(i) == "*":
                if remove:
                    box.removeItem(i)
                return
        else:
            if not remove:
                box.addItem("*")

    def set_default_color(self, color):
        if color == "*":
            self._check_add_star(self.plot_settings.all_color_options, False)
        else:
            self._check_add_star(self.plot_settings.all_color_options, True)

        self.plot_settings.all_color_options.setCurrentText(color)

    def set_linestyle(self, linestyle):
        if linestyle == "*":
            self._check_add_star(self.plot_settings.linestyle_options, False)
        else:
            self._check_add_star(self.plot_settings.linestyle_options, True)

        self.plot_settings.linestyle_options.setCurrentText(linestyle)

    def set_line_color(self, line_color):
        if line_color == "*":
            self._check_add_star(self.plot_settings.line_color_options, False)
        else:
            self._check_add_star(self.plot_settings.line_color_options, True)

        self.plot_settings.line_color_options.setCurrentText(line_color)

    def set_line_width(self, line_width):
        if line_width == "*":
            self._check_add_star(self.plot_settings.line_width_options, False)
        else:
            self._check_add_star(self.plot_settings.line_width_options, True)

        self.plot_settings.line_width_options.setCurrentText(line_width)

    def set_marker(self, marker):
        if marker == "*":
            self._check_add_star(self.plot_settings.marker_options, False)
        else:
            self._check_add_star(self.plot_settings.marker_options, True)

        self.plot_settings.marker_options.setCurrentText(marker)

    def set_marker_color(self, color):
        if color == "*":
            self._check_add_star(self.plot_settings.marker_color_options, False)
        else:
            self._check_add_star(self.plot_settings.marker_color_options, True)

        self.plot_settings.marker_color_options.setCurrentText(color)

    def set_fit_color(self, color):
        if color == "*":
            self._check_add_star(self.plot_settings.fit_color_options, False)
        else:
            self._check_add_star(self.plot_settings.fit_color_options, True)

        self.plot_settings.fit_color_options.setCurrentText(color)

    def set_marker_size(self, size):
        if size == "*":
            self._check_add_star(self.plot_settings.marker_size_options, False)
        else:
            self._check_add_star(self.plot_settings.marker_size_options, True)

        self.plot_settings.marker_size_options.setCurrentText(size)

    def set_fillstyle(self, fillstyle):
        if fillstyle == "*":
            self._check_add_star(self.plot_settings.fillstyle_options, False)
        else:
            self._check_add_star(self.plot_settings.fillstyle_options, True)

        self.plot_settings.fillstyle_options.setCurrentText(fillstyle)

    def set_errorbar_style(self, style):
        if style == "*":
            self._check_add_star(self.plot_settings.errorbar_style_options, False)
        else:
            self._check_add_star(self.plot_settings.errorbar_style_options, True)

        self.plot_settings.errorbar_style_options.setCurrentText(style)

    def set_errorbar_color(self, color):
        if color == "*":
            self._check_add_star(self.plot_settings.errorbar_color_options, False)
        else:
            self._check_add_star(self.plot_settings.errorbar_color_options, True)

        self.plot_settings.errorbar_color_options.setCurrentText(color)

    def set_errorbar_width(self, width):
        if width == "*":
            self._check_add_star(self.plot_settings.errorbar_width_options, False)
        else:
            self._check_add_star(self.plot_settings.errorbar_width_options, True)

        self.plot_settings.errorbar_width_options.setCurrentText(width)

    def set_header_meta_keys(self, keys, multiple=False):
        if multiple:
            self.data_settings.meta_key_options.setEnabled(False)
            self.data_settings.meta_value_display.setEnabled(False)
            return
        else:
            self.data_settings.meta_key_options.setEnabled(True)
            self.data_settings.meta_value_display.setEnabled(True)

        self.data_settings.meta_key_options.clear()
        self.data_settings.meta_key_options.addItems(keys)

    def set_header_display(self, value):
        self.data_settings.meta_value_display.setText(value)

    def set_alpha(self, alpha):
        if alpha != "*":
            float(alpha)
        self.data_settings.alpha_input.setText(str(alpha))

    def set_histograms(self, histograms):
        self.data_settings.histogram_options.clear()
        self.data_settings.histogram_options.addItems(histograms)

    def set_enabled_histograms(self, enabled):
        self.data_settings.histogram_options.clear()
        self.data_settings.histogram_options.setEnabled(enabled)
        self.data_settings.see_histogram_button.setEnabled(enabled)

    def set_enabled_meta(self, enabled):
        self.data_settings.meta_key_options.clear()
        self.data_settings.meta_value_display.clear()
        self.data_settings.meta_value_display.setEnabled(enabled)
        self.data_settings.meta_key_options.setEnabled(enabled)

    def set_enabled_file(self, enabled):
        self.data_settings.see_file_button.setEnabled(enabled)

    def set_enabled_fit(self, enabled):
        self.fit_settings.variable_table.setEnabled(enabled)
        self.fit_settings.fit_button.setEnabled(enabled)
        self.fit_settings.plot_initial.setEnabled(enabled)

    def set_expression(self, expression):
        self.fit_settings.expression_input.setText(expression)

    def set_parameter_values(self, variable, value):
        for i in range(self.fit_settings.variable_table.rowCount()):
            if self.fit_settings.variable_table.verticalHeaderItem(i).text() == variable:
                item = QtWidgets.QTableWidgetItem()
                try:
                    item.setText('{:8.6f}'.format(value))
                except ValueError:
                    item.setText(value)
                self.fit_settings.variable_table.takeItem(i, 0)
                self.fit_settings.variable_table.setItem(i, 0, item)


class MuonRunPanelPresenter:
    def __init__(self, view: MuonRunPanel):
        self._view = view
        self._model = MuonRunPanelModel(self)
        self._runs = None
        self._styles = None
        self.__populating_settings = False
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.run_list.itemSelectionChanged.connect(self._run_selection_changed)
        self._view.isolate_button.released.connect(self._isolate_clicked)
        self._view.plot_all_button.released.connect(self._plot_all_clicked)
        self._view.clear_all_button.released.connect(self._clear_all_clicked)
        self._view.data_settings.fit_button.released.connect(self._fit_clicked)
        self._view.data_settings.meta_key_options.currentTextChanged.connect(self._meta_key_changed)
        self._view.data_settings.apply_correction_button.released.connect(self._apply_correction_clicked)
        self._view.data_settings.see_file_button.released.connect(self._see_file_clicked)
        self._view.data_settings.see_histogram_button.released.connect(self._see_histogram_clicked)
        self._view.data_settings.integrate_button.released.connect(self._integrate_clicked)
        self._view.fit_settings.analyze_button.released.connect(self._analyze_clicked)
        self._view.fit_settings.fit_button.released.connect(self._fit_clicked)
        self._view.fit_settings.equation_choices.currentTextChanged.connect(self._equation_changed)
        self._view.fit_settings.plot_initial.clicked.connect(self._plot_initial_fit)
        self._view.fit_settings.insert_alpha.clicked.connect(lambda: self._insert_key_clicked(mufyt.ALPHA))
        self._view.fit_settings.insert_beta.clicked.connect(lambda: self._insert_key_clicked(mufyt.BETA))
        self._view.fit_settings.insert_delta.clicked.connect(lambda: self._insert_key_clicked(mufyt.DELTA))
        self._view.fit_settings.insert_lambda.clicked.connect(lambda: self._insert_key_clicked(mufyt.LAMBDA))
        self._view.fit_settings.insert_phi.clicked.connect(lambda: self._insert_key_clicked(mufyt.PHI))
        self._view.fit_settings.insert_sigma.clicked.connect(lambda: self._insert_key_clicked(mufyt.SIGMA))
        self._view.fit_settings.insert_pi.clicked.connect(lambda: self._insert_key_clicked(mufyt.PI))
        self._view.fit_settings.insert_naught.clicked.connect(lambda: self._insert_key_clicked(mufyt.NAUGHT))
        self._view.fit_settings.expression_input.textChanged.connect(lambda: self._view.set_enabled_fit(False))
        self._view.data_settings.fit_control_button.released.connect(lambda: FitDialog.launch([]))

        self._view.plot_settings.all_color_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.DEFAULT_COLOR,
                                                 self._view.plot_settings.all_color_options.currentText()))
        self._view.plot_settings.linestyle_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.LINESTYLE,
                                                 self._view.plot_settings.linestyle_options.currentText()))
        self._view.plot_settings.line_color_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.LINE_COLOR,
                                                 self._view.plot_settings.line_color_options.currentText()))
        self._view.plot_settings.line_width_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.LINE_WIDTH,
                                                 self._view.plot_settings.line_width_options.currentText()))
        self._view.plot_settings.marker_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.MARKER,
                                                 self._view.plot_settings.marker_options.currentText()))
        self._view.plot_settings.marker_color_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.MARKER_COLOR,
                                                 self._view.plot_settings.marker_color_options.currentText()))
        self._view.plot_settings.marker_size_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.MARKER_SIZE,
                                                 self._view.plot_settings.marker_size_options.currentText()))
        self._view.plot_settings.fillstyle_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.FILLSTYLE,
                                                 self._view.plot_settings.fillstyle_options.currentText()))
        self._view.plot_settings.errorbar_style_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.ERRORBAR_STYLE,
                                                 self._view.plot_settings.errorbar_style_options.currentText()))
        self._view.plot_settings.errorbar_color_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.ERRORBAR_COLOR,
                                                 self._view.plot_settings.errorbar_color_options.currentText()))
        self._view.plot_settings.errorbar_width_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.ERRORBAR_WIDTH,
                                                 self._view.plot_settings.errorbar_width_options.currentText()))
        self._view.plot_settings.fit_color_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.FIT_COLOR,
                                                 self._view.plot_settings.fit_color_options.currentText()))
        self._view.plot_settings.fit_linestyle_options.currentTextChanged.connect(
            lambda: self._plot_parameter_changed(PlotContext.Keys.FIT_LINESTYLE,
                                                 self._view.plot_settings.fit_linestyle_options.currentText()))

    def _insert_key_clicked(self, key):
        self._view.insert_character_at_cursor(key)

    def _equation_changed(self):
        equation_title = self._view.get_current_equation()
        self._view.set_expression(mufyt.EQUATION_DICTIONARY[equation_title])
        self._analyze_clicked()

    def _analyze_clicked(self):
        expression = self._view.get_fit_expression()

        ind, variables, _ = self._model.parse_expression(expression)
        if ind is None or variables is None:
            self._view.set_enabled_fit(False)
            WarningMessageDialog.launch(["Invalid Expression. Must have form similar to f(x) = a*x^2"])
            return

        self._view.clear_variables()
        for var in variables:
            self._view.add_fit_row(var)
        self._view.set_enabled_fit(True)

        self._view.get_variable_data()

    def _plot_initial_fit(self):
        variables = self._view.get_variable_data()
        function = self._view.get_fit_expression()
        ind, _, expression = self._model.parse_expression(function)
        try:
            self._model.set_initial_fit_parameters(ind, expression, variables, self._view.get_selected_titles())
        except ValueError:
            WarningMessageDialog.launch(["Invalid input."])

    def _fit_clicked(self):
        variables = self._view.get_variable_data()
        function = self._view.get_fit_expression()
        ind, _, expression = self._model.parse_expression(function)
        try:
            self._model.get_fit(ind, expression, variables, self._view.get_selected_titles())
        except ValueError:
            WarningMessageDialog.launch(["Invalid input."])
        variables = self._model.get_run_fit_parameters(self._view.get_selected_titles())[0].free_variables

        for k, v in variables.items():
            self._view.set_parameter_values(k, v[0])

    def _isolate_clicked(self):
        self._model.set_visibility_for_runs(True, self._view.get_selected_titles(), True)
        self._model.set_visibility_for_runs(False, self._view.get_unselected_titles())

    def _plot_all_clicked(self):
        self._model.set_visibility_for_runs(True)

    def _clear_all_clicked(self):
        self._model.set_visibility_for_runs(False)

    def _run_selection_changed(self):
        self._populate_settings()
        self._model.set_focus_runs(self._view.get_selected_titles())

    def _meta_key_changed(self):
        meta_key = self._view.get_meta_key()
        if len(meta_key) > 0 and self._runs is not None and not self.__populating_settings:
            self._view.set_header_display(str(list(self._runs.values())[0].meta[meta_key]))

    def _apply_correction_clicked(self):
        titles = self._view.get_selected_titles()
        if len(titles) > 0:
            try:
                alpha = self._view.get_alpha()
                self._model.correct_asymmetries(titles, alpha)
            except ValueError:
                WarningMessageDialog.launch(["Invalid input for alpha."])

    def _integrate_clicked(self):
        x_axis_label = self._view.get_integration_type()
        titles = self._view.get_selected_titles()
        if x_axis_label == "Field":
            x_axis_data = self._model.get_run_fields(titles)
        else:
            x_axis_data = self._model.get_run_temperatures(titles)
        integration_data = self._model.get_run_integrations(titles)
        IntegrationDisplayDialog.launch([integration_data, x_axis_label, x_axis_data])

    def _see_file_clicked(self):
        filename = list(self._runs.values())[0].file
        with open(filename) as f:
            file_content = f.read()
        FileDisplayDialog.launch([filename, file_content])

    def _see_histogram_clicked(self):
        run = list(self._runs.values())[0]
        file = files.file(run.file)
        histogram_label = self._view.get_histogram_label()
        histograms = self._view.get_histograms()
        HistogramDisplayTab.launch(histogram=file.read_data()[histogram_label], id=run.id, label=histogram_label, histograms=histograms, file=file, meta=run.meta)

    def _plot_parameter_changed(self, key, value):
        selected_items = self._view.get_selected_titles()
        if len(selected_items) > 0 and value != "*" and not self.__populating_settings:
            self._model.change_parameter(selected_items, key, value)

    def _populate_settings(self):
        self.__populating_settings = True  # Because this sends a lot of signals because QComboBoxes are changing
        current_selected_titles = self._view.get_selected_titles()
        self._runs = self._model.get_run_by_title(current_selected_titles)
        self._styles = self._model.get_style_by_title(current_selected_titles)

        if len(current_selected_titles) > 1:
            self._populate_with_multiple_selected()
        elif len(current_selected_titles) == 1:
            self._populate_with_single_selected()
        self.__populating_settings = False

    def _populate_with_single_selected(self):
        style = list(self._styles.values())[0]
        run = list(self._runs.values())[0]

        self._view.set_enabled_meta(True)
        self._view.set_enabled_file(True)
        self._view.set_default_color(PlotContext.color_options[style[PlotContext.Keys.DEFAULT_COLOR]])
        self._view.set_alpha(run.alpha)
        self._view.set_errorbar_color(PlotContext.color_options_extra[style[PlotContext.Keys.ERRORBAR_COLOR]])
        self._view.set_fit_color(PlotContext.color_options_extra[style[PlotContext.Keys.FIT_COLOR]])
        self._view.set_errorbar_style(PlotContext.errorbar_styles[style[PlotContext.Keys.ERRORBAR_STYLE]])
        self._view.set_errorbar_width(PlotContext.errorbar_width[style[PlotContext.Keys.ERRORBAR_WIDTH]])
        self._view.set_fillstyle(PlotContext.fillstyle_options[style[PlotContext.Keys.FILLSTYLE]])
        self._view.set_header_meta_keys(run.meta.keys())
        self._view.set_line_color(PlotContext.color_options_extra[style[PlotContext.Keys.LINE_COLOR]])
        self._view.set_line_width(PlotContext.line_width_options[style[PlotContext.Keys.LINE_WIDTH]])
        self._view.set_linestyle(PlotContext.linestyle_options[style[PlotContext.Keys.LINESTYLE]])
        self._view.set_marker(PlotContext.marker_options[style[PlotContext.Keys.MARKER]])
        self._view.set_marker_color(PlotContext.color_options_extra[style[PlotContext.Keys.MARKER_COLOR]])
        self._view.set_marker_size(PlotContext.marker_size_options[style[PlotContext.Keys.MARKER_SIZE]])

        if files.file(run.file).DATA_FORMAT == files.Format.HISTOGRAM:
            self._view.set_enabled_histograms(True)
            self._view.set_histograms(run.meta[files.HIST_TITLES_KEY])
        else:
            self._view.set_enabled_histograms(False)

    def _populate_with_multiple_selected(self):
        self._view.set_enabled_histograms(False)
        self._view.set_enabled_meta(False)
        self._view.set_enabled_file(False)

        values = {run.alpha for run in self._runs.values()}
        if len(values) > 1:
            self._view.set_alpha("*")
        else:
            self._view.set_alpha(values.pop())

        values = {PlotContext.color_options[style[PlotContext.Keys.DEFAULT_COLOR]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_default_color("*")
        else:
            self._view.set_default_color(values.pop())

        values = {PlotContext.errorbar_width[style[PlotContext.Keys.ERRORBAR_WIDTH]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_errorbar_width("*")
        else:
            self._view.set_errorbar_width(values.pop())

        values = {PlotContext.color_options_extra[style[PlotContext.Keys.ERRORBAR_COLOR]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_errorbar_color("*")
        else:
            self._view.set_errorbar_color(values.pop())

        values = {PlotContext.color_options_extra[style[PlotContext.Keys.FIT_COLOR]] for style in
                  self._styles.values()}
        if len(values) > 1:
            self._view.set_fit_color("*")
        else:
            self._view.set_fit_color(values.pop())

        values = {PlotContext.errorbar_styles[style[PlotContext.Keys.ERRORBAR_STYLE]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_errorbar_style("*")
        else:
            self._view.set_errorbar_style(values.pop())

        values = {PlotContext.marker_size_options[style[PlotContext.Keys.MARKER_SIZE]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_marker_size("*")
        else:
            self._view.set_marker_size(values.pop())

        values = {PlotContext.line_width_options[style[PlotContext.Keys.LINE_WIDTH]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_line_width("*")
        else:
            self._view.set_line_width(values.pop())

        values = {PlotContext.linestyle_options[style[PlotContext.Keys.LINESTYLE]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_linestyle("*")
        else:
            self._view.set_linestyle(values.pop())

        values = {PlotContext.fillstyle_options[style[PlotContext.Keys.FILLSTYLE]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_fillstyle("*")
        else:
            self._view.set_fillstyle(values.pop())

        values = {PlotContext.color_options_extra[style[PlotContext.Keys.MARKER_COLOR]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_marker_color("*")
        else:
            self._view.set_marker_color(values.pop())

        values = {PlotContext.color_options_extra[style[PlotContext.Keys.LINE_COLOR]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_line_color("*")
        else:
            self._view.set_line_color(values.pop())

        values = {PlotContext.marker_options[style[PlotContext.Keys.MARKER]] for style in self._styles.values()}
        if len(values) > 1:
            self._view.set_marker("*")
        else:
            self._view.set_marker(values.pop())

    def update(self):
        print('Updating the Run Display')
        run_titles = self._model.get_current_titles()

        if len(run_titles) == 0:
            self._view.clear_titles()
            self._view.setEnabled(False)
            return

        current_titles = self._view.get_run_titles()
        new_titles = [title for title in run_titles if title not in current_titles]
        old_titles = [title for title in current_titles if title not in run_titles]
        self._view.add_run_titles(new_titles)
        self._view.remove_run_titles(old_titles)

        if not self._view.isEnabled():
            self._view.setEnabled(True)
            self._view.set_first_selected()

        self._populate_settings()


class MuonRunPanelModel:
    def __init__(self, observer):
        self._observer = observer
        self._data_context = MuonDataContext()
        self._plot_context = PlotContext()
        self._focus_context = FocusContext()
        self._data_context.subscribe(self)
        self._plot_context.subscribe(self)
        self._runs = self._data_context.get_runs()
        self._styles = self._plot_context.get_styles()

    def get_current_titles(self):
        return [run.meta[files.TITLE_KEY] for run in self._data_context.get_runs()]

    def get_current_run_ids(self):
        return [run.id for run in self._data_context.get_runs()]

    def get_run_by_title(self, titles):
        runs = dict()
        for title in titles:
            for run in self._runs:
                if run.meta[files.TITLE_KEY] == title:
                    runs[title] = run
        return runs

    def get_style_by_title(self, titles):
        styles = dict()
        for title in titles:
            for style_key in self._styles:
                style = self._styles[style_key]
                if style[PlotContext.Keys.LABEL] == title:
                    styles[title] = style
        return styles

    def set_focus_runs(self, titles):
        run_ids = titles
        if titles is not None:
            run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        self._focus_context.focus_runs(run_ids)

    def set_visibility_for_runs(self, visible, titles=None, stop_signal=False):
        run_ids = titles
        if titles is not None:
            run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        self._plot_context.change_visibilities(visible=visible, run_id=run_ids, stop_signal=stop_signal)

    def change_parameter(self, titles, key, value):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        self._plot_context.change_style_parameter(run_ids, key, value)

    def correct_asymmetries(self, titles, alpha, beta=None):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        self._data_context.apply_correction_to_runs_by_id(run_ids, alpha, beta)

    def get_run_integrations(self, titles):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        runs = [self._data_context.get_run_by_id(run_id) for run_id in run_ids]
        return [muon.calculate_muon_integration(run) for run in runs]

    def get_run_temperatures(self, titles):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        runs = [self._data_context.get_run_by_id(run_id) for run_id in run_ids]
        return [float(run.meta[files.TEMPERATURE_KEY].split('(')[0].split('K')[0]) for run in runs]

    def get_run_fit_parameters(self, titles):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        runs = [self._data_context.get_run_by_id(run_id) for run_id in run_ids]
        return [run.fit for run in runs]

    def get_run_fields(self, titles):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        runs = [self._data_context.get_run_by_id(run_id) for run_id in run_ids]
        return [float(run.meta[files.FIELD_KEY].split('(')[0].split('G')[0]) for run in runs]

    def get_fit(self, independent_variable, expression, variables, titles):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        self._data_context.set_fit_data_for_runs(run_ids, expression, independent_variable, variables, True)

    def set_initial_fit_parameters(self, independent_variable, expression, variables, titles):
        run_ids = [run.id for run in self.get_run_by_title(titles).values()]
        self._data_context.set_fit_data_for_runs(run_ids, expression, independent_variable, variables, False)

    def parse_expression(self, expression):
        if mufyt.is_valid_expression(expression):
            ind, exp = mufyt.split_expression(expression)
            vars = mufyt.parse(exp)
            if ind in vars:
                vars.remove(ind)
            return ind, vars, exp
        else:
            return None, None, None

    def update(self):
        self._runs = self._data_context.get_runs()
        self._styles = self._plot_context.get_styles()
        self.notify()

    def notify(self):
        self._observer.update()

