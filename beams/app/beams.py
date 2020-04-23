
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
        self.setStyleSheet(main_window.StyleFile(r'resources/light_style.qss',
                                                 r'resources/light_style_vars.txt').style)
        self.main_program_window = None

    def run(self):
        """
        Creates the main window and starts the application.
        """

        self.main_program_window = main_window.MainWindow()
        self.main_program_window.show()
        sys.exit(self.exec_())

    @staticmethod
    def set_last_used_directory(path):
        if len(path) == 0:
            path = "."

        if os.path.exists(path) and os.path.isdir(path):
            with open(r'resources/config.txt', 'w') as f:
                f.write(path)

    @staticmethod
    def load_last_used_directory():

        try:
            with open(r'resources/config.txt', 'r+') as f:
                path = f.readline().strip()

                if os.path.exists(r'{}'.format(path)) and os.path.isdir(r'{}'.format(path)):
                    return path
                else:
                    f.truncate(0)
                    f.seek(0)
                    f.write(os.getcwd())
        except FileNotFoundError:
            BEAMS.set_last_used_directory(os.getcwd())

        return os.getcwd()


if __name__ == '__main__':
    app = BEAMS()
    app.run()
