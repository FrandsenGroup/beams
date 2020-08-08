
from PyQt5 import QtWidgets, QtCore, QtGui

from app.panel_file_manager import FileManagerPanel
from app.panel_muon_plot import MuonPlotPanel
from app.panel_run_display import MuonRunPanel
from app.tab_histogram_display import HistogramDisplayTab
from app.tab_fit import FitDialog


# noinspection PyArgumentList
class MainWindow(QtWidgets.QMainWindow):
    """
    MainWindow widget for the program. Creates the default arrangement of panels.
    """
    LEFT_PANEL_MAX = 280  # pixels

    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        self.presenter = MainWindowPresenter()  # Connect to Presenter

        # self.setGeometry(50, 50, 950, 950)
        self.setWindowTitle("BEAMS | Basic and Effective Analysis for Muon Spin-Spectroscopy")
        self.statusBar()

        # Initialize the menu bar
        # self.menu_bar = self.menuBar()
        #
        # self.exit_act = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        # self.exit_act.setShortcut('Ctrl+Q')
        # self.exit_act.setStatusTip('Exit application.')
        #
        # self.add_data_act = QtWidgets.QAction(QtGui.QIcon('addDada.png'), '&Add Data File', self)
        # self.add_data_act.setStatusTip('Add a data file to current session.')
        #
        # file_menu = self.menu_bar.addMenu('&File')
        # file_menu.addAction(self.add_data_act)
        # file_menu.addSeparator()
        # file_menu.addAction(self.exit_act)
        # self._set_callbacks()

        # Initialize the window panels
        self._set_default_panels()

    def _set_callbacks(self):
        pass

    def _set_default_panels(self):
        """
        Sets the default panels of the main window for µSR analysis.
        """
        self._file_manager = FileManagerPanel()
        self._file_manager.setFixedHeight(200)
        self._file_manager.setFixedWidth(280)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._file_manager)

        self._tabs = QtWidgets.QTabWidget()
        self._tabs.setAutoFillBackground(True)
        self._tabs.setBackgroundRole(QtGui.QPalette.Base)
        p = self._tabs.palette()
        p.setColor(self._tabs.backgroundRole(), QtGui.QColor('#FFFFFF'))
        self._tabs.setPalette(p)

        self._plot_panel_one = MuonPlotPanel()
        # self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._plot_panel_one, QtCore.Qt.Horizontal)

        self._plot_panel_two = MuonPlotPanel()
        self._plot_panel_two.set_max_time(.25)
        self._plot_panel_two.set_bin_input(2)
        self._plot_panel_two.set_bin_slider(2)
        # self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._plot_panel_two, QtCore.Qt.Horizontal)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self._plot_panel_one)
        row.addWidget(self._plot_panel_two)
        temp_widget = QtWidgets.QWidget()
        temp_widget.setLayout(row)
        self._tabs.setDocumentMode(True)
        # self._tabs.setStyleSheet("QTabBar { background-color: red; }")
        i = self._tabs.addTab(temp_widget, '')
        self._tabs.setTabIcon(i, QtGui.QIcon(r'beams\app\resources\icons\plotting_icon.png'))
        self._tabs.setIconSize(QtCore.QSize(35, 35))

        i = self._tabs.addTab(HistogramDisplayTab(), '')
        self._tabs.setTabIcon(i, QtGui.QIcon(r'beams\app\resources\icons\histo_icon.png'))
        self._tabs.setIconSize(QtCore.QSize(36, 36))

        i = self._tabs.addTab(FitDialog(), '')
        self._tabs.setTabIcon(i, QtGui.QIcon(r'beams\app\resources\icons\fitting_icon.png'))
        self._tabs.setIconSize(QtCore.QSize(35, 35))

        self._tabs.addTab(QtWidgets.QWidget(), '')

        # self._tabs.tabBar().setAutoFillBackground(True)
        # self._tabs.tabBar().setBackgroundRole(QtGui.QPalette.Background)
        # p = self._tabs.tabBar().palette()
        # p.setColor(self._tabs.tabBar().backgroundRole(), QtGui.QColor('#070536'))
        # self._tabs.tabBar().setPalette(p)

        temp_docking_widget = QtWidgets.QDockWidget()
        temp_docking_widget.setWidget(self._tabs)
        temp_docking_widget.setTitleBarWidget(QtWidgets.QWidget())
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, temp_docking_widget, QtCore.Qt.Horizontal)

        self._run_panel = MuonRunPanel()
        self._run_panel.setFixedWidth(280)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._run_panel)

    def set_status_message(self, message):
        """
        Sets the status message for the main window.
        :param message: the message to be displayed.
        """

        self.setStatusTip(message)

    def update(self):
        pass


class MainWindowPresenter:
    """
    Presenter for the MainWindow, takes data from users interfacing with view and can pass that
    information to the model, update the view, etc.
    """
    def __init__(self):
        self._model = None # Connect to Model


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

