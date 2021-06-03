
import enum
import os
import sys
from urllib import parse
import tarfile
from datetime import datetime

import requests
from PyQt5 import QtWidgets, QtCore

from app.model.domain import FileService
from app.util import widgets
from app.model import files


# fixme put limits on downloads
# noinspection PyArgumentList
class PSIDownloadDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        NEW_FILES = 1
        NO_NEW_FILES = 2

    def __init__(self, args=None):
        super(PSIDownloadDialog, self).__init__()

        self.status_bar = QtWidgets.QStatusBar()
        self.input_area = QtWidgets.QComboBox()
        self.input_year = QtWidgets.QComboBox()
        self.input_runs = QtWidgets.QLineEdit()
        self.input_file = QtWidgets.QLineEdit()
        self.input_expt = QtWidgets.QLineEdit()
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
                                                   'psi.ch.\n')

        self._set_widget_dimensions()
        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = PSIDownloadDialogPresenter(self)

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def _set_widget_dimensions(self):
        self.input_area.setFixedWidth(100)
        self.input_expt.setFixedWidth(100)
        self.input_year.setFixedWidth(100)
        self.select_button.setFixedWidth(80)
        self.download_button.setFixedWidth(80)
        self.download_all.setFixedWidth(140)
        self.download_selected.setFixedWidth(140)
        self.done_button.setFixedWidth(80)
        self.search_button.setFixedWidth(80)
        self.output_web.setFixedHeight(100)
        self.setFixedWidth(600)

    def _set_widget_attributes(self):
        self.input_area.addItems(['LEM', 'GPS', 'LTF', 'Dolly', 'GPD', 'ALC', 'HAL', 'ALL'])
        self.input_year.addItems(list([str(year) for year in range(datetime.today().year, 1992, -1)]))

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
        # row_1.addWidget(self.input_expt)
        row_1.addWidget(self.input_year)
        row_1.addWidget(self.input_area)
        row_1.addWidget(self.input_runs)
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

    def set_if_empty(self, expt_new=None, year_new=None, area_new=None):
        area = self.get_area()
        if len(area) == 0 and area_new is not None:
            self.input_area.setCurrentText(area_new)

        year = self.get_year()
        if len(year) == 0 and year_new is not None:
            self.input_year.setCurrentText(year_new)

        expt = self.get_experiment_number()
        if len(expt) == 0 and expt_new is not None:
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
        dialog = PSIDownloadDialog(args)
        return dialog.exec()


