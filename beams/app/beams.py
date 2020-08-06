
# Standard Library Packages
import sys

# Installed Packages
from PyQt5 import QtWidgets, QtCore

# BEAMS Modules
from app import main_window
from app.util import widgets


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
        frame = widgets.Frame()
        vbox = QtWidgets.QVBoxLayout(frame.content_widget())
        vbox.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        vbox.addWidget(self.main_program_window)
        frame.show()
        sys.exit(self.exec_())
