
import os

from PyQt5 import QtWidgets, QtCore
import numpy as np

from app.util import widgets
from app.model.domain import RunService
from app.model import files
from app.gui.dialogs.dialog_plot_file import PlotFileDialog
from app.gui.dialogs.dialog_misc import PermissionsMessageDialog


# noinspection PyArgumentList
class WriteDataDialog(QtWidgets.QDialog):
    def __init__(self, args):
        super(WriteDataDialog, self).__init__()
        self.setWindowTitle('Specify options for writing data')

        self.status_bar = QtWidgets.QStatusBar()
        self.file_list = QtWidgets.QComboBox()
        self.select_folder = widgets.StyleTwoButton('Custom')
        self.skip_file = widgets.StyleOneButton('Skip File')
        self.write_file = widgets.StyleOneButton('Write')
        self.write_all = widgets.StyleOneButton('Write All')
        self.done_button = widgets.StyleOneButton('Done')
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

        self.files = args[0]
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
        row_two.setAlignment(QtCore.Qt.AlignLeft)
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
        row_thr.setAlignment(QtCore.Qt.AlignLeft)
        col_one.addLayout(row_thr)

        col_one.addWidget(self.status_bar)

        self.setLayout(col_one)

    @staticmethod
    def launch(args=None):
        dialog = WriteDataDialog(args)
        return dialog.exec()


# fixme to remove dependency on context (all I did was switch _context to __service so far) as well as muon file (needs to use new
#  domain objects
class WriteDataDialogPresenter:
    def __init__(self, view: WriteDataDialog):
        self._view = view
        self.__service = RunService()
        self._files = self._view.files
        read_files = []
        unread_files = []
        for file_path in self._files:
            run = self._context.get_run_by_filename(file_path)
            if run:
                read_files.append(file_path)
            else:
                unread_files.append(file_path)

        if unread_files:
            code = PermissionsMessageDialog.launch(["Some files have not yet been loaded. Load them now?"])
            if code == PermissionsMessageDialog.Codes.OKAY:
                PlotFileDialog.launch([unread_files])
            else:
                self._files = read_files

        self._view.add_files(self._files)
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
        run = self._context.get_run_by_filename(self._view.get_current_file())
        if self._view.is_binned():
            self._write_binned(run)
        elif self._view.is_full():
            self._write_full(run)
        else:
            self._write_fft(run)
        self._view.set_status_message('Done.')

    def _write_all_clicked(self):
        self._view.set_status_message('Writing files ... ')
        for file_path in self._view.get_all_files():
            run = self._context.get_run_by_filename(file_path)

            if self._view.is_binned():
                self._write_binned(run)
            elif self._view.is_full():
                self._write_full(run)
            else:
                self._write_fft(run)
        self._view.set_status_message('Done.')

    def _save_to_clicked(self):
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
        self._view.remove_current_file()
        if len(self._view.get_current_file()) == 0:
            self._view.done(0)

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

    def _write_binned(self, run):
        save_path = self._view.get_file_path()

        if len(save_path) == 0:
            if 'RunNumber' in run.meta.keys():
                save_path = os.path.join(os.path.split(run.file)[0], str(run.meta['RunNumber']) + '.asy')
            else:
                save_path = os.path.splitext(run.file)[0] + '.asy'

        bin_size = float(self._view.get_bin_size())
        meta_string = files.TITLE_KEY + ":" + str(run.meta[files.TITLE_KEY]) + "," \
                      + files.BIN_SIZE_KEY + ":" + str(bin_size) + "," \
                      + files.TEMPERATURE_KEY + ":" + str(run.meta[files.TEMPERATURE_KEY]) + "," \
                      + files.FIELD_KEY + ":" + str(run.meta[files.FIELD_KEY]) + "," \
                      + files.T0_KEY + ":" + str(run.t0) + "\n"
        asymmetry = muon.bin_muon_asymmetry(run, bin_size)
        uncertainty = muon.bin_muon_uncertainty(run, bin_size)
        time = muon.bin_muon_time(run, bin_size)
        np.savetxt(save_path, np.c_[time, asymmetry, uncertainty],
                   fmt='%2.9f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "Time, Asymmetry, Uncertainty")

    def _write_full(self, run):
        save_path = self._view.get_file_path()

        if len(save_path) == 0:
            if 'RunNumber' in run.meta.keys():
                save_path = os.path.join(os.path.split(run.file)[0], str(run.meta['RunNumber']) + '.asy')
            else:
                save_path = os.path.splitext(run.file)[0] + '.asy'

        meta_string = files.TITLE_KEY + ":" + str(run.meta[files.TITLE_KEY]) + "," \
                      + files.BIN_SIZE_KEY + ":" + str(run.meta[files.BIN_SIZE_KEY]) + "," \
                      + files.TEMPERATURE_KEY + ":" + str(run.meta[files.TEMPERATURE_KEY]) + "," \
                      + files.FIELD_KEY + ":" + str(run.meta[files.FIELD_KEY]) + "," \
                      + files.T0_KEY + ":" + str(run.t0) + "\n"
        np.savetxt(save_path, np.c_[run.time, run.asymmetry, run.uncertainty],
                   fmt='%2.9f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "Time, Asymmetry, Uncertainty")

    def _write_fft(self, run):
        pass
