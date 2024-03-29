import os
import zipfile

from PyQt5 import QtCore, QtWidgets

from app.util import qt_widgets, report
from app.gui.dialogs import dialog_misc
from app.model import objects, services, files


class WriteFitDialog(QtWidgets.QDialog):
    def __init__(self, dataset: objects.FitDataset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dataset = dataset
        self._ignore_radio_button = False

        self.radio_summary = QtWidgets.QRadioButton("Summary")
        self.radio_parameter = QtWidgets.QRadioButton("Single Parameter")
        self.radio_directory = QtWidgets.QRadioButton("Directory")
        self.radio_zip = QtWidgets.QRadioButton("Zip")
        self.button_save_as = qt_widgets.StyleOneButton("Save")
        self.button_done = qt_widgets.StyleOneButton("Cancel")
        self.option_prefix = QtWidgets.QComboBox()
        self.option_order_by = QtWidgets.QComboBox()
        self.option_ind_var = QtWidgets.QComboBox()
        self.option_parameter = QtWidgets.QComboBox()

        self.single_file_button_group = QtWidgets.QButtonGroup()
        self.individual_button_group = QtWidgets.QButtonGroup()

        # TODO we should add ability to specify bin size and spectrum limits here.

        self._set_attributes()
        self._set_layout()

        self._presenter = WriteFitDialogPresenter(self, dataset)

    def _set_attributes(self):
        metas = [f.meta for f in self._dataset.fits.values()]

        meta_keys = metas[0].keys()
        possible_order_by_list = [files.TEMPERATURE_KEY, files.FIELD_KEY, files.RUN_NUMBER_KEY]
        order_by_list = [x for x in possible_order_by_list if x in meta_keys]

        self.option_order_by.addItems(order_by_list)

        # populate independent variable combo
        ind_var_list = order_by_list
        self.option_ind_var.addItems(ind_var_list)

        # populate parameter combo
        parameter_set = {parameter for fit in self._dataset.fits.values() for parameter in fit.parameters.keys()}
        self.option_parameter.addItems(parameter_set)

        self.option_ind_var.setEnabled(False)
        self.option_parameter.setEnabled(False)

        # We only want to use keys as filenames if there is a unique value for reach run
        meta_keys = [k for k in meta_keys if len({str(m[k]) for m in metas}) == len(metas)]

        self.option_prefix.addItems(meta_keys)
        self.option_prefix.setEnabled(False)

        self.individual_button_group.addButton(self.radio_zip)
        self.individual_button_group.addButton(self.radio_directory)
        self.single_file_button_group.addButton(self.radio_summary)
        self.single_file_button_group.addButton(self.radio_parameter)

        self.single_file_button_group.setExclusive(False)
        self.individual_button_group.setExclusive(False)

        self.radio_summary.setChecked(True)

        self.radio_zip.toggled.connect(lambda: self._radio_button_clicked(self.radio_zip.text()))
        self.radio_summary.toggled.connect(lambda: self._radio_button_clicked(self.radio_summary.text()))
        self.radio_parameter.toggled.connect(lambda: self._radio_button_clicked(self.radio_parameter.text()))
        self.radio_directory.toggled.connect(lambda: self._radio_button_clicked(self.radio_directory.text()))

    def _set_layout(self):
        summary_vbox = QtWidgets.QVBoxLayout()
        summary_vbox.addWidget(self.radio_summary)
        # order_hbox = QtWidgets.QHBoxLayout()
        summary_vbox.addWidget(QtWidgets.QLabel("Order runs by:"))
        # order_hbox.addStretch()
        # summary_vbox.addLayout(order_hbox)
        summary_vbox.addWidget(self.option_order_by)
        summary_vbox.addStretch()

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        parameter_vbox = QtWidgets.QVBoxLayout()
        parameter_vbox.addWidget(self.radio_parameter)
        parameter_vbox.addWidget(QtWidgets.QLabel("Independent variable:"))
        parameter_vbox.addWidget(self.option_ind_var)
        parameter_vbox.addWidget(QtWidgets.QLabel("Parameter:"))
        parameter_vbox.addWidget(self.option_parameter)

        single_file_hbox = QtWidgets.QHBoxLayout()
        single_file_hbox.addLayout(summary_vbox)
        single_file_hbox.addWidget(line)
        single_file_hbox.addLayout(parameter_vbox)

        single_file_group = QtWidgets.QGroupBox("Fitting Parameters")
        single_file_group.setLayout(single_file_hbox)

        vbox = QtWidgets.QVBoxLayout()
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.radio_directory)
        hbox.addWidget(self.radio_zip)
        vbox.addLayout(hbox)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel("Name files by:"))
        hbox.addStretch()
        vbox.addLayout(hbox)
        vbox.addWidget(self.option_prefix)
        vbox.addStretch()
        individual_group = QtWidgets.QGroupBox("Calculated Asymmetries")
        individual_group.setLayout(vbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(single_file_group)
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
        self.radio_parameter.setChecked(self.radio_parameter.text() == text)
        self.radio_zip.setChecked(self.radio_zip.text() == text)
        self.radio_directory.setChecked(self.radio_directory.text() == text)

        self._ignore_radio_button = False

        self.option_prefix.setEnabled(self.radio_directory.text() == text or self.radio_zip.text() == text)
        self.option_order_by.setEnabled(self.radio_summary.text() == text)
        self.option_ind_var.setEnabled(self.radio_parameter.text() == text)
        self.option_parameter.setEnabled(self.radio_parameter.text() == text)

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
        self._view.button_save_as.released.connect(self._on_save_as_clicked)
        self._view.button_done.released.connect(self._on_done_clicked)

    @QtCore.pyqtSlot()
    def _on_done_clicked(self):
        self._view.done(0)

    @QtCore.pyqtSlot()
    def _on_save_as_clicked(self):
        prefix_key = self._view.option_prefix.currentText()
        order_by_key = self._view.option_order_by.currentText()
        ind_var_key = self._view.option_ind_var.currentText()
        parameter_key = self._view.option_parameter.currentText()

        if self._view.radio_summary.isChecked():
            save_path = self._get_save_path("Fit (*{})".format(files.Extensions.FIT_SUMMARY_VERBOSE))

            if not save_path:
                return

            try:
                self._dataset.write(save_path, order_by_key)
            except Exception as e:
                report.report_exception(e)
                dialog_misc.WarningMessageDialog.launch(["Error writing dataset file: " + str(e)])
                return
        elif self._view.radio_parameter.isChecked():
            save_path = self._get_save_path("prm (*{})".format(files.Extensions.PARAMETER))
            if not save_path:
                return

            try:
                self._dataset.write(save_path, ind_var_key, parameter_key)
            except Exception as e:
                report.report_exception(e)
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
                report.report_exception(e)
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
                report.report_exception(e)
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
