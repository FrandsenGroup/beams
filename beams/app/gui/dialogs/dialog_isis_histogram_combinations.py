
from PyQt5 import QtWidgets, QtCore


class IsisHistogramCombinationDialog(QtWidgets.QDialog):
    def __init__(self, files):
        super().__init__()

        self.okay_button = QtWidgets.QPushButton('Okay')
        self.skip_button = QtWidgets.QPushButton('Don''t Combine')
        self.cancel_button = QtWidgets.QPushButton('Cancel')
        self.combination_table = QtWidgets.QTableWidget()

        self._set_attributes()
        self._set_layout()

        self._presenter = IsisHistogramCombinationDialogPresenter(files)

    def _set_attributes(self):
        pass

    def _set_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.combination_table)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.okay_button)
        button_row.addWidget(self.skip_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)

        self.setLayout(layout)

    @staticmethod
    def launch(files):
        dialog = IsisHistogramCombinationDialog(files)
        return dialog.exec()


class IsisHistogramCombinationDialogPresenter:
    def __init__(self, files):
        self.__files = files
