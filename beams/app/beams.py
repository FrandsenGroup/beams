"""
Main entry point for the application.
"""

# Standard Library Packages
import os
import sys
import logging

# Installed Packages
from PyQt5 import QtWidgets, QtCore, QtGui

# BEAMS Modules
from app.util import qt_widgets, qt_constants
from app.model import services
from app.resources import resources
from app.gui import mainwindow


class BEAMS(QtWidgets.QApplication):
    """
    Main program class. Initializing will not instantiate any GUI elements until run() is called.
    """

    def __init__(self):
        super(BEAMS, self).__init__(sys.argv)
        self.__system_service = services.SystemService()
        self.__file_service = services.FileService()
        self.__system_service.load_configuration_file()
        logging.basicConfig(filename=resources.QT_LOG_FILE, level=logging.DEBUG)
        logging.getLogger('matplotlib').setLevel(logging.ERROR)

        pix = QtGui.QPixmap(resources.SPLASH_IMAGE)
        self.splash = QtWidgets.QSplashScreen(pix.scaledToHeight(200, qt_constants.SmoothTransformation))
        self.splash.show()
        self.processEvents()

        self.setStyleSheet(mainwindow.StyleFile(resources.QSS_STYLE_SHEET, resources.DARK_STYLE_VARIABLES).style)
        db = QtGui.QFontDatabase()
        db.addApplicationFont(resources.LATO_BLACK_FONT)
        db.addApplicationFont(resources.LATO_BLACK_ITALIC_FONT)
        db.addApplicationFont(resources.LATO_BOLD_FONT)
        db.addApplicationFont(resources.LATO_BOLD_ITALIC_FONT)
        db.addApplicationFont(resources.LATO_ITALIC_FONT)
        db.addApplicationFont(resources.LATO_LIGHT_FONT)
        db.addApplicationFont(resources.LATO_LIGHT_ITALIC_FONT)
        db.addApplicationFont(resources.LATO_REGULAR_FONT)
        db.addApplicationFont(resources.LATO_THIN_FONT)
        db.addApplicationFont(resources.LATO_THIN_ITALIC_FONT)
        self.main_program_window = None

    def run(self):
        """
        Creates the main window and starts the application.
        """

        self.main_program_window = mainwindow.MainWindow()
        # frame = qt_widgets.Frame()
        # vbox = QtWidgets.QVBoxLayout(frame.content_widget())
        # vbox.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        # vbox.addWidget(self.main_program_window)
        # size_object = QtWidgets.QDesktopWidget().screenGeometry(-1)
        # frame.setGeometry(10, 10, size_object.width()-20, size_object.height()-100)
        # frame.show()

        # self.splash.finish(frame)

        self.main_program_window.show()
        sys.exit(self.exec_())

    def exec_(self) -> int:
        i = super(BEAMS, self).exec_()
        self.__system_service.write_configuration_file()
        return i
