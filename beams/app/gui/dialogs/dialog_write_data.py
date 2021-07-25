
import os

from PyQt5 import QtWidgets, QtCore
import numpy as np

from app.util import qt_widgets, qt_constants
from app.model import files, domain, services
from app.gui.dialogs.dialog_misc import WarningMessageDialog


# noinspection PyArgumentList
class WriteDataDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(WriteDataDialog, self).__init__()
        self.setWindowTitle('Write Data')

        self.status_bar = QtWidgets.QStatusBar()
        self.file_list = QtWidgets.QComboBox()
        self.select_folder = qt_widgets.StyleTwoButton('Custom')
        self.skip_file = qt_widgets.StyleOneButton('Skip File')
        self.write_file = qt_widgets.StyleOneButton('Write')
        self.write_all = qt_widgets.StyleOneButton('Write All')
        self.done_button = qt_widgets.StyleOneButton('Done')
        self.input_filename = QtWidgets.QLineEdit()
        self.input_filename.setPlaceholderText('Default is [run number].asy')
        self.label_full = QtWidgets.QLabel('Full Data')
        self.label_binned = QtWidgets.QLabel('Binned Data')
        self.label_binned_size = QtWidgets.QLabel('Bin Size')
        self.label_fft = QtWidgets.QLabel('FFT')
        self.radio_binned = QtWidgets.QRadioButton()
        self.radio_binned_size = QtWidgets.QLineEdit()
        self.radio_full = QtWidgets.QRadioButton()
        self.radio_fft = QtWidgets.QRadioButton()

        self._set_widget_attributes()
        self._set_widget_tooltips()
        self._set_widget_dimensions()
        self._set_widget_layout()

        self.files = args
        self._presenter = WriteDataDialogPresenter(self)
        self.set_status_message('Ready.')

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def enabled_binning(self, binned):
        if binned:
            self.radio_binned_size.setEnabled(True)
            self.enable_writing(False)
        else:
            self.radio_binned_size.setEnabled(False)
            self.enable_writing(True)

    def enable_writing(self, writing):
        self.write_file.setEnabled(writing)
        self.write_all.setEnabled(writing)

    def get_all_files(self):
        return [self.file_list.itemText(i) for i in range(self.file_list.count())]

    def get_file_path(self):
        return self.input_filename.text()

    def get_current_file(self):
        return self.file_list.currentText()

    def set_file_path(self, path):
        self.input_filename.setText(path)

    def remove_current_file(self):
        self.file_list.removeItem(self.file_list.currentIndex())

    def add_files(self, file_paths):
        self.file_list.addItems(file_paths)

    def get_bin_size(self):
        return self.radio_binned_size.text()

    def is_binned(self):
        return self.radio_binned.isChecked()

    def is_full(self):
        return self.radio_full.isChecked()

    def is_fft(self):
        return self.radio_fft.isChecked()

    def _set_widget_attributes(self):
        self.radio_full.setChecked(True)
        self.radio_binned_size.setEnabled(False)

    def _set_widget_tooltips(self):
        pass

    def _set_widget_dimensions(self):
        self.select_folder.setFixedWidth(80)
        self.skip_file.setFixedWidth(80)
        self.write_file.setFixedWidth(80)
        self.write_all.setFixedWidth(80)
        self.done_button.setFixedWidth(80)
        self.radio_binned_size.setFixedWidth(60)

    def _set_widget_layout(self):
        col_one = QtWidgets.QVBoxLayout()
        row_one = QtWidgets.QHBoxLayout()
        row_two = QtWidgets.QHBoxLayout()
        row_thr = QtWidgets.QHBoxLayout()

        col_one.addWidget(self.file_list)

        row_one.addWidget(self.select_folder)
        row_one.addWidget(self.input_filename)
        col_one.addLayout(row_one)

        col_one.addSpacing(15)
        row_two.addStretch()
        row_two.addWidget(self.label_binned)
        row_two.addWidget(self.radio_binned)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_binned_size)
        row_two.addWidget(self.radio_binned_size)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_full)
        row_two.addWidget(self.radio_full)
        row_two.addSpacing(10)
        row_two.addWidget(self.label_fft)
        row_two.addWidget(self.radio_fft)
        row_two.addSpacing(10)
        row_two.setAlignment(qt_constants.AlignLeft)
        row_two.addStretch()
        col_one.addLayout(row_two)
        col_one.addSpacing(15)

        row_thr.addStretch()
        row_thr.addWidget(self.skip_file)
        row_thr.addSpacing(5)
        row_thr.addWidget(self.write_file)
        row_thr.addSpacing(5)
        row_thr.addWidget(self.write_all)
        row_thr.addWidget(self.done_button)
        row_thr.addStretch()
        row_thr.setAlignment(qt_constants.AlignLeft)
        col_one.addLayout(row_thr)

        col_one.addWidget(self.status_bar)

        self.setLayout(col_one)

    @staticmethod
    def launch(*args, **kwargs):
        dialog = WriteDataDialog(*args, **kwargs)
        return dialog.exec()


