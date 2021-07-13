
from PyQt5 import QtWidgets, QtCore, QtGui

from app.gui.consolepanel import MainConsolePanel
from app.gui.histogrampanel import HistogramPanel
from app.gui.plottingpanel import PlottingPanel
from app.resources import resources
from app.gui.fittingpanel import FittingPanel
from app.util import qt_constants


# noinspection PyArgumentList
class MainWindow(QtWidgets.QMainWindow):
    """
    MainWindow widget for the program. Creates the default arrangement of panels.
    """

    class MainWindowTabs(QtWidgets.QTabWidget):
        def __init__(self):
            super(MainWindow.MainWindowTabs, self).__init__()
            self.__index = 0
            self._set_style()

            self.plotting_panel = PlottingPanel()
            i = self.addTab(self.plotting_panel, '')
            self.setTabIcon(i, QtGui.QIcon(resources.PLOTTING_CLICKED_IMAGE))
            self.setIconSize(QtCore.QSize(35, 35))

            self.histogram_panel = HistogramPanel()
            i = self.addTab(self.histogram_panel, '')
            self.setTabIcon(i, QtGui.QIcon(resources.HISTOGRAM_IMAGE))
            self.setIconSize(QtCore.QSize(36, 36))

            self.fit_panel = FittingPanel()
            i = self.addTab(self.fit_panel, '')
            self.setTabIcon(i, QtGui.QIcon(resources.FITTING_IMAGE))
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

    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())

        self.setWindowTitle("BEAMS | Basic and Effective Analysis for Muon Spin-Spectroscopy")
        self.statusBar()

        self._tabs = MainWindow.MainWindowTabs()
        self._plotting_support = self._tabs.plotting_panel.createSupportPanel()
        self._histogram_support = self._tabs.histogram_panel.createSupportPanel()
        self._fit_support = self._tabs.fit_panel.createSupportPanel()
        self._current_support = self._plotting_support

        self._set_default_panels()
        self._set_callbacks()

    def _set_callbacks(self):
        self._tabs.currentChanged.connect(self._change_support_panel)

    def _change_support_panel(self):
        self.removeDockWidget(self._current_support)

        index = self._tabs.currentIndex()
        if index == 0:
            self._current_support = self._plotting_support
        elif index == 1:
            self._current_support = self._histogram_support
        elif index == 2:
            self._current_support = self._fit_support

        self._current_support.show()
        self.addDockWidget(qt_constants.LeftDockWidgetArea, self._current_support)

    def _set_default_panels(self):
        """
        Sets the default panels of the main window for µSR analysis.
        """
        self.addDockWidget(qt_constants.LeftDockWidgetArea, MainConsolePanel())

        temp_docking_widget = QtWidgets.QDockWidget()
        temp_docking_widget.setWidget(self._tabs)
        temp_docking_widget.setTitleBarWidget(QtWidgets.QWidget())
        self.addDockWidget(qt_constants.RightDockWidgetArea, temp_docking_widget, qt_constants.Horizontal)

        self.addDockWidget(qt_constants.LeftDockWidgetArea, self._tabs.plotting_panel.createSupportPanel())

    def set_status_message(self, message):
        """
        Sets the status message for the main window.
        :param message: the message to be displayed.
        """

        self.setStatusTip(message)

    def update(self, signal):
        pass


# noinspection PyArgumentList
class StyleFile:
    """
    A class to parse the variable file and store the updated QSS file.
    """

    def __init__(self, qss_file, var_file):
        qss_vars = self._parse_var_file(var_file)
        self.style = self._parse_qss_file(qss_file, qss_vars)

    @staticmethod
    def _parse_var_file(var_file):
        """
        Gets all the variables and stores in a dictionary

        :param var_file: The variable file
        :return qss_vars: A dictionary of variables
        """
        var_read_file = open(var_file).read().split()
        keys = [key for key in var_read_file if key[0] == '@']
        values = [value for value in var_read_file if value[0] == '#']
        qss_vars = {k: v for k, v in zip(keys, values)}
        return qss_vars

    @staticmethod
    def _parse_qss_file(qss_file, qss_vars):
        """
        Replaces all the variables in the qss files with their actual values.

        :param qss_file: The file with the QSS custom styles.
        :param qss_vars: The variables as a dictionary
        :return qss_updated_file: The updated file as a string
        """
        qss_read_file = open(qss_file).read()
        qss_updated_file = ""
        current_char = 0
        for _ in qss_read_file:
            if current_char == len(qss_read_file):
                break
            for key in qss_vars.keys():
                len_key = len(key)
                if qss_read_file[current_char:current_char+len_key] == key:
                    qss_updated_file += qss_vars[key]
                    current_char += len_key
                    break
            else:
                qss_updated_file += qss_read_file[current_char]
                current_char += 1
        return qss_updated_file

