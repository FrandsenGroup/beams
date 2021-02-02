
import abc
from PyQt5 import QtWidgets


class Panel(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def createSupportPanel(self) -> QtWidgets.QDockWidget:
        pass


class PanelPresenter(abc.ABC):
    def __init__(self, view: Panel):
        self._view = view

    def update(self):
        pass
