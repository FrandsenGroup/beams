
import enum
import json
import os
import shutil
import time
import zipfile
from datetime import datetime
import webbrowser

import requests
from PyQt5 import QtWidgets, QtCore

from app.model import services
from app.util import qt_widgets, qt_constants, report


# noinspection PyArgumentList
class ISISDownloadDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        NEW_FILES = 1
        NO_NEW_FILES = 2

    def __init__(self, args=None):
        super(ISISDownloadDialog, self).__init__()

        self.status_bar = QtWidgets.QStatusBar()
        self.input_area = QtWidgets.QComboBox()
        self.input_year = QtWidgets.QComboBox()
        self.input_runs = QtWidgets.QLineEdit()
        self.input_file = QtWidgets.QLineEdit()
        self.input_expt = QtWidgets.QLineEdit()
        self.input_start_date = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.input_end_date = QtWidgets.QDateTimeEdit(calendarPopup=True)
        self.output_list = qt_widgets.ListWidget()
        self.output_web = QtWidgets.QPlainTextEdit()
        self.title_search = QtWidgets.QLineEdit()
        self.download_selected = qt_widgets.StyleOneButton('Download Selected')
        self.download_all = qt_widgets.StyleOneButton('Download All')
        self.select_button = qt_widgets.StyleTwoButton('Save to')
        self.search_button = qt_widgets.StyleOneButton('Search')
        self.done_button = qt_widgets.StyleOneButton('Done')
        self._label_description = QtWidgets.QLabel('Provide the information below to search and download runs from '
                                                   'musr.ca.\n')

        self._set_widget_dimensions()
        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = ISISDownloadDialogPresenter(self)

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def _set_widget_dimensions(self):
        self.input_area.setFixedWidth(90)
        self.input_expt.setFixedWidth(70)
        self.input_year.setFixedWidth(90)
        self.select_button.setFixedWidth(80)
        self.download_all.setFixedWidth(140)
        self.download_selected.setFixedWidth(140)
        self.done_button.setFixedWidth(80)
        self.search_button.setFixedWidth(80)
        self.output_web.setFixedHeight(100)
        self.setFixedWidth(600)

    def _set_widget_attributes(self):
        self.input_area.setToolTip("Area of facility where experiment was conducted")
        self.input_year.setToolTip("Year the experiment was conducted")
        self.input_runs.setToolTip("Range of run numbers to search for (i.e. 65333 or 65333-65336)")
        self.input_file.setToolTip("Directory the runs will be downloaded to")
        self.input_expt.setToolTip("Experiment number")
        self.input_start_date.setToolTip("Date to start search at")
        self.input_end_date.setToolTip("Date to end search at")
        self.output_list.setToolTip("Results of search will be shown here")
        self.output_web.setToolTip("Request updates will be shown here")
        self.title_search.setToolTip("Title of run (can be a partial title)")
        self.download_selected.setToolTip("Download only the checked runs")
        self.download_all.setToolTip("Download all runs in search result")
        self.select_button.setToolTip("Select directory to download runs to")
        self.search_button.setToolTip("Search for runs based on provided criteria")
        self.done_button.setToolTip("Close prompt")

        self.input_year.addItems(list([str(year) for year in range(datetime.today().year, 1977, -1)]))
        self.input_area.addItems(['M20', 'M20C', 'M20D', 'M15', 'M13', 'M9', 'BNMR', 'BNQR', 'ISAC'])
        self.input_start_date.setDisplayFormat('yyyy-mm-dd')
        self.input_end_date.setDisplayFormat('yyyy-MM-dd')
        self.input_start_date.clear()
        self.input_end_date.setDate(QtCore.QDate.currentDate())

        self.input_runs.setPlaceholderText('Range of Runs (N-N)')
        self.input_file.setPlaceholderText('Save Directory (default is current)')
        self.input_expt.setPlaceholderText('Expt #')
        self.title_search.setPlaceholderText('Run Title (for searching)')

        self.output_web.setEnabled(True)
        self.download_all.setEnabled(False)
        self.download_selected.setEnabled(False)
        self.output_web.appendPlainText('No queries or downloads attempted.\n')

        self.set_status_message('Ready.')

    def _set_widget_layout(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._label_description)
        main_layout.addSpacing(5)

        row_1 = QtWidgets.QHBoxLayout()
        row_1.addStretch()
        row_1.addWidget(QtWidgets.QLabel('Start Date'))
        row_1.addWidget(self.input_start_date)
        row_1.addSpacing(15)
        row_1.addWidget(QtWidgets.QLabel('End Date'))
        row_1.addWidget(self.input_end_date)
        row_1.addStretch()
        main_layout.addLayout(row_1)

        main_layout.addWidget(self.title_search)

        row_2 = QtWidgets.QHBoxLayout()
        row_2.addWidget(self.select_button)
        row_2.addWidget(self.input_file)
        main_layout.addLayout(row_2)
        main_layout.addSpacing(10)

        row_3 = QtWidgets.QHBoxLayout()
        row_3.addStretch()
        row_3.addWidget(self.search_button)
        row_3.addSpacing(10)
        row_3.addSpacing(10)
        row_3.addWidget(self.done_button)
        row_3.addStretch()
        main_layout.addLayout(row_3)
        main_layout.addSpacing(10)

        main_layout.addWidget(QtWidgets.QLabel("Search Results"))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.output_list)
        main_layout.addLayout(row)
        main_layout.addSpacing(10)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.download_selected)
        row.addWidget(self.download_all)
        main_layout.addLayout(row)
        main_layout.addSpacing(10)

        main_layout.addWidget(QtWidgets.QLabel("Web Output"))
        row_4 = QtWidgets.QHBoxLayout()
        row_4.addWidget(self.output_web)
        main_layout.addLayout(row_4)

        main_layout.addWidget(self.status_bar)

        self.setLayout(main_layout)

    def set_file(self, file_path):
        self.input_file.setText(file_path)

    def get_file(self):
        return self.input_file.text()

    def get_title(self):
        return self.title_search.text()

    def get_start_date(self):
        return ''.join(self.input_start_date.text().split('-')) + '0000'

    def get_end_date(self):
        return ''.join(self.input_end_date.text().split('-')) + '0000'

    def get_selected_search_results(self):
        checked_files = []

        for i in range(self.output_list.count()):
            if self.output_list.item(i).checkState() == qt_constants.Checked:
                checked_files.append(self.output_list.item(i).text())

        return checked_files

    def get_all_search_results(self):
        run_items = []

        for i in range(self.output_list.count()):
            run_items.append(self.output_list.item(i).text())

        return run_items

    def fill_list(self, data):
        self.output_list.clear()

        for identifier in data:
            run_item = QtWidgets.QListWidgetItem(identifier, self.output_list)
            run_item.setFlags(run_item.flags() | qt_constants.ItemIsUserCheckable)
            run_item.setCheckState(qt_constants.Unchecked)

        self.download_selected.setEnabled(len(data) > 0)
        self.download_all.setEnabled(len(data) > 0)

    def log_message(self, message):
        self.output_web.insertPlainText(message)

    @staticmethod
    def launch(args=None):
        webbrowser.open(r"https://data.isis.stfc.ac.uk/browse/instrument?sort=%7B%22fullName%22%3A%22asc%22%7D")
        return 2
        # dialog = ISISDownloadDialog(args)
        # dialog.title_search.setFocus()
        # return dialog.exec()


