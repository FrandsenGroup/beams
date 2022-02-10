"""
Main entry point for the application.
"""

# Standard Library Packages
import logging
import sys

# Installed Packages
import darkdetect
import qdarkstyle
import sentry_sdk
from PyQt5 import QtWidgets, QtGui

# BEAMS Modules
from app.gui import mainwindow
from app.model import services
from app.resources import resources
from app.util import qt_constants, report


class BEAMS(QtWidgets.QApplication):
    """
    Main program class. Initializing will not instantiate any GUI elements until run() is called.
    """

    def __init__(self):
        super(BEAMS, self).__init__(sys.argv)
        sentry_sdk.init(
            "https://ff7cf26a5b3d4d2ab1ff98320448fa04@o1139782.ingest.sentry.io/6196236",
            max_breadcrumbs=50,
            traces_sample_rate=1.0,
            attach_stacktrace=True,
            release="beams@0.1.0",
            environment="development"
        )

        self.__system_service = services.SystemService()
        self.__file_service = services.FileService()
        self.__system_service.load_configuration_file()
        logging.getLogger('matplotlib').setLevel(logging.ERROR)

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        file = logging.FileHandler(resources.QT_LOG_FILE)
        file.setLevel(logging.DEBUG)
        logger.addHandler(file)

        stream = logging.StreamHandler()
        stream.setLevel(logging.INFO)
        logger.addHandler(stream)

        pix = QtGui.QPixmap(resources.SPLASH_IMAGE)
        self.splash = QtWidgets.QSplashScreen(pix.scaledToHeight(200, qt_constants.SmoothTransformation))
        self.splash.show()
        self.processEvents()

        if self.__system_service.get_theme_preference() == self.__system_service.Themes.LIGHT:
            self.setStyleSheet(qdarkstyle.load_stylesheet(palette=qdarkstyle.LightPalette))
        elif self.__system_service.get_theme_preference() == self.__system_service.Themes.DARK:
            self.setStyleSheet(qdarkstyle.load_stylesheet(palette=qdarkstyle.DarkPalette))
        else:
            if darkdetect.isDark():
                self.setStyleSheet(qdarkstyle.load_stylesheet(palette=qdarkstyle.DarkPalette))
            else:
                self.setStyleSheet(qdarkstyle.load_stylesheet(palette=qdarkstyle.LightPalette))

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
        self.main_program_window.show()
        self.splash.finish(self.main_program_window)
        sys.exit(self.exec_())

    def exec_(self) -> int:
        try:
            i = super(BEAMS, self).exec_()
            return i
        except Exception as e:
            report.report_exception(e)
        finally:
            self.__system_service.write_configuration_file()
