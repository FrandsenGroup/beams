
import os

from PyQt5 import QtCore

import app.model.data_access as dao
from app.model import files, domain
from app.services import run_service, fit_service


class Signals(QtCore.QObject):
    changed = QtCore.pyqtSignal()


class FileService:
    __dao = dao.FileDAO()
    __run_service = run_service.RunService()
    __fit_service = fit_service.FitService()
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
        FileService.signals.changed.emit()
