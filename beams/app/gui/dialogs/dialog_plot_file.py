import enum

from PyQt5 import QtWidgets, QtCore

from app.util import qt_widgets
from app.model import files, services, objects
from app.gui.dialogs.dialog_misc import WarningMessageDialog


# noinspection PyArgumentList
class PlotFileDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        FILES_PLOTTED = 1
        NO_FILES_PLOTTED = 2

    def __init__(self, args=None):
        super(PlotFileDialog, self).__init__()

        self.t_tip = QtWidgets.QLabel('Specify the two histograms you want to use calculate the asymmetry.')
        self.c_title_list = QtWidgets.QComboBox()
        self.c_hist_one = QtWidgets.QComboBox()
        self.c_hist_two = QtWidgets.QComboBox()
        self.b_apply = qt_widgets.StyleOneButton('Apply')
        self.b_apply_all = qt_widgets.StyleOneButton('Apply All')
        self.b_plot = qt_widgets.StyleOneButton('Plot')
        self.b_cancel = qt_widgets.StyleTwoButton('Cancel')
        self.status_bar = QtWidgets.QStatusBar()

        self.c_title_list.setToolTip("List of runs selected to plot.")
        self.c_hist_one.setToolTip("The first histogram to be included in asymmetry.")
        self.c_hist_two.setToolTip("The second histogram to be included in asymmetry.")
        self.b_apply.setToolTip("Apply this format to only the current run.")
        self.b_apply_all.setToolTip("Apply this format to all selected runs.")
        self.b_plot.setToolTip("Plot the asymmetries (must choose histograms before plotting).")
        self.b_cancel.setToolTip("Close prompt.")

        self.b_plot.setEnabled(False)

        col = QtWidgets.QVBoxLayout()
        row_1 = QtWidgets.QHBoxLayout()
        row_2 = QtWidgets.QHBoxLayout()

        col.addWidget(self.t_tip)
        col.addWidget(self.c_title_list)
        row_1.addWidget(self.c_hist_one)
        row_1.addWidget(self.c_hist_two)
        row_2.addWidget(self.b_apply)
        row_2.addWidget(self.b_apply_all)
        row_2.addWidget(self.b_plot)
        row_2.addWidget(self.b_cancel)
        col.addLayout(row_1)
        col.addLayout(row_2)
        col.addWidget(self.status_bar)


        self.setLayout(col)
        self._presenter = PlotFileDialogPresenter(self, args[0])

    def get_title(self):
        return self.c_title_list.currentText()

    def set_title(self, title):
        self.c_title_list.setCurrentText(title)

    def set_titles(self, titles):
        self.c_title_list.clear()
        self.c_title_list.addItems(titles)

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

    def increment_current_title(self):
        if self.c_title_list.currentIndex() < self.c_title_list.count() - 1:
            self.c_title_list.setCurrentIndex(self.c_title_list.currentIndex() + 1)
        else:
            self.c_title_list.setCurrentIndex(0)

    def exec(self):
        if self.c_title_list.count() == 0:
            return self.Codes.FILES_PLOTTED

        return super().exec()

    @staticmethod
    def launch(args=None):
        dialog = PlotFileDialog(args)
        return dialog.exec()


class PlotFileDialogPresenter(QtCore.QObject):
    def __init__(self, view: PlotFileDialog, runs):
        super().__init__()

        self.__run_service = services.RunService()
        self._view = view
        self._runs = runs
        self._formats = {run.meta['Title']: None for run in runs}

        current_hists = runs[0].histograms.keys()
        self._view.set_first_histogram(current_hists)
        self._view.set_second_histogram(current_hists)

        self._view.set_titles([run.meta['Title'] for run in runs])
        self._set_callbacks()

    def _set_callbacks(self):
        self._view.b_apply.released.connect(self._on_apply_clicked)
        self._view.b_apply_all.released.connect(self._on_apply_all_clicked)
        self._view.b_cancel.released.connect(self._on_cancel_clicked)
        self._view.b_plot.released.connect(self._on_plot_clicked)
        self._view.c_title_list.currentIndexChanged.connect(self._on_title_choice_changed)

    @QtCore.pyqtSlot()
    def _on_apply_clicked(self):
        current_format = self._current_format()

        if not current_format[3]:
            WarningMessageDialog.launch(["Cannot calculate asymmetry from the same histograms."])
            self._view.set_enabled_plot_button(False)
            self._view.set_status_message("Cannot use the same histograms.")
            return

        self._formats[current_format[0]] = current_format[1:3]

        if self._is_all_formatted():
            self._view.set_enabled_plot_button(True)

        self._view.increment_current_title()
        self._view.set_status_message("Applied.")

    @QtCore.pyqtSlot()
    def _on_apply_all_clicked(self):
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
                self._formats[run.meta['Title']] = current_format[1:3]

        if self._is_all_formatted():
            self._view.set_enabled_plot_button(True)

        self._view.set_status_message("Applied.")

    @QtCore.pyqtSlot()
    def _on_cancel_clicked(self):
        self._view.done(PlotFileDialog.Codes.NO_FILES_PLOTTED)

    @QtCore.pyqtSlot()
    def _on_plot_clicked(self):
        if self._is_all_formatted():
            self._load_runs()
        else:
            self._view.set_enabled_plot_button(False)

    @QtCore.pyqtSlot()
    def _on_title_choice_changed(self):
        current_title = self._view.get_title()
        current_run = self._runs[0]

        for run in self._runs:
            if run.meta[files.TITLE_KEY] == current_title:
                current_run = run
                break

        current_hists = current_run.histograms
        self._view.set_first_histogram(current_hists)
        self._view.set_second_histogram(current_hists)

    def _is_all_formatted(self):
        for k, v in self._formats.items():
            if v is None:
                return False
        return True

    def _load_runs(self):
        self._view.done(PlotFileDialog.Codes.FILES_PLOTTED)

        for run in self._runs:
            format = self._formats[run.meta['Title']]
            run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] = objects.Asymmetry(histogram_one=run.histograms[format[0]],
                                                                                   histogram_two=run.histograms[format[1]])
            run.histograms_used = format  # We need this for when we have to recalculate the asymmetry from hist panel

        self.__run_service.changed()

    def _current_format(self):
        current_title = self._view.get_title()
        current_first_histogram = self._view.get_first_histogram()
        current_second_histogram = self._view.get_second_histogram()

        return [current_title, current_first_histogram, current_second_histogram,
                current_first_histogram != current_second_histogram]
