import enum

from PyQt5 import QtWidgets

from app.model.domain import Asymmetry, RunDataset
from app.util import qt_widgets
from app.model import files
from app.services import run_service
from app.gui.dialogs.dialog_misc import WarningMessageDialog


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
        self.b_apply = qt_widgets.StyleOneButton('Apply')
        self.b_apply_all = qt_widgets.StyleOneButton('Apply All')
        self.b_plot = qt_widgets.StyleOneButton('Plot')
        self.b_skip = qt_widgets.StyleOneButton('Skip')
        self.b_cancel = qt_widgets.StyleTwoButton('Cancel')
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
            self.c_file_list.setCurrentIndex(self.c_file_list.currentIndex() + 1)

    def exec(self):
        if self.c_file_list.count() == 0:
            return self.Codes.FILES_PLOTTED

        return super().exec()

    @staticmethod
    def launch(args=None):
        dialog = PlotFileDialog(args)
        return dialog.exec()


class PlotFileDialogPresenter:
    def __init__(self, view: PlotFileDialog, runs):
        self.__run_service = run_service.RunService()
        self._view = view
        self._runs = runs
        self._formats = {run.file.file_path: None for run in runs}

        current_hists = runs[0].histograms.keys()
        self._view.set_first_histogram(current_hists)
        self._view.set_second_histogram(current_hists)

        self._view.set_files([run.file.file_path for run in runs])
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.b_apply.released.connect(lambda: self._apply_clicked())
        self._view.b_apply_all.released.connect(lambda: self._apply_all_clicked())
        self._view.b_cancel.released.connect(lambda: self._cancel_clicked())
        self._view.b_skip.released.connect(lambda: self._skip_clicked())
        self._view.b_plot.released.connect(lambda: self._plot_clicked())
        self._view.c_file_list.currentIndexChanged.connect(lambda: self._file_choice_changed())

    def _is_all_formatted(self):
        for k, v in self._formats.items():
            if v is None:
                return False
        return True

    def _apply_clicked(self):
        current_format = self._current_format()

        if not current_format[3]:
            WarningMessageDialog.launch(["Cannot calculate asymmetry from the same histograms."])
            self._view.set_enabled_plot_button(False)
            self._view.set_status_message("Cannot use the same histograms.")
            return

        self._formats[current_format[0]] = current_format[1:3]

        if self._is_all_formatted():
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

        first_histogram = current_format[1]
        second_histogram = current_format[2]

        for run in self._runs:
            if first_histogram in run.histograms.keys() and second_histogram in run.histograms.keys():
                self._formats[run.file.file_path] = current_format[1:3]

        if self._is_all_formatted():
            self._view.set_enabled_plot_button(True)

        self._view.set_status_message("Applied.")

    def _cancel_clicked(self):
        self._view.done(PlotFileDialog.Codes.NO_FILES_PLOTTED)

    def _skip_clicked(self):
        current_file = self._view.get_file()

        for run in self._runs:
            if run.file.file_path == current_file:
                self._runs.remove(run)

        self._formats.pop(current_file)
        self._view.remove_current_file()

        if self._is_all_formatted():
            self._view.set_enabled_plot_button(True)

    def _plot_clicked(self):
        if self._is_all_formatted():
            self._load_runs()
        else:
            self._view.set_enabled_plot_button(False)

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

        for run in self._runs:
            format = self._formats[run.file.file_path]
            run.asymmetries[RunDataset.FULL_ASYMMETRY] = Asymmetry(histogram_one=run.histograms[format[0]],
                                                                   histogram_two=run.histograms[format[1]])
            run.histograms_used = format  # We need this for when we have to recalculate the asymmetry from hist panel

        self.__run_service.changed()

    def _current_format(self):
        current_file = self._view.get_file()
        current_first_histogram = self._view.get_first_histogram()
        current_second_histogram = self._view.get_second_histogram()

        return [current_file, current_first_histogram, current_second_histogram,
                current_first_histogram != current_second_histogram]
