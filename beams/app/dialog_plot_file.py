
import enum

from PyQt5 import QtWidgets

from util import widgets, files
from app.model import MuonDataContext
from app.dialog_misc import WarningMessageDialog


# noinspection PyArgumentList
class PlotFileDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        FILES_PLOTTED = 1
        NO_FILES_PLOTTED = 2

    def __init__(self, args=None):
        super(PlotFileDialog, self).__init__()

        self.t_tip = QtWidgets.QLabel('Specify the two histograms you want to use calculate the asymmetry.')
        self.c_file_list = QtWidgets.QComboBox()
        self.c_hist_one = QtWidgets.QComboBox()
        self.c_hist_two = QtWidgets.QComboBox()
        self.b_apply = widgets.StyleOneButton('Apply')
        self.b_apply_all = widgets.StyleOneButton('Apply All')
        self.b_plot = widgets.StyleOneButton('Plot')
        self.b_skip = widgets.StyleOneButton('Skip')
        self.b_cancel = widgets.StyleTwoButton('Cancel')
        self.status_bar = QtWidgets.QStatusBar()

        self.b_plot.setEnabled(False)

        col = QtWidgets.QVBoxLayout()
        row_1 = QtWidgets.QHBoxLayout()
        row_2 = QtWidgets.QHBoxLayout()

        col.addWidget(self.t_tip)
        col.addWidget(self.c_file_list)
        row_1.addWidget(self.c_hist_one)
        row_1.addWidget(self.c_hist_two)
        row_2.addWidget(self.b_apply)
        row_2.addWidget(self.b_apply_all)
        row_2.addWidget(self.b_skip)
        row_2.addWidget(self.b_plot)
        row_2.addWidget(self.b_cancel)
        col.addLayout(row_1)
        col.addLayout(row_2)
        col.addWidget(self.status_bar)

        self.setLayout(col)
        self._presenter = PlotFileDialogPresenter(self, args[0])

    def get_file(self):
        return self.c_file_list.currentText()

    def set_file(self, path):
        self.c_file_list.setCurrentText(path)

    def set_files(self, paths):
        self.c_file_list.clear()
        self.c_file_list.addItems(paths)

    def set_first_histogram(self, hists):
        self.c_hist_one.clear()
        self.c_hist_one.addItems(hists)

    def set_second_histogram(self, hists):
        self.c_hist_two.clear()
        self.c_hist_two.addItems(hists)

    def get_first_histogram(self):
        return self.c_hist_one.currentText()

    def get_second_histogram(self):
        return self.c_hist_two.currentText()

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def set_enabled_plot_button(self, enabled):
        self.b_plot.setEnabled(enabled)

    def remove_current_file(self):
        self.c_file_list.removeItem(self.c_file_list.currentIndex())

    def increment_current_file(self):
        if self.c_file_list.currentIndex() < self.c_file_list.count() - 1:
            self.c_file_list.setCurrentIndex(self.c_file_list.currentIndex()+1)

    def exec(self):
        if self.c_file_list.count() == 0:
            return self.Codes.FILES_PLOTTED

        return super().exec()

    @staticmethod
    def launch(args=None):
        dialog = PlotFileDialog(args)
        return dialog.exec()


