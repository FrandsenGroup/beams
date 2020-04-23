
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
