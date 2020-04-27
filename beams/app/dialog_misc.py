
import socket
import enum

from PyQt5 import QtWidgets, QtCore

from util import widgets


# noinspection PyArgumentList
class AddFileDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        FILE_SYSTEM = 1
        WEB_DOWNLOAD = 2

    def __init__(self):
        super(AddFileDialog, self).__init__()

        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel('Would you like to add files from the local file system or online.')
        self.pos_button = widgets.StyleOneButton('From disk')
        self.neg_button = widgets.StyleOneButton('From musr.ca')
        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(100)
        self.neg_button.setFixedWidth(100)

        self.pos_button.released.connect(lambda: self._set_type(True))
        self.neg_button.released.connect(lambda: self._set_type(False))

        try:
            socket.create_connection(("www.google.com", 80))
        except OSError:
            self.neg_button.setEnabled(False)

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)

        col.setAlignment(message, QtCore.Qt.AlignCenter)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        row.setAlignment(self.pos_button, QtCore.Qt.AlignRight)
        row.setAlignment(self.neg_button, QtCore.Qt.AlignLeft)
        col.addLayout(row)
        self.setLayout(col)

    def _set_type(self, x=False):
        if x:
            self.done(AddFileDialog.Codes.FILE_SYSTEM)
        else:
            self.done(AddFileDialog.Codes.WEB_DOWNLOAD)

    @staticmethod
    def launch():
        dialog = AddFileDialog()
        return dialog.exec()


# noinspection PyArgumentList
class WarningMessageDialog(QtWidgets.QDialog):
    def __init__(self, args=None):
        super(WarningMessageDialog, self).__init__()
        if args:
            if len(args) == 2:
                pos_function = args[1]
                error_message = args[0]
            else:
                pos_function = None
                error_message = args[0]
        else:
            error_message = None
            pos_function = None

        self.setWindowTitle('Error')
        message = QtWidgets.QLabel(error_message)
        pos_button = widgets.StyleOneButton('Okay')
        self.setMinimumWidth(300)
        self.setMinimumHeight(80)
        pos_button.setFixedWidth(80)

        if pos_function:
            pos_button.released.connect(lambda: pos_function())

        pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()

        col.addWidget(message)
        col.addWidget(pos_button)
        col.setAlignment(message, QtCore.Qt.AlignCenter)
        col.setAlignment(pos_button, QtCore.Qt.AlignCenter)
        self.setLayout(col)

    @staticmethod
    def launch(args=None):
        dialog = WarningMessageDialog(args)
        return dialog.exec()


# noinspection PyArgumentList
class PermissionsMessageDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        OKAY = 0
        CANCEL = 1

    def __init__(self, args):
        super(PermissionsMessageDialog, self).__init__()
        self.setWindowTitle('Permission')
        message = QtWidgets.QLabel(args[0])
        self.pos_button = widgets.StyleOneButton('Okay')
        self.neg_button = widgets.StyleTwoButton('Cancel')
        self.setMinimumWidth(300)
        self.setMinimumWidth(80)
        self.pos_button.setFixedWidth(80)
        self.neg_button.setFixedWidth(80)

        self.pos_button.released.connect(lambda: self.done(PermissionsMessageDialog.Codes.OKAY))

        self.neg_button.released.connect(lambda: self.done(PermissionsMessageDialog.Codes.CANCEL))

        self.neg_button.released.connect(lambda: self.close())
        self.pos_button.released.connect(lambda: self.close())

        col = QtWidgets.QVBoxLayout()
        col.addWidget(message)
        col.setAlignment(message, QtCore.Qt.AlignCenter)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.pos_button)
        row.addWidget(self.neg_button)
        row.setAlignment(self.pos_button, QtCore.Qt.AlignRight)
        row.setAlignment(self.neg_button, QtCore.Qt.AlignLeft)
        col.addLayout(row)
        self.setLayout(col)

    @staticmethod
    def launch(args):
        dialog = PermissionsMessageDialog(args)
        return dialog.exec()