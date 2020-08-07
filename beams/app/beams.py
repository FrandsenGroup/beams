
# Standard Library Packages
import sys

# Installed Packages
from PyQt5 import QtWidgets, QtCore, QtGui

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
        db = QtGui.QFontDatabase()
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-Black.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-BlackItalic.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-Bold.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-BoldItalic.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-Italic.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-Light.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-LightItalic.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-Regular.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-Thin.ttf')
        db.addApplicationFont(r'beams/app/resources/Lato/Lato-ThinItalic.ttf')
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
        frame.setGeometry(50, 50, 950, 950)
        frame.show()
        sys.exit(self.exec_())
