
from PyQt5 import QtCore, QtWidgets, QtGui

from app.util import qt_widgets


class WriteFitDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.radio_short = QtWidgets.QRadioButton("Short")
        self.radio_verbose = QtWidgets.QRadioButton("Verbose")
        self.radio_directory = QtWidgets.QRadioButton("Directory")
        self.radio_zip = QtWidgets.QRadioButton("Zip")
        self.button_save_as = qt_widgets.StyleOneButton("Save As")
        self.button_done = qt_widgets.StyleOneButton("Done")
        self.option_prefix = QtWidgets.QComboBox()

        self._set_attributes()
        self._set_layout()

    def _set_attributes(self):
        pass

    def _set_layout(self):
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.radio_short)
        hbox.addWidget(self.radio_verbose)
        summary_group = QtWidgets.QGroupBox("Summary")
        summary_group.setLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.radio_directory)
        hbox.addWidget(self.radio_zip)
        individual_group = QtWidgets.QGroupBox("Individual")
        individual_group.setLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(summary_group)
        hbox.addWidget(individual_group)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.option_prefix)
        prefix_group = QtWidgets.QGroupBox("File Prefix")
        prefix_group.setLayout(prefix_group)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(prefix_group)
        hbox.addWidget(self.button_save_as)
        hbox.addWidget(self.button_done)

        main_layout.addLayout(hbox)

        self.setLayout(main_layout)

    def _radio_button_clicked(self):
        pass

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    @staticmethod
    def launch(self, *args, **kwargs):
        dialog = WriteFitDialog(*args, **kwargs)

        return dialog.exec()


class WriteFitDialogPresenter:
    def __int__(self, view: WriteFitDialog):
        self._view = view

    def _set_callbacks(self):
        pass