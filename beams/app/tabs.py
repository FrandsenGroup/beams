
from PyQt5 import QtWidgets, QtGui, QtCore
from app.panel_muon_plot import MuonPlotPanel
from app.tab_histogram_display import HistogramDisplayTab
from app.tab_fit import FitDialog
from app.resources import resources


# noinspection PyArgumentList
class MainWindowTabs(QtWidgets.QTabWidget):
    def __init__(self):
        super(MainWindowTabs, self).__init__()
        self.__index = 0
        self._set_style()

        self._plot_panel_one = MuonPlotPanel()
        self._plot_panel_two = MuonPlotPanel()
        self._plot_panel_two.set_max_time(.25)
        self._plot_panel_two.set_bin_input(2)
        self._plot_panel_two.set_bin_slider(2)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self._plot_panel_one)
        row.addWidget(self._plot_panel_two)
        temp_widget = QtWidgets.QWidget()
        temp_widget.setLayout(row)

        i = self.addTab(temp_widget, '')
        self.setTabIcon(i, QtGui.QIcon(resources.PLOTTING_CLICKED_IMAGE))
        self.setIconSize(QtCore.QSize(35, 35))

        i = self.addTab(HistogramDisplayTab(), '')
        self.setTabIcon(i, QtGui.QIcon(resources.HISTOGRAM_IMAGE))
        self.setIconSize(QtCore.QSize(36, 36))

        i = self.addTab(FitDialog(), '')
        self.setTabIcon(i, QtGui.QIcon(resources.FITTING_IMAGE))
        self.setIconSize(QtCore.QSize(35, 35))

        i = self.addTab(QtWidgets.QLabel('Useless tab.. Kinda sad'), '')
        self.setTabIcon(i, QtGui.QIcon(resources.DOWNLOAD_IMAGE))
        self.setIconSize(QtCore.QSize(35, 35))

        i = self.addTab(QtWidgets.QLabel('No help for you.'), '')
        self.setTabIcon(i, QtGui.QIcon(resources.QUESTION_IMAGE))
        self.setIconSize(QtCore.QSize(35, 35))

        self.currentChanged.connect(self._selection_changed)

    def _set_style(self):
        self.setDocumentMode(True)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Base)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self.setPalette(p)

    def _selection_changed(self):
        if self.__index == 0:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.PLOTTING_IMAGE))

        elif self.__index == 1:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.HISTOGRAM_IMAGE))

        elif self.__index == 2:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.FITTING_IMAGE))

        elif self.__index == 3:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.DOWNLOAD_IMAGE))

        elif self.__index == 4:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.QUESTION_IMAGE))

        self.__index = self.currentIndex()

        if self.__index == 0:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.PLOTTING_CLICKED_IMAGE))

        elif self.__index == 1:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.HISTOGRAM_CLICKED_IMAGE))

        elif self.__index == 2:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.FITTING_CLICKED_IMAGE))

        elif self.__index == 3:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.DOWNLOAD_CLICKED_IMAGE))

        elif self.__index == 4:
            self.setTabIcon(self.__index, QtGui.QIcon(resources.QUESTION_CLICKED_IMAGE))
