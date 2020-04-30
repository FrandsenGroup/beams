
# Standard Library Packages
import sys
import os

# Installed Packages
from PyQt5 import QtWidgets

# BEAMS Modules
from app import main_window


class BEAMS(QtWidgets.QApplication):
    """
    Main program class. Initializing will not instantiate any GUI elements until run() is called.
    """

    def __init__(self):
        super(BEAMS, self).__init__(sys.argv)
        self.setStyleSheet(main_window.StyleFile(r'beams/app/resources/light_style.qss',
                                                 r'beams/app/resources/light_style_vars.txt').style)
        self.main_program_window = None

    def run(self):
        """
        Creates the main window and starts the application.
        """

        self.main_program_window = main_window.MainWindow()
        self.main_program_window.show()
        sys.exit(self.exec_())