class PlotFileDialogPresenter:
    def __init__(self, view: PlotFileDialog, file_paths):
        self._view = view
        self._files = file_paths
        self._model = PlotFileDialogModel(self._files)

        histogram_files = self._model.histogram_files
        if not histogram_files:
            self._load_runs()
        else:
            current_hists = files.file(histogram_files[0]).read_meta()[files.HIST_TITLES_KEY]
            self._view.set_first_histogram(current_hists)
            self._view.set_second_histogram(current_hists)

        self._view.set_files(histogram_files)
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.b_apply.released.connect(lambda: self._apply_clicked())
        self._view.b_apply_all.released.connect(lambda: self._apply_all_clicked())
        self._view.b_cancel.released.connect(lambda: self._cancel_clicked())
        self._view.b_skip.released.connect(lambda: self._skip_clicked())
        self._view.b_plot.released.connect(lambda: self._plot_clicked())
        self._view.c_file_list.currentIndexChanged.connect(lambda: self._file_choice_changed())

    def _apply_clicked(self):
        current_format = self._current_format()

        if not current_format[3]:
            WarningMessageDialog.launch(["Cannot calculate asymmetry from the same histograms."])
            self._view.set_enabled_plot_button(False)
            self._view.set_status_message("Cannot use the same histograms.")
            return

        self._model.set_format(current_format)

        if self._model.is_all_formatted():
            self._view.set_enabled_plot_button(True)

        self._view.increment_current_file()
        self._view.set_status_message("Applied.")

    def _apply_all_clicked(self):
        current_format = self._current_format()

        if not current_format[3]:
            WarningMessageDialog.launch(["Cannot calculate asymmetry from the same histograms."])
            self._view.set_enabled_plot_button(False)
            self._view.set_status_message("Cannot use the same histograms.")
            return

        for file_path in self._model.histogram_files:
            current_format[0] = file_path
            self._model.set_format(current_format)

        if self._model.is_all_formatted():
            self._view.set_enabled_plot_button(True)

        self._view.set_status_message("Applied.")

    def _cancel_clicked(self):
        self._view.done(PlotFileDialog.Codes.NO_FILES_PLOTTED)

    def _skip_clicked(self):
        current_file = self._view.get_file()

        self._files.remove(current_file)
        self._model.remove_file(current_file)
        self._view.remove_current_file()

        if self._model.is_all_formatted():
            self._view.set_enabled_plot_button(True)

    def _plot_clicked(self):
        if self._model.is_all_formatted():
            self._load_runs()

    def _file_choice_changed(self):
        current_file = self._view.get_file()
        if len(current_file) < 2:
            self._view.done(PlotFileDialog.Codes.NO_FILES_PLOTTED)
            return

        current_hists = files.file(current_file).read_meta()[files.HIST_TITLES_KEY]
        self._view.set_first_histogram(current_hists)
        self._view.set_second_histogram(current_hists)

    def _load_runs(self):
        self._view.done(PlotFileDialog.Codes.FILES_PLOTTED)
        self._model.load_runs()

    def _current_format(self):
        current_file = self._view.get_file()
        current_first_histogram = self._view.get_first_histogram()
        current_second_histogram = self._view.get_second_histogram()

        return [current_file, current_first_histogram, current_second_histogram,
                      current_first_histogram != current_second_histogram]


class PlotFileDialogModel:
    def __init__(self, file_paths):
        self._formats = {}
        self._context = MuonDataContext()

        self._files = file_paths
        self.histogram_files = []
        self.asymmetry_files = []

        self._sort_files()

        for path in self.histogram_files:
            reader = files.file(path)
            self._formats[path] = reader.read_meta()

    def _sort_files(self):
        for file_path in self._files:
            file_reader = files.file(file_path)
            if file_reader.DATA_FORMAT == files.Format.HISTOGRAM:
                self.histogram_files.append(file_path)
            else:
                self.asymmetry_files.append(file_path)

    def set_format(self, current_format):
        hists = self._formats[current_format[0]][files.HIST_TITLES_KEY]
        if current_format[1] not in hists or current_format[2] not in hists:
            return False

        self._formats[current_format[0]][files.CALC_HISTS_KEY] = current_format[1:3]
        return True

    def is_all_formatted(self):
        for file, meta in self._formats.items():
            try:
                if not meta[files.CALC_HISTS_KEY]:
                    return False
            except KeyError:
                return False
        return True

    def remove_file(self, file_path):
        self._formats.pop(file_path)
        self.histogram_files.remove(file_path)

    def load_runs(self):
        if not self.asymmetry_files and not self.histogram_files:
            return

        for file_path in self.histogram_files:
            self._context.add_run_from_histogram_file(file_path,
                                                      meta=self._formats[file_path], stop_signal=True)

        for file_path in self.asymmetry_files:
            self._context.add_run_from_asymmetry_file(file_path, stop_signal=True)

        self._context.send_signal()


