
import os
import logging

from PyQt5 import QtCore

import app.model.data_access as dao
from app.model import domain, files


class FitService:
    class Signals(QtCore.QObject):
        added = QtCore.pyqtSignal()
        changed = QtCore.pyqtSignal()

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


class RunService:
    class Signals(QtCore.QObject):
        added = QtCore.pyqtSignal()
        changed = QtCore.pyqtSignal()
        loaded = QtCore.pyqtSignal()

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


class FileService:
    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    __dao = dao.FileDAO()
    __logger = logging.getLogger("FileService")
    __run_service = RunService()
    __fit_service = FitService()
    signals = Signals()

    @staticmethod
    def get_files(ids=None):
        if ids is not None:
            return FileService.__dao.get_files_by_ids(ids)
        else:
            return FileService.__dao.get_files()

    @staticmethod
    def convert_files(ids):
        new_paths = []
        datasets = FileService.__dao.get_files_by_ids(ids)
        for dataset in datasets:
            if dataset.file.DATA_FORMAT == files.Format.BINARY:
                temp = os.path.splitext(dataset.file.file_path)[0]
                outfile = temp + ".dat"
                outfile_reader = dataset.file.convert(outfile)
                new_paths.append(outfile_reader.file_path)
                FileService.__dao.remove_files_by_id(dataset.id)

        FileService.add_files(new_paths)

    @staticmethod
    def add_files(paths):
        if len(paths) == 0:
            return

        for path in paths:
            if FileService.__dao.get_files_by_path(path) is not None:
                continue

            f = files.file(path)
            data_set = domain.DataBuilder.build_minimal(f)
            file_set = domain.FileDataset(f)

            if data_set is not None:
                file_set.dataset = data_set
                file_set.title = data_set.meta[files.TITLE_KEY]

                if isinstance(data_set, domain.RunDataset):
                    FileService.__run_service.add_dataset([data_set], suppress_signal=True)
                else:
                    FileService.__fit_service.add_dataset([data_set], suppress_signal=True)

            FileService.__dao.add_files([file_set])

        FileService.__logger.debug("Emitted: changed")
        FileService.signals.changed.emit()

    @staticmethod
    def load_files(ids):
        is_changed = False

        for file_dataset in FileService.__dao.get_files_by_ids(ids):
            if not file_dataset.isLoaded:
                is_changed = True
                domain.DataBuilder.build_full(file_dataset.file, file_dataset.dataset)
                file_dataset.isLoaded = True

        if is_changed:
            FileService.__logger.debug("Emitted: changed")
            FileService.signals.changed.emit()
            FileService.__run_service.changed()
            FileService.__fit_service.changed()

    @staticmethod
    def remove_files(checked_items):
        run_files = FileService.__dao.get_files_by_ids(checked_items)
        run_ids = []
        for rf in run_files:
            if rf.isLoaded:
                run_ids.append(rf.dataset.id)
            FileService.__dao.remove_files_by_id(rf.id)

        FileService.__run_service.remove_runs_by_ids(run_ids)
        FileService.__logger.debug("Emitted: changed")
        FileService.signals.changed.emit()


class StyleService:
    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    __dao = dao.StyleDAO()


class SystemService:
    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    __dao = dao.SystemDAO()
