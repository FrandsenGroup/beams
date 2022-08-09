import os

from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import darkdetect

from app.gui.dialogs import dialog_misc
from app.resources import resources
from app.model import services, files
from app.util import qt_widgets, report


class IntegrationDialog(QtWidgets.QDialog):
    class IntegrationCanvas(FigureCanvas):
        def __init__(self, num_integrations):
            self._draw_pending = True
            self._is_drawing = True
            FigureCanvas.__init__(self, Figure())
            self.axes = [self.figure.add_subplot(1, num_integrations, n+1) for n in range(num_integrations)]

    class IntegrationToolbar(NavigationToolbar2QT):
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

    def __init__(self, x_axis, x_axis_label, integrations, titles):
        super().__init__()
        self.setWindowTitle("Integration")
        self.__system_service = services.SystemService()
        self._integrations = integrations
        self._main = QtWidgets.QMainWindow()
        self.canvas = IntegrationDialog.IntegrationCanvas(len(integrations))
        self._main.addToolBar(IntegrationDialog.IntegrationToolbar(self.canvas, self._main))
        self._ind_var_label = x_axis_label
        self._ind_var_array = x_axis

        layout = QtWidgets.QVBoxLayout()

        for i, integration in enumerate(integrations):
            self.canvas.axes[i].errorbar(x_axis, integration[0], integration[1], linestyle='None', marker='o')
            self.canvas.axes[i].set_xlabel(x_axis_label)
            self.canvas.axes[i].set_title(titles[i])

            if i == 0:
                self.canvas.axes[i].set_ylabel("Integrated Asymmetry")

        self.setMinimumWidth(800)
        self.set_stylesheet()
        self._main.setCentralWidget(self.canvas)
        layout.addWidget(self._main)

        self.export_buttons = [qt_widgets.StyleOneButton(f"Export Integration {i+1}") for i in range(len(integrations))]
        for button in self.export_buttons:
            button.setToolTip("Export integration to a .int file")
        hbox = QtWidgets.QHBoxLayout()
        hbox.addSpacing(80)
        for i, button in enumerate(self.export_buttons):
            hbox.addWidget(button)
            hbox.addStretch()
            button.released.connect(lambda integration_index=i: self._export_button_clicked(integration_index))
        layout.addLayout(hbox)

        self.setLayout(layout)

    def set_stylesheet(self):
        style = self.__system_service.get_theme_preference()
        if style == self.__system_service.Themes.DEFAULT:
            if darkdetect.isDark():
                style = self.__system_service.Themes.DARK
            else:
                style = self.__system_service.Themes.LIGHT

        color = resources.DARK_COLOR if style == self.__system_service.Themes.DARK else resources.LIGHT_COLOR
        tick_color = resources.LIGHT_COLOR if style == self.__system_service.Themes.DARK else resources.DARK_COLOR

        self.canvas.figure.set_facecolor(color)
        for axes in self.canvas.axes:
            axes.set_facecolor(color)
            axes.tick_params(axis='x', colors=tick_color)
            axes.tick_params(axis='y', colors=tick_color)
            axes.spines['left'].set_color(tick_color)
            axes.spines['bottom'].set_color(tick_color)
            axes.spines['right'].set_color(tick_color)
            axes.spines['top'].set_color(tick_color)
            axes.title.set_color(tick_color)
            axes.xaxis.label.set_color(tick_color)
            axes.yaxis.label.set_color(tick_color)
            axes.figure.canvas.draw()

    def _export_button_clicked(self, integration_index):
        save_path = self._get_save_path("Integration (*{})".format(files.Extensions.INTEGRATION))
        if not save_path:
            return
        try:
            self.write_integration(save_path, integration_index)
        except Exception as e:
            report.report_exception(e)
            dialog_misc.WarningMessageDialog.launch(["Error writing integration file: " + str(e)])

    # this is duplicated code, we should break this into a Dialog superclass
    def _get_save_path(self, filter):
        path = QtWidgets.QFileDialog.getSaveFileName(caption="Save", filter=filter,
                                                     directory=self.__system_service.get_last_used_directory())[0]
        if path:
            split_path = os.path.split(path)
            self.__system_service.set_last_used_directory(split_path[0])
            return path

    def write_integration(self, save_path, integration_index):
        integration_string = "# Integration\n"
        integration_string += "# {:<12}\t".format(self._ind_var_label)
        integration_string += "{:<21}\t".format("Integrated Asymmetry")
        integration_string += "{:<12}\t\n".format("Uncertainty")

        integration = self._integrations[integration_index]
        for i, integration_tuple in enumerate(zip(*integration)):
            integration_string += "{:<12}\t".format(self._ind_var_array[i])
            integration_string += "{:<21.5f}\t".format(float(integration_tuple[0]))
            integration_string += "{:<12.5f}\t\n".format(float(integration_tuple[1]))

        with open(save_path, 'w', encoding="utf-8") as out_file_object:
            out_file_object.write("# BEAMS\n"
                                  + integration_string)

    @staticmethod
    def launch(x_axis, x_axis_label, integrations, titles):
        dialog = IntegrationDialog(x_axis, x_axis_label, integrations, titles)
        return dialog.exec()