class ISISDownloadDialogPresenter(QtCore.QObject):
    def __init__(self, view: ISISDownloadDialog):
        super().__init__()
        self._view = view

        self._session_url = r'https://icatisis.esc.rl.ac.uk/icat/session'
        self._file_data_url = r'https://icatisis.esc.rl.ac.uk/icat/lucene/data'
        self._entity_url = r'https://icatisis.esc.rl.ac.uk/icat/entityManager'
        self._cart_url = r'https://data.isis.stfc.ac.uk/topcat/user/cart/ISIS/cartItems'
        self._submit_url = r'https://data.isis.stfc.ac.uk/topcat/user/cart/ISIS/submit'
        self._download_url = r'https://data.isis.stfc.ac.uk/topcat/user/downloads'
        self._data_url = r'https://isisicatds.stfc.ac.uk/ids/getData'

        self._current_identifiers = {}
        self._session_id = None
        self._session_start = None
        self._new_files = False
        self.__file_service = services.FileService()
        self.__system_service = services.SystemService()

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.search_button.released.connect(self._on_search_clicked)
        self._view.done_button.released.connect(self._on_done_clicked)
        self._view.select_button.released.connect(self._on_save_to_clicked)
        self._view.download_selected.released.connect(self._on_download_selected_clicked)
        self._view.download_all.released.connect(self._on_download_all_clicked)

    @QtCore.pyqtSlot()
    def _on_save_to_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self._view, 'Select directory to save MUD files to',
                                                          self.__system_service.get_last_used_directory(),
                                                          options=QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            self.__system_service.set_last_used_directory(path)
            self._view.set_file(path)

    @QtCore.pyqtSlot()
    def _on_search_clicked(self):
        self._view.set_status_message('Querying ... ')
        self._view.setEnabled(False)
        QtCore.QCoreApplication.processEvents()
        self._search_request()
        self._view.setEnabled(True)
        self._view.set_status_message('Done.')

    @QtCore.pyqtSlot()
    def _on_download_selected_clicked(self):
        self._view.set_status_message('Downloading ... ')
        self._view.setEnabled(False)
        QtCore.QCoreApplication.processEvents()
        self._download_items(False)
        self._view.setEnabled(True)
        self._view.set_status_message('Done')

    @QtCore.pyqtSlot()
    def _on_download_all_clicked(self):
        self._view.set_status_message('Downloading ... ')
        self._view.setEnabled(False)
        QtCore.QCoreApplication.processEvents()
        self._download_items(True)
        self._view.setEnabled(True)
        self._view.set_status_message('Done')

    @QtCore.pyqtSlot()
    def _on_done_clicked(self):
        if self._new_files:
            self._view.done(ISISDownloadDialog.Codes.NEW_FILES)
        else:
            self._view.done(ISISDownloadDialog.Codes.NO_NEW_FILES)

    def _assemble_save(self):
        directory = self._view.get_file()

        if len(directory) == 0:
            directory = os.getcwd()

        return directory

    def _renew_session(self):
        data = {'json': json.dumps({'plugin': 'anon', 'credentials': [{'username': ''}, {'password': ''}]})}
        try:
            response = requests.post(self._session_url, data=data)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            self._session_id = None
            self._session_start = None
            return
        self._session_start = time.time()
        self._session_id = json.loads(response.text)['sessionId']

    def _check_session(self):
        if self._session_start is None or time.time() - self._session_start > 7200:
            self._renew_session()

        return self._session_id is not None

    def _search_request(self):
        self._check_session()
        data = self._gather_datafile_data()

        if data is not None:
            self._view.fill_list(['{} | {}'.format(d['Datafile']['name'], d['Datafile']['description']) for d in data if 'description' in d['Datafile'].keys()])
            self._current_identifiers = {'{} | {}'.format(d['Datafile']['name'], d['Datafile']['description']): d for d in data if 'description' in d['Datafile'].keys()}
        else:
            self._current_identifiers = {}
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')

    def _gather_dataset_ids(self):
        investigation_ids = [str(inv_id) for inv_id in self._gather_investigation_ids()]
        query_ids = ','.join(investigation_ids)
        query_string = '?sessionId={}&query=select distinct dataset from Dataset dataset , dataset.investigation as investigation where investigation.id in ({})&server=https://icatisis.esc.rl.ac.uk'.format(self._session_id, query_ids)

        try:
            response = requests.get(self._entity_url + query_string)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return [entity['Dataset']['id'] for entity in json.loads(response.text)]

    def _gather_datafile_data(self):
        dataset_ids = [str(inv_id) for i, inv_id in enumerate(self._gather_dataset_ids()) if i < 20]
        query_ids = ','.join(dataset_ids)
        query_string = '?sessionId={}&query=select distinct datafile from Datafile datafile , datafile.dataset as dataset where dataset.id in ({})&server=https://icatisis.esc.rl.ac.uk'.format(self._session_id, query_ids)

        try:
            response = requests.get(self._entity_url + query_string)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return json.loads(response.text)

    def _gather_investigation_ids(self):
        title_string = self._view.get_title()
        start_date = self._view.get_start_date()
        end_date = self._view.get_end_date()
        target = 'Investigation'
        max_count = 300

        query_string = '?sessionId={}&query={{"text":"{}","lower":"{}","upper":"{}","target":"{}"}}&maxCount={}'.format(self._session_id, title_string, start_date, end_date, target, max_count)

        try:
            response = requests.get(self._file_data_url + query_string)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return [entity['id'] for entity in json.loads(response.text)]

    def _cart_items(self, select_all=False):
        if select_all:
            identifiers = self._view.get_all_search_results()
            if len(identifiers) > 50:
                self._view.log_message('Cannot download more then 50 items at a time.\n')
                return False

            datafile_string = ','.join(['Datafile {}'.format(self._current_identifiers[identifier]['Datafile']['id']) for identifier in identifiers])
        else:
            identifiers = self._view.get_selected_search_results()
            if len(identifiers) > 50:
                self._view.log_message('Cannot download more then 50 items at a time.\n')
                return False

            datafile_string = ','.join(['Datafile {}'.format(self._current_identifiers[identifier]['Datafile']['id']) for identifier in identifiers])

        form_data = {'sessionId': self._session_id, 'items': datafile_string}

        try:
            requests.post(self._cart_url, data=form_data)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return False

        return True

    def _submit_cart(self):
        form_data = {'sessionId': self._session_id, 'fileName': 'temporary_isis_compressed', 'transport': 'https', 'email': '', 'zipType': ''}

        try:
            response = requests.post(self._submit_url, data=form_data)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return json.loads(response.text)['downloadId']

    def _prepare_download(self, download_id):
        query_string = "?facilityName=ISIS&sessionId={}&queryOffset=where download.facilityName = 'ISIS' AND download.id = {}".format(self._session_id, download_id)

        try:
            response = requests.get(self._download_url + query_string)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return json.loads(response.text)[0]['preparedId']

    def _download_items(self, select_all=False):
        self._check_session()

        success = self._cart_items(select_all)

        if not success:
            return

        download_id = self._submit_cart()

        prepared_id = self._prepare_download(download_id)

        query_string = '?preparedId={}&outname=temporary_isis_compressed'.format(prepared_id)

        try:
            response = requests.get(self._data_url + query_string)
        except requests.ConnectionError as e:
            report.report_exception(e)
            self._view.log_message('Failed to download {}. Connection Error\n'.format(query_string))
            return

        temporary_compressed_path = os.path.join(os.getcwd(), 'temporary_isis_compressed.zip')
        save_directory = self._assemble_save()

        with open(temporary_compressed_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=10485760):  # fixme, how to determine proper chunk size?
                f.write(chunk)

        new_files = []
        with zipfile.ZipFile(temporary_compressed_path, 'r') as zf:
            for member in zf.namelist():
                filename = os.path.basename(member)

                if not filename:
                    continue

                new_files.append(os.path.join(save_directory, filename))
                source = zf.open(member)
                target = open(os.path.join(save_directory, filename), 'wb')
                with source, target:
                    shutil.copyfileobj(source, target)

        os.remove(temporary_compressed_path)

        self.__file_service.add_files(new_files)
        self._new_files = True
        self._view.log_message('{} Files downloaded successfully.\n'.format(len(new_files)))
        self._view.set_status_message('Done.')
