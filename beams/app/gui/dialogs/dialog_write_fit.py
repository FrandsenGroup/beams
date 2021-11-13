import os
import zipfile

from PyQt5 import QtCore, QtWidgets

from app.util import qt_widgets
from app.gui.dialogs import dialog_misc
from app.model import objects, services, files


class WriteFitDialog(QtWidgets.QDialog):
    def __init__(self, dataset: objects.FitDataset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dataset = dataset
        self._ignore_radio_button = False

        self.radio_summary = QtWidgets.QRadioButton("Summary")
        self.radio_directory = QtWidgets.QRadioButton("Directory")
        self.radio_zip = QtWidgets.QRadioButton("Zip")
        self.button_save_as = qt_widgets.StyleOneButton("Save As")
        self.button_done = qt_widgets.StyleOneButton("Done")
        self.option_prefix = QtWidgets.QComboBox()
        self.option_order_by = QtWidgets.QComboBox()

        self.summary_button_group = QtWidgets.QButtonGroup()
        self.individual_button_group = QtWidgets.QButtonGroup()

        # TODO perhaps we should add ability to specify bin size and spectrum limits here.

        self._set_attributes()
        self._set_layout()

        self._presenter = WriteFitDialogPresenter(self, dataset)

    def _set_attributes(self):
        magical_list = list(self._dataset.fits.values())[0].meta.keys()

        self.option_prefix.addItems(magical_list)
        self.option_prefix.setEnabled(False)

        possible_values_list = [files.TEMPERATURE_KEY, files.FIELD_KEY, files.RUN_NUMBER_KEY]
        order_by_list = [x for x in possible_values_list if x in magical_list]

        self.option_order_by.addItems(order_by_list)

        self.individual_button_group.addButton(self.radio_zip)
        self.individual_button_group.addButton(self.radio_directory)
        self.summary_button_group.addButton(self.radio_summary)

        self.summary_button_group.setExclusive(False)
        self.individual_button_group.setExclusive(False)

        self.radio_summary.setChecked(True)

        self.radio_zip.toggled.connect(lambda: self._radio_button_clicked(self.radio_zip.text()))
        self.radio_summary.toggled.connect(lambda: self._radio_button_clicked(self.radio_summary.text()))
        self.radio_directory.toggled.connect(lambda: self._radio_button_clicked(self.radio_directory.text()))

    def _set_layout(self):
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.radio_summary)
        vbox.addWidget(self.option_order_by)

        summary_group = QtWidgets.QGroupBox("Summary")
        summary_group.setLayout(vbox)

        vbox = QtWidgets.QVBoxLayout()
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.radio_directory)
        hbox.addWidget(self.radio_zip)
        vbox.addLayout(hbox)
        vbox.addWidget(self.option_prefix)
        individual_group = QtWidgets.QGroupBox("Individual")
        individual_group.setLayout(vbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(summary_group)
        hbox.addWidget(individual_group)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.button_save_as)
        hbox.addWidget(self.button_done)

        main_layout.addLayout(hbox)

        self.setLayout(main_layout)

    def _radio_button_clicked(self, text):
        if self._ignore_radio_button:
            return

        # Otherwise it will try to update.
        self._ignore_radio_button = True

        self.radio_summary.setChecked(self.radio_summary.text() == text)
        self.radio_zip.setChecked(self.radio_zip.text() == text)
        self.radio_directory.setChecked(self.radio_directory.text() == text)

        self._ignore_radio_button = False

        self.option_prefix.setEnabled(self.radio_directory.text() == text or self.radio_zip.text() == text)
        self.option_order_by.setEnabled(self.radio_summary.text() == text)

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    @staticmethod
    def launch(*args, **kwargs):
        dialog = WriteFitDialog(*args, **kwargs)

        return dialog.exec()


class WriteFitDialogPresenter(QtCore.QObject):
    def __init__(self, view: WriteFitDialog, dataset: objects.FitDataset):
        super().__init__()

        self._view = view
        self._dataset = dataset
        self._system_service = services.SystemService()  # For getting/setting last used directory

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.button_save_as.released.connect(self._handle_save_as)
        self._view.button_done.released.connect(lambda: self._view.done(0))

    @QtCore.pyqtSlot()
    def _handle_save_as(self):
        prefix_key = self._view.option_prefix.currentText()
        order_by_key = self._view.option_order_by.currentText()

        if self._view.radio_summary.isChecked():
            save_path = self._get_save_path("Fit (*{})".format(files.Extensions.FIT_SUMMARY_VERBOSE))

            if not save_path:
                return

            try:

                self._dataset.write(save_path, order_by_key)
            except Exception as e:
                dialog_misc.WarningMessageDialog.launch(["Error writing dataset file: " + str(e)])
                return

        elif self._view.radio_directory.isChecked():
            save_directory = self._get_save_directory()

            if not save_directory:
                return

            try:
                for fit in self._dataset.fits.values():
                    full_file_path = os.path.join(save_directory, str(fit.meta[prefix_key]) + files.Extensions.FIT)
                    fit.write(full_file_path)
            except Exception as e:
                dialog_misc.WarningMessageDialog.launch(["Error writing dataset file: " + str(e)])
                return

        else:
            save_path = self._get_save_path("Zip (*.zip)")

            if not save_path:
                return

            for data in self._dataset.fits.values():
                data.write(str(data.meta[prefix_key]) + files.Extensions.FIT)

            fit_files = [str(d.meta[prefix_key]) + files.Extensions.FIT for d in self._dataset.fits.values()]

            try:
                with zipfile.ZipFile(save_path, 'w') as z:
                    for f in fit_files:
                        z.write(f)
            except Exception as e:
                dialog_misc.WarningMessageDialog.launch(["Error writing to zip file: " + str(e)])
                return
            finally:
                [os.remove(f) for f in fit_files]

        self._view.done(0)

    def _get_save_path(self, filter):
        path = QtWidgets.QFileDialog.getSaveFileName(self._view, caption="Save", filter=filter,
                                                     directory=self._system_service.get_last_used_directory())[0]
        if path:
            split_path = os.path.split(path)
            self._system_service.set_last_used_directory(split_path[0])
            return path

    def _get_save_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self._view, caption="Save",
                                                          directory=self._system_service.get_last_used_directory())
        if path and path != '':
            self._system_service.set_last_used_directory(path)
            return path