class WriteDataDialogPresenter:
    def __init__(self, view: WriteDataDialog):
        self._view = view
        self.__service = services.FileService()
        self.__files = self.__service.get_files(self._view.files)

        # fixme, we will want to allow for fits but for now we will just do runs
        unloaded = 0
        files_with_run_datasets = []
        for file in self.__files:
            if file.dataset is None or (isinstance(file.dataset, domain.RunDataset) and file.dataset.asymmetries[domain.RunDataset.FULL_ASYMMETRY] is None):
                WarningMessageDialog.launch(["Some selected runs have not been loaded, or asymmetries have not been plotted."])
                unloaded += 1

            elif isinstance(file.dataset, domain.RunDataset) and file.dataset.asymmetries[domain.RunDataset.FULL_ASYMMETRY] is not None:
                files_with_run_datasets.append(file)

        if len(files_with_run_datasets) + unloaded < len(self.__files):
            WarningMessageDialog.launch(["Some non-asymmetry datasets are selected. These can't be written yet from this view. "])

        self.__files = files_with_run_datasets
        self._view.add_files([f.file_path for f in self.__files])
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.radio_binned.clicked.connect(lambda: self._view.enabled_binning(self._view.is_binned()))
        self._view.radio_full.clicked.connect(lambda: self._view.enabled_binning(self._view.is_binned()))
        self._view.radio_fft.clicked.connect(lambda: self._view.enabled_binning(self._view.is_binned()))
        self._view.radio_binned_size.textChanged.connect(lambda: self._bin_changed())
        self._view.select_folder.released.connect(lambda: self._save_to_clicked())
        self._view.write_file.released.connect(lambda: self._write_clicked())
        self._view.write_all.released.connect(lambda: self._write_all_clicked())
        self._view.done_button.released.connect(lambda: self._done_clicked())
        self._view.skip_file.released.connect(lambda: self._skip_clicked())

    def _write_clicked(self):
        self._view.set_status_message('Writing files ... ')
        current_file = self._view.get_current_file()
        if self._view.is_binned():
            self._write_binned(current_file)
        elif self._view.is_full():
            self._write_full(current_file)
        else:
            self._write_fft(current_file)
        self._view.set_status_message('Done.')

    def _write_all_clicked(self):
        self._view.set_status_message('Writing files ... ')
        for file in self._view.get_all_files():

            if self._view.is_binned():
                self._write_binned(file)
            elif self._view.is_full():
                self._write_full(file)
            else:
                self._write_fft(file)
        self._view.set_status_message('Done.')

    def _save_to_clicked(self):
        # fixme only specifies for .asy files
        # noinspection PyCallByClass,PyArgumentList
        saved_file_path = QtWidgets.QFileDialog.getSaveFileName(self._view, 'Specify file',
                                                                files.load_last_used_directory(), 'ASY(*.asy)')[0]

        if not saved_file_path:
            return
        else:
            path = os.path.split(saved_file_path)
            files.set_last_used_directory(path[0])
            self._view.set_file_path(saved_file_path)

    def _skip_clicked(self):
        current_file = self._view.get_current_file()
        self._view.remove_current_file()

        if len(self._view.get_current_file()) == 0:
            self._view.done(0)
            return

        for file in self.__files:
            if file.file_path == current_file:
                self.__files.remove(file)
                break

    def _done_clicked(self):
        self._view.done(0)

    def _bin_changed(self):
        try:
            float(self._view.get_bin_size())
            self._view.enable_writing(True)
        except ValueError:
            self._view.enable_writing(False)

    def _load_files(self, unread_files):
        for file_path in unread_files:
            reader = files.file(file_path)
            if reader.DATA_FORMAT == files.Format.HISTOGRAM:
                self._context.add_run_from_histogram_file(file_path)
            elif reader.DATA_FORMAT == files.Format.ASYMMETRY:
                self._context.add_run_from_asymmetry_file(file_path)
            else:
                self._files.remove(file_path)

    def _write_binned(self, file_path):
        run = None

        for f in self.__files:
            if f.file_path == file_path:
                run = f.dataset

        if run is None:
            return

        save_path = self._view.get_file_path()
        if len(save_path) == 0:
            if 'RunNumber' in run.meta.keys():
                save_path = os.path.join(os.path.split(file_path)[0], str(run.meta['RunNumber']) + '.asy')
            else:
                save_path = os.path.splitext(file_path)[0] + '.asy'

        bin_size = float(self._view.get_bin_size())
        run.write(save_path, bin_size)

    def _write_full(self, file_path):
        run = None

        for f in self.__files:
            if f.file_path == file_path:
                run = f.dataset

        if run is None:
            return

        save_path = self._view.get_file_path()
        if len(save_path) == 0:
            if 'RunNumber' in run.meta.keys():
                save_path = os.path.join(os.path.split(file_path)[0], str(run.meta['RunNumber']) + '.asy')
            else:
                save_path = os.path.splitext(file_path)[0] + '.asy'

        run.write(save_path)

    def _write_fft(self, run):
        pass
