
from PyQt5 import QtCore

import app.model.data_access as dao


class Signals(QtCore.QObject):
    changed = QtCore.pyqtSignal()


class StyleService:
    __dao = dao.StyleDAO()
