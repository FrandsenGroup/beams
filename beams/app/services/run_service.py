
import logging

from PyQt5 import QtCore

import app.model.data_access as dao
import app.model.domain as domain


class Signals(QtCore.QObject):
    added = QtCore.pyqtSignal()
    changed = QtCore.pyqtSignal()
    loaded = QtCore.pyqtSignal()


class RunService:
    signals = Signals()
    __dao = dao.RunDAO()
    __logger = logging.getLogger("RunService")

    @staticmethod
    def get_runs():
        return RunService.__dao.get_runs()

    @staticmethod
    def get_runs_by_ids(ids):
        return RunService.__dao.get_runs_by_ids(ids)

    @staticmethod
    def get_loaded_runs():
        loaded_runs = []
        for run in RunService.__dao.get_runs():
            if run.isLoaded:
                loaded_runs.append(run)
        return loaded_runs

    def load_runs(self, ids):
        pass

    def combine_histograms(self, ids, titles):
        pass

    @staticmethod
    def recalculate_asymmetries(ids):
        for run in RunService.__dao.get_runs_by_ids(ids):
            if len(run.histograms_used) == 2:
                run.asymmetries[domain.RunDataset.FULL_ASYMMETRY] = domain.Asymmetry(
                    histogram_one=run.histograms[run.histograms_used[0]],
                    histogram_two=run.histograms[run.histograms_used[1]],
                    alpha=run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].alpha)

                if run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                    run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                    run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()

    @staticmethod
    def add_runs(paths):
        builder = domain.DataBuilder()
        for path in paths:
            run = builder.build_minimal(path)
            RunService.__dao.add_runs([run])

        RunService.__logger.debug("Emitted: added")
        RunService.signals.added.emit()

    @staticmethod
    def remove_runs_by_ids(ids):
        RunService.__dao.remove_runs_by_ids(ids)

        RunService.__logger.debug("Emitted: loaded")
        RunService.signals.loaded.emit()

    @staticmethod
    def add_dataset(datasets, suppress_signal):
        RunService.__dao.add_runs(datasets)

        if not suppress_signal:
            RunService.__logger.debug("Emitted: added")
            RunService.signals.added.emit()

    @staticmethod
    def update_runs_by_ids(ids, asymmetries):
        RunService.__dao.update_runs_by_id(ids, asymmetries)
        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()

    @staticmethod
    def update_alphas(ids, alphas):
        if len(alphas) == 1:  # When we update alpha from plotting panel we send one alpha for multiple runs
            alpha = alphas[0]
            alphas = [alpha for _ in ids]

        for rid, alpha in zip(ids, alphas):
            run = RunService.__dao.get_runs_by_ids([rid])[0]

            run.asymmetries[domain.RunDataset.FULL_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].correct(alpha)

            if run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()

    @staticmethod
    def changed():
        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()
