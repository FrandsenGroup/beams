
import logging

from PyQt5 import QtCore

import app.model.data_access as dao


class Signals(QtCore.QObject):
    added = QtCore.pyqtSignal()
    changed = QtCore.pyqtSignal()


class FitService:
    __dao = dao.FitDAO()
    __logger = logging.getLogger('FitService')
    signals = Signals()

    @staticmethod
    def get_fit_datasets():
        return FitService.__dao.get_fits()

    @staticmethod
    def add_dataset(datasets, suppress_signal=False):
        FitService.__dao.add_fits(datasets)

        if not suppress_signal:
            FitService.__logger.debug("Emitted: added")
            FitService.signals.added.emit()

    @staticmethod
    def changed():
        FitService.__logger.debug("Emitted: changed")
        FitService.signals.changed.emit()