class PSIDownloadDialogPresenter:
    def __init__(self, view: PSIDownloadDialog):
        self._view = view
        self._search_url = 'http://musruser.psi.ch/cgi-bin/SearchDB.cgi'
        self._data_url = 'http://musruser.psi.ch/cgi-bin/SearchDB.cgi'
        self._new_files = False
        self.__file_service = FileService()
        self._current_identifier_uris = {}
        self._counter = 0

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.search_button.released.connect(lambda: self._search_clicked())
        self._view.download_button.released.connect(lambda: self._download_clicked())
        self._view.done_button.released.connect(lambda: self._done_clicked())
        self._view.select_button.released.connect(lambda: self._save_to_clicked())
        self._view.download_selected.released.connect(lambda: self._download_selected_clicked())
        self._view.download_all.released.connect(lambda: self._download_all_clicked())

    def _assemble_query(self):
        form_data_dictionary = {}

        area = self._view.get_area()
        if len(area) > 0:
            form_data_dictionary['AREA'] = area

        year = self._view.get_year()
        if len(year) > 0:
            if len(year) == 4:
                try:
                    int(year)
                except ValueError:
                    self._view.log_message("Give year as 4 digits.\n")
                    return
                form_data_dictionary['YEAR'] = year
            else:
                self._view.log_message("Give year as 4 digits.\n")
                return

        run = self._view.get_runs()
        if len(run) > 0:
            run = run.split('-')
            try:
                int(run[0])
            except ValueError:
                self._view.log_message("Run number should be an integer or a range (xxx-xxx)\n")
                return

            if len(run) == 2:
                try:
                    int(run[1])
                except ValueError:
                    self._view.log_message("Run number should be an integer or a range (xxx-xxx)\n")
                    return

                form_data_dictionary['Rmin'] = run[0]
                form_data_dictionary['Rmax'] = run[1]

            else:
                form_data_dictionary['RUN'] = run[0]

        title = self._view.get_title()
        if len(title) > 0:
            form_data_dictionary['Phrases'] = title

        form_data_dictionary['go'] = 'Search'

        return form_data_dictionary

    def _assemble_downloads_from_search(self, selected):

        if selected:
            identifiers = self._view.get_selected_search_results()
        else:
            identifiers = self._view.get_all_search_results()

        if len(identifiers) == 0:
            return

        form_data = {'go': 'TAR', 'Counter': self._counter,
                     'AREA': self._current_identifier_uris[identifiers[0]]['AREA'], 'FORMAT': 'PSI-BIN',
                     'HGROUP': '-h 0, 20'}
        for identifier in identifiers:
            form_data[self._current_identifier_uris[identifier]['CHECK']] = \
                self._current_identifier_uris[identifier]['URI']

        return form_data

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

    def _assemble_save(self):
        directory = self._view.get_file()

        if len(directory) == 0:
            directory = os.getcwd()

        return directory

    def _search_clicked(self):
        self._view.set_status_message('Querying ... ')
        form_data = self._assemble_query()

        if form_data is None:
            return

        if len(form_data) < 2:
            self._view.log_message("No query parameters filled.\n")
        else:
            self._view.log_message("Sending query : {}\n".format(form_data))

        try:
            response = requests.post(self._search_url, data=form_data)
        except requests.exceptions.ConnectionError:
            self._view.log_message("Error: Check your internet connection.\n")
            return

        if response.status_code != 200:
            self._view.log_message("Error : {}\n".format(response.status_code))
            return

        printed_response = False
        identifiers = []
        self._current_identifier_uris = {}
        i = True

        try:
            self._counter = response.text.split('name="Counter" value="')[1].split('"')[0]
        except IndexError:
            self._view.log_message("No results.\n")
            return

        for x in response.text.split('<tr>'):
            y = x.split('<td>')

            if len(y) == 7:
                title = y[-1].split('</td>')[0]
                run = y[-3].split('</td>')[0].split('>')[1].split('<')[0]
                year = y[-4].split('</td>')[0]

                if run != 'RUN':
                    if i:
                        self._view.set_if_empty(year_new=year)
                        i = False
                    check = y[-6].split('</td>')[0].split('name="')[1].split('"')[0]
                    uri = y[-6].split('</td>')[0].split('value="')[1].split('"')[0]

                    identifier = '{} Title: {}, Year: {}, Area: {}'.format(run, title, year, form_data['AREA'])
                    self._current_identifier_uris[identifier] = {'TITLE': title, 'RUN': run, 'YEAR': year,
                                                                 'CHECK': check, 'URI': uri, 'AREA': form_data['AREA']}

                    identifiers.append(identifier)
                    printed_response = True

        self._view.fill_list(identifiers)
        if not printed_response:
            self._view.log_message("No runs found.\n")

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

    def _download(self, form_data):
        try:
            response = requests.post(self._data_url, data=form_data, stream=True)
        except requests.ConnectionError:
            self._view.log_message('Failed to download {}. Connection Error\n'.format(form_data))
            return

        temporary_compressed_path = os.path.join(os.getcwd(), 'temp_compressed_psi_file.tar.gz')
        save_directory = self._assemble_save()

        with open(temporary_compressed_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1048576):
                f.write(chunk)

        tar_file_object = tarfile.open(temporary_compressed_path, 'r')
        tar_file_object.extractall(save_directory,
                     members=[member for member in tar_file_object.getmembers() if member.name != 'out.txt'])
        new_files = [os.path.join(save_directory, member.name) for member in tar_file_object.getmembers() if member.name != 'out.txt']
        tar_file_object.close()
        os.remove(temporary_compressed_path)

        self.__file_service.add_files(new_files)
        self._new_files = True
        self._view.log_message('{} Files downloaded successfully.\n'.format(len(new_files)))
        self._view.set_status_message('Done.')

    def _done_clicked(self):
        if self._new_files:
            self._view.done(PSIDownloadDialog.Codes.NEW_FILES)
        else:
            self._view.done(PSIDownloadDialog.Codes.NO_NEW_FILES)

    # noinspection PyCallByClass
    def _save_to_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self._view, 'Select directory to save MUD files to',
                                                          files.load_last_used_directory(),
                                                          options=QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            files.set_last_used_directory(path)
            self._view.set_file(path)
