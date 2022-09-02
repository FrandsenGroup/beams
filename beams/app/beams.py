"""
Main entry point for the application.
"""

# Standard Library Packages
import logging
import sys

# Installed Packages
import darkdetect
import qdarkstyle
from PyQt5 import QtWidgets, QtGui

# BEAMS Modules
from app.gui import mainwindow
from app.gui.dialogs.dialog_misc import NotificationDialog, PermissionsMessageDialog
from app.model import services
from app.resources import resources
from app.util import qt_constants, report


class BEAMS(QtWidgets.QApplication):
    """
    Main program class. Initializing will not instantiate any GUI elements until run() is called.
    """

    def __init__(self):
        super(BEAMS, self).__init__(sys.argv)
        report.init_reporting()

        self.__system_service = services.SystemService()
        self.__file_service = services.FileService()
        self.__system_service.load_configuration_file()

        pix = QtGui.QPixmap(resources.SPLASH_IMAGE)
        self.splash = QtWidgets.QSplashScreen(pix.scaledToHeight(200, qt_constants.SmoothTransformation))
        self.splash.show()
        self.processEvents()

        if self.__system_service.get_theme_preference() == self.__system_service.Themes.LIGHT:
            self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=qdarkstyle.LightPalette))
        elif self.__system_service.get_theme_preference() == self.__system_service.Themes.DARK:
            self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=qdarkstyle.DarkPalette))
        else:
            if darkdetect.isDark():
                self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=qdarkstyle.DarkPalette))
            else:
                self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5', palette=qdarkstyle.LightPalette))

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

        qr = self.main_program_window.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.main_program_window.move(qr.topLeft())

        self.splash.finish(self.main_program_window)
        self._check_report_status()
        self._check_version()
        sys.exit(self.exec_())

    def _check_report_status(self):
        if self.__system_service.get_report_errors() is not None:
            return  # The user has already indicated their preference

        response = PermissionsMessageDialog.launch([
            "Hi! Would you like to automatically report errors back to our research group so we can continue "
            "to improve our software?\n"
        ])

        self.__system_service.set_report_errors(response == PermissionsMessageDialog.Codes.OKAY)

    def _check_version(self):
        notify = self.__system_service.get_notify_user_of_update()
        current_version = self.__system_service.get_current_version()
        _, latest_version = self.__system_service.get_latest_version()

        report.log_info(f"Running beams@{current_version}")

        if notify and latest_version != "unknown":
            NotificationDialog.launch(f"New version available! Currently {current_version} is installed, {latest_version} is available.",
                                      "Do not show again (until next release).",
                                      lambda user_checked: self.__system_service.set_notify_user_of_update(not user_checked))

    def exec_(self) -> int:
        try:
            i = super(BEAMS, self).exec_()
            return i
        except Exception as e:
            report.report_exception(e)
        finally:
            report.close()
            self.__system_service.write_configuration_file()
