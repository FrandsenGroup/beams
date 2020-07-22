
import enum
import os
import sys
from urllib import parse
from datetime import datetime
import json
import time
import requests

from PyQt5 import QtWidgets, QtCore

from app.util import widgets
from app.model.model import FileContext
from app.model import files


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
        self.output_list = QtWidgets.QListWidget()
        self.output_web = QtWidgets.QPlainTextEdit()
        self.title_search = QtWidgets.QLineEdit()
        self.download_selected = widgets.StyleOneButton('Download Selected')
        self.download_all = widgets.StyleOneButton('Download All')
        self.select_button = widgets.StyleTwoButton('Save to')
        self.download_button = widgets.StyleOneButton('Download')
        self.search_button = widgets.StyleOneButton('Search')
        self.done_button = widgets.StyleOneButton('Done')
        self._label_description = QtWidgets.QLabel('Provide the information below to search and download runs from '
                                                   'musr.ca.\n')

        self._set_widget_dimensions()
        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = ISISDownloadDialogPresenter(self)

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def _set_widget_dimensions(self):
        self.input_area.setFixedWidth(70)
        self.input_expt.setFixedWidth(70)
        self.input_year.setFixedWidth(70)
        self.select_button.setFixedWidth(80)
        self.download_button.setFixedWidth(80)
        self.download_all.setFixedWidth(140)
        self.download_selected.setFixedWidth(140)
        self.done_button.setFixedWidth(80)
        self.search_button.setFixedWidth(80)
        self.output_web.setFixedHeight(100)
        self.setFixedWidth(400)

    def _set_widget_attributes(self):
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
        # row_3.addWidget(self.download_button)
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

    def set_if_empty(self, expt_new, year_new, area_new):
        area = self.get_area()
        if len(area) == 0:
            self.input_area.setCurrentText(area_new)

        year = self.get_year()
        if len(year) == 0:
            self.input_year.setCurrentText(year_new)

        expt = self.get_experiment_number()
        if len(expt) == 0:
            self.input_expt.setText(expt_new)

    def get_area(self):
        return self.input_area.currentText()

    def get_year(self):
        return self.input_year.currentText()

    def get_runs(self):
        return self.input_runs.text()

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
            if self.output_list.item(i).checkState() == QtCore.Qt.Checked:
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
            run_item.setFlags(run_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            run_item.setCheckState(QtCore.Qt.Unchecked)

        self.download_selected.setEnabled(len(data) > 0)
        self.download_all.setEnabled(len(data) > 0)

    def get_experiment_number(self):
        return self.input_expt.text()

    def log_message(self, message):
        self.output_web.insertPlainText(message)

    @staticmethod
    def launch(args=None):
        dialog = ISISDownloadDialog(args)
        dialog.title_search.setFocus()
        return dialog.exec()


class ISISDownloadDialogPresenter:
    def __init__(self, view: ISISDownloadDialog):
        self._view = view
        self._search_url = "http://musr.ca/mud/runSel.php"
        self._data_url = "http://musr.ca/mud/data/"
        self._session_url = r'https://icatisis.esc.rl.ac.uk/icat/session'
        self._data_url = r'https://icatisis.esc.rl.ac.uk/icat/lucene/data'
        self._entity_url = r'https://icatisis.esc.rl.ac.uk/icat/entityManager'
        self._current_identifiers = {}
        self._session_id = None
        self._session_start = None
        self._new_files = False
        self._context = FileContext()

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.search_button.released.connect(lambda: self._search_clicked())
        self._view.download_button.released.connect(lambda: self._download_clicked())
        self._view.done_button.released.connect(lambda: self._done_clicked())
        self._view.select_button.released.connect(lambda: self._save_to_clicked())
        self._view.download_selected.released.connect(lambda: self._download_selected_clicked())
        self._view.download_all.released.connect(lambda: self._download_all_clicked())

    def _assemble_query(self):
        query = "?"

        area = self._view.get_area()
        if len(area) > 0:
            query += "area={}&".format(area)

        year = self._view.get_year()
        if len(year) > 0:
            if len(year) == 4:
                try:
                    int(year)
                except ValueError:
                    self._view.log_message("Give year as 4 digits.\n")
                    return
                query += "year={}&".format(year)
            else:
                self._view.log_message("Give year as 4 digits.\n")
                return

        expt = self._view.get_experiment_number()
        if len(expt) > 0:
            try:
                int(expt)
            except ValueError:
                self._view.log_message("Experiment number should be an integer.\n")
                return
            query += "expt={}&".format(expt)

        title = self._view.get_title()
        if len(title) > 0:
            query += "title={}&".format(title)

        return query

    def _assemble_downloads_from_search(self, selected):

        if selected:
            identifiers = self._view.get_selected_search_results()
        else:
            identifiers = self._view.get_all_search_results()

        if len(identifiers) == 0:
            return

        download_strings = []
        for identifier in identifiers:
            split_string = identifier.split(' ')
            run = split_string[0]
            year = split_string[-3].split(',')[0]
            area = split_string[-1].split(',')[0]
            download_string = '{}/{}/'.format(area, year)
            download_string += '{0:06d}.msr'.format(int(run))
            download_strings.append(download_string)

        return download_strings

    def _assemble_downloads(self):
        download_string = ""

        area = self._view.get_area()
        if len(area) == 0:
            return
        download_string += "{}/".format(area)

        year = self._view.get_year()
        if len(year) == 0:
            return
        download_string += "{}/".format(year)

        runs = self._view.get_runs()
        if len(runs) == 0:
            return

        runs = runs.split('-')
        if len(runs) == 1:
            download_string += '{0:06d}.msr'.format(int(runs[0]))
            return [download_string]

        return [download_string + '{0:06d}.msr'.format(download) for download in range(int(runs[0]), int(runs[1])+1)]

    def _assemble_save(self, download):
        directory = self._view.get_file()

        if len(directory) == 0:
            directory = os.getcwd()

        if sys.platform == 'win32':
            separator = "\\"
        else:
            separator = "/"

        return directory + "{}{}".format(separator, download.split('/')[-1])

    def _search_clicked(self):
        self._view.set_status_message('Querying ... ')
        self._search_request()
        self._view.set_status_message('Done.')

    def _download_clicked(self):
        self._view.set_status_message('Downloading ... ')

        downloads = self._assemble_downloads()
        if downloads is None:
            self._view.log_message('No runs specified.\n')
            self._view.set_status_message('Done.')
            return

        self._download(downloads)

    def _download_selected_clicked(self):
        self._view.set_status_message('Downloading ... ')

        downloads = self._assemble_downloads_from_search(True)
        if downloads is None:
            self._view.log_message('No runs specified.\n')
            self._view.set_status_message('Done.')
            return

        self._download(downloads)

    def _download_all_clicked(self):
        self._view.set_status_message('Downloading ... ')

        downloads = self._assemble_downloads_from_search(False)
        if downloads is None:
            self._view.log_message('Please finish filling in Expt Number, Year and Area.\n')
            self._view.set_status_message('Done.')
            return

        self._download(downloads)

    def _download(self, downloads):
        good = 0
        new_files = []
        for i, download in enumerate(downloads):
            full_url = self._data_url + download

            try:
                response = requests.get(full_url)
            except requests.exceptions.ConnectionError:
                self._view.log_message('Failed to download {}. Connection Error\n'.format(full_url))
                continue

            if response.status_code != 200:
                self._view.log_message('Failed to download {}. Error {}\n'.format(full_url, response.status_code))
                continue

            save_file = self._assemble_save(download)
            with open(save_file, 'wb') as fb:
                for chunk in response.iter_content(100000):
                    fb.write(chunk)
            new_files.append(save_file)
            self._new_files = True
            self._view.log_message('Successfully downloaded {}.\n'.format(full_url))
            good += 1

        self._context.add_files(new_files)
        self._view.log_message('{}/{} Files downloaded successfully.\n'.format(good, len(downloads)))
        self._view.set_status_message('Done.')

    def _done_clicked(self):
        if self._new_files:
            self._view.done(ISISDownloadDialog.Codes.NEW_FILES)
        else:
            self._view.done(ISISDownloadDialog.Codes.NO_NEW_FILES)

    def _renew_session(self):
        data = {'json': json.dumps({'plugin': 'anon', 'credentials': [{'username': ''}, {'password': ''}]})}
        try:
            response = requests.post(self._session_url, data=data)
        except requests.ConnectionError:
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
        except requests.ConnectionError:
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return [entity['Dataset']['id'] for entity in json.loads(response.text)]

    def _gather_datafile_data(self):
        dataset_ids = [str(inv_id) for i, inv_id in enumerate(self._gather_dataset_ids()) if i < 20]
        query_ids = ','.join(dataset_ids)
        query_string = '?sessionId={}&query=select distinct datafile from Datafile datafile , datafile.dataset as dataset where dataset.id in ({})&server=https://icatisis.esc.rl.ac.uk'.format(self._session_id, query_ids)

        try:
            response = requests.get(self._entity_url + query_string)
        except requests.ConnectionError:
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
            response = requests.get(self._data_url + query_string)
        except requests.ConnectionError:
            self._view.log_message('Couldn\'t get a session ID for ISIS. Connection Error.\n')
            return

        return [entity['id'] for entity in json.loads(response.text)]

    # noinspection PyCallByClass
    def _save_to_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self._view, 'Select directory to save MUD files to',
                                                          files.load_last_used_directory(),
                                                          options=QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            files.set_last_used_directory(path)
            self._view.set_file(path)


if __name__ == '__main__':
    # {"plugin":"anon","credentials":[{"username":""},{"password":""}]}

    test_data = {'json': json.dumps({'plugin': 'anon', 'credentials': [{'username': ''}, {'password': ''}]})}
    test_response = requests.post(r'https://icatisis.esc.rl.ac.uk/icat/session', data=test_data)
    print(json.loads(test_response.text)['sessionId'])


if __name__ == '__main__':
    print(parse.unquote('https://icatisis.esc.rl.ac.uk/icat/entityManager?sessionId=a242ff93-05df-4291-8547-001f67372b1f&query=select%20distinct%20dataset%20from%20Dataset%20dataset%20,%20dataset.investigation%20as%20investigation%20,%20investigation.facility%20as%20facility%20,%20facility.instruments%20as%20instrument%20,%20facility.facilityCycles%20as%20facilityCycle%20,%20investigation.investigationInstruments%20as%20investigationInstrumentPivot%20,%20investigationInstrumentPivot.instrument%20as%20investigationInstrument%20where%20facility.id%20%3D%201%20and%20instrument.id%20%3D%2028%20and%20facilityCycle.id%20%3D%2051%20and%20investigation.id%20%3D%2024064911%20and%20investigationInstrument.id%20%3D%20instrument.id%20and%20investigation.startDate%20BETWEEN%20facilityCycle.startDate%20AND%20facilityCycle.endDate%20ORDER%20BY%20dataset.createTime%20desc%20,%20dataset.id%20asc%20limit%200,%2050&server=https:%2F%2Ficatisis.esc.rl.ac.uk'))