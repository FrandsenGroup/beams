
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
import darkdetect

from app.resources import resources
from app.model import services


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
        self._main = QtWidgets.QMainWindow()
        self.canvas = IntegrationDialog.IntegrationCanvas(len(integrations))
        self._main.addToolBar(IntegrationDialog.IntegrationToolbar(self.canvas, self._main))

        layout = QtWidgets.QVBoxLayout()

        for i, integration in enumerate(integrations):
            self.canvas.axes[i].plot(x_axis, integration, linestyle='None', marker='o')
            self.canvas.axes[i].set_xlabel(x_axis_label)
            self.canvas.axes[i].set_title(titles[i])

            if i == 0:
                self.canvas.axes[i].set_ylabel("Integrated Asymmetry")

        self.setMinimumWidth(800)
        self.set_stylesheet()
        self._main.setCentralWidget(self.canvas)
        layout.addWidget(self._main)
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

    @staticmethod
    def launch(x_axis, x_axis_label, integrations, titles):
        dialog = IntegrationDialog(x_axis, x_axis_label, integrations, titles)
        return dialog.exec()
