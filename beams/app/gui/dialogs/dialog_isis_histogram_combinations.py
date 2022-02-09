
import uuid
from typing import Sequence

from PyQt5 import QtWidgets, QtCore

from app.model import objects
from app.gui.dialogs.dialog_misc import WarningMessageDialog
from app.util import qt_constants


class IsisHistogramCombinationDialog(QtWidgets.QDialog):
    class Codes:
        Done = 0
        Cancel = 1

    def __init__(self, isis_files: Sequence['objects.FileDataset']):
        super().__init__()
        self.__rows = {}  # id : row_number

        self.setMaximumWidth(400)

        self.done_button = QtWidgets.QPushButton('Done')
        self.skip_button = QtWidgets.QPushButton('Don''t Combine')
        self.cancel_button = QtWidgets.QPushButton('Cancel')

        self.combination_table = QtWidgets.QTableWidget()

        num_histograms_ranges = set([f.file.get_number_of_histograms() for f in isis_files])
        if len(num_histograms_ranges) != 1:
            WarningMessageDialog.launch(["Selected files with different ranges of histograms."])
            self.done(self.Codes.Done)

        num_histograms = num_histograms_ranges.pop()

        self.dialog_description = QtWidgets.QLabel("Indicate using the tables below the histograms to combine. "
                                                   "The files you selected each have {} histograms. An example range "
                                                   "would be 1-32 and 33-64 for a file with 64 histograms if you wanted"
                                                   "two resulting histograms. Ranges can also wrap around (i.e. 48-16)."
                                                   .format(num_histograms))

        self.dialog_description.setMaximumWidth(300)
        self.dialog_description.setWordWrap(True)

        self._set_attributes()
        self._set_layout()

        self._presenter = IsisHistogramCombinationDialogPresenter(isis_files, num_histograms, self)

    def _set_attributes(self):
        self.cancel_button.released.connect(lambda: self.done(self.Codes.Cancel))
        self.skip_button.released.connect(lambda: self.done(self.Codes.Done))

        self.combination_table.setColumnCount(4)
        self.combination_table.setHorizontalHeaderLabels(["Start #", "End #", "Title", ""])
        self.combination_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.combination_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.combination_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.combination_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.combination_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)

        self.add_row()

    def add_row(self):
        n = self.combination_table.verticalHeader().count()
        self.combination_table.setRowCount(n + 1)

        row_id = str(uuid.uuid4())
        self.__rows[row_id] = n

        item = QtWidgets.QTableWidgetItem()
        item.setText("")
        self.combination_table.setItem(n, 0, item)

        item = QtWidgets.QTableWidgetItem()
        item.setText("")
        self.combination_table.setItem(n, 1, item)

        item = QtWidgets.QTableWidgetItem()
        item.setText("")
        self.combination_table.setItem(n, 2, item)

        remove_button = QtWidgets.QPushButton("-")
        remove_button.setFixedWidth(30)
        remove_button.released.connect(lambda: self.remove_row(row_id))
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(remove_button)
        layout.setAlignment(qt_constants.AlignCenter)
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(layout)
        self.combination_table.setCellWidget(n, 3, button_widget)

    def get_empty_rows(self):
        num_empty = 0

        for i in range(self.combination_table.verticalHeader().count()):
            if self.combination_table.item(i, 0).text() == "" \
                    and self.combination_table.item(i, 1).text() == "" \
                    and self.combination_table.item(i, 2).text() == "":
                num_empty += 1

        return num_empty

    def remove_row(self, row_id):
        row_to_remove = self.__rows[row_id]
        self.__rows.pop(row_id)

        for rid, row_num in self.__rows.items():
            if row_num > row_to_remove:
                self.__rows[rid] = row_num - 1

        self.combination_table.removeRow(row_to_remove)

    def _set_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.dialog_description)
        layout.addWidget(self.combination_table)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.done_button)
        button_row.addWidget(self.skip_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)

        self.setLayout(layout)

    @staticmethod
    def launch(files):
        dialog = IsisHistogramCombinationDialog(files)
        return dialog.exec()


class IsisHistogramCombinationDialogPresenter(QtCore.QObject):
    def __init__(self, files, num_histograms, view: IsisHistogramCombinationDialog):
        super().__init__()

        self._files = files
        self._num_histograms = num_histograms
        self._view = view

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.combination_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self._view.combination_table.itemChanged.connect(self._on_table_contents_changed)
        self._view.done_button.released.connect(self._on_done_clicked)

    @QtCore.pyqtSlot()
    def _on_table_selection_changed(self):
        num_rows = self._view.combination_table.rowCount()

        # Select outside the table after selecting a cell
        try:
            row = self._view.combination_table.selectedRanges()[0].topRow()
        except IndexError:
            return

        # We only add a new row if they click the last row and there is only one current empty row.
        if row != num_rows - 1 or self._view.get_empty_rows() > 1:
            return

        self._view.add_row()

    @QtCore.pyqtSlot()
    def _on_table_contents_changed(self):
        pass

    @QtCore.pyqtSlot()
    def _on_done_clicked(self):
        num_rows = self._view.combination_table.rowCount()

        histogram_ranges = []
        for i in range(num_rows):
            start_text = self._view.combination_table.item(i, 0).text()
            end_text = self._view.combination_table.item(i, 1).text()
            title = self._view.combination_table.item(i, 2).text()

            # Ignore the final row if it is empty.
            if i == num_rows - 1 and start_text == '' and end_text == '' and title == '':
                continue

            # Ensure start and end are both integers
            try:
                start = int(start_text) - 1
            except ValueError:
                WarningMessageDialog.launch(["Start value ('{}') in row {} is invalid.".format(start_text, i+1)])
                return

            try:
                end = int(end_text)
            except ValueError:
                WarningMessageDialog.launch(["End value ('{}') in row {} is invalid.".format(end_text, i+1)])
                return

            histogram_ranges.append((start, end, title))

        for start, end, title in histogram_ranges:
            if start < 0 or end < 0 or end > self._num_histograms or start > self._num_histograms - 1:
                # We are going to allow overlapping ranges, but start and ends need to make sense.
                WarningMessageDialog.launch(["Histogram range of '{}' to '{}' is invalid.".format(start, end)])
                return

            if title == '':
                WarningMessageDialog.launch(["Please specify a title for every histogram."])
                return

        for f in self._files:
            starts = [r[0] for r in histogram_ranges]
            ends = [r[1] for r in histogram_ranges]
            names = [r[2] for r in histogram_ranges]

            try:
                f.file.set_combine_format(starts, ends, names)
            except:
                WarningMessageDialog.launch(["Invalid set of histogram ranges"])
                return

        self._view.done(self._view.Codes.Done)
