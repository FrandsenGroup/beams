
import abc
from PyQt5 import QtWidgets, QtCore


class Panel(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def createSupportPanel(self) -> QtWidgets.QDockWidget:
        pass


class PanelPresenter(QtCore.QObject):
    def __init__(self, view: Panel):
        super().__init__()
        self._view = view

    def update(self, signal):
        pass
