import os
import zipfile

from PyQt5 import QtCore, QtWidgets

from app.util import qt_widgets
from app.gui.dialogs import dialog_misc
from app.model import domain, services


class WriteFitDialog(QtWidgets.QDialog):
    def __init__(self, dataset: domain.FitDataset, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.radio_short = QtWidgets.QRadioButton("Short")
        self.radio_verbose = QtWidgets.QRadioButton("Verbose")
        self.radio_directory = QtWidgets.QRadioButton("Directory")
        self.radio_zip = QtWidgets.QRadioButton("Zip")
        self.button_save_as = qt_widgets.StyleOneButton("Save As")
        self.button_done = qt_widgets.StyleOneButton("Done")
        self.option_prefix = QtWidgets.QComboBox()

        # TODO perhaps we should add ability to specify bin size and spectrum limits here.

        self._set_attributes()
        self._set_layout()

        self._datasets = dataset
        self._presenter = WriteFitDialogPresenter(self, dataset)

    def _set_attributes(self):
        self.option_prefix.addItems(list(self._dataset.fits.values())[0].meta.keys())

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
    def launch(*args, **kwargs):
        dialog = WriteFitDialog(*args, **kwargs)

        return dialog.exec()


class WriteFitDialogPresenter(QtCore.QObject):
    def __init__(self, view: WriteFitDialog, dataset: domain.FitDataset):
        super().__init__()

        self._view = view
        self._dataset = dataset
        self._system_service = services.SystemService()

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.button_save_as.released.connect(self._handle_save_as)
        self._view.button_done.released.connect(self._view.done(0))

    @QtCore.pyqtSlot()
    def _handle_save_as(self):
        prefix_key = self._view.option_prefix.currentText()

        if self._view.radio_short.isChecked():
            save_path = self._get_save_path("Fit (*.ft3)")

            if not save_path:
                return

            self._dataset.write(save_path)

        elif self._view.radio_verbose.isChecked():
            save_path = self._get_save_path("Fit (*.ft2)")

            if not save_path:
                return

            self._dataset.write(save_path, verbose_format=True)

        elif self._view.radio_directory.isChecked():
            save_directory = self._get_save_directory()

            if not save_directory:
                return

            for fit in self._dataset.fits.values():
                full_file_path = os.path.join(save_directory, str(fit.meta[prefix_key]) + ".ft1")
                fit.write(full_file_path)

        else:  # Zip
            save_path = self._get_save_path("Zip (*.zip)")

            if not save_path:
                return

            # TODO Make our file extensions constants in the files module.

            for data in self._dataset.fits.values():
                data.write(str(data.meta[prefix_key]) + ".ft1")

            fit_files = [str(d.meta[prefix_key]) + ".ft1" for d in self._dataset.fits.values()]

            try:
                with zipfile.ZipFile(save_path) as z:
                    for f in fit_files:
                        z.write(f)
            except Exception as e:
                dialog_misc.WarningMessageDialog.launch(["Error writing to zip file: " + str(e)])
                return
            finally:
                [os.remove(f) for f in fit_files]

    def _get_save_path(self, filter):
        path = QtWidgets.QFileDialog.getSaveFileName(self._view, caption="Save", filter=filter,
                                                     directory=self._system_service.get_last_used_directory())[0]
        if path:
            split_path = os.path.split(path)
            self.__system_service.set_last_used_directory(split_path[0])
            return path

    def _get_save_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self._view, caption="Save",
                                                          directory=self._system_service.get_last_used_directory())[0]
        if path:
            self._system_service.set_last_used_directory(path)
            return path
