
import enum

from PyQt5 import QtWidgets

from util import widgets


# noinspection PyArgumentList
class PlotFileDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        FILES_PLOTTED = 1
        NO_FILES_PLOTTED = 2

    def __init__(self):
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
        self._presenter = PlotFileDialogPresenter()

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    @staticmethod
    def launch():
        dialog = PlotFileDialog()
        return dialog.exec()


class PlotFileDialogPresenter:
    def __init__(self):
        pass
