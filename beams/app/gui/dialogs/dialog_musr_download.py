
import enum
import os
import sys
from urllib import parse
from datetime import datetime

import requests
from PyQt5 import QtWidgets, QtCore

from app.util import qt_widgets, qt_constants, report
from app.model import services


# noinspection PyArgumentList
class MusrDownloadDialog(QtWidgets.QDialog):
    class Codes(enum.IntEnum):
        NEW_FILES = 1
        NO_NEW_FILES = 2

    def __init__(self, args=None):
        super(MusrDownloadDialog, self).__init__()

        self.status_bar = QtWidgets.QStatusBar()
        self.input_area = QtWidgets.QComboBox()
        self.input_year = QtWidgets.QComboBox()
        self.input_runs = QtWidgets.QLineEdit()
        self.input_file = QtWidgets.QLineEdit()
        self.input_expt = QtWidgets.QLineEdit()
        self.output_list = qt_widgets.ListWidget()
        self.output_web = QtWidgets.QPlainTextEdit()
        self.title_search = QtWidgets.QLineEdit()
        self.download_selected = qt_widgets.StyleOneButton('Download Selected')
        self.download_all = qt_widgets.StyleOneButton('Download All')
        self.select_button = qt_widgets.StyleTwoButton('Save to')
        self.download_button = qt_widgets.StyleOneButton('Download')
        self.search_button = qt_widgets.StyleOneButton('Search')
        self.done_button = qt_widgets.StyleOneButton('Done')
        self._label_description = QtWidgets.QLabel('Provide the information below to search and download runs from '
                                                   'musr.ca.\n')

        self._set_widget_dimensions()
        self._set_widget_attributes()
        self._set_widget_layout()

        self._presenter = MusrDownloadDialogPresenter(self)

    def set_status_message(self, message):
        self.status_bar.showMessage(message)

    def _set_widget_dimensions(self):
        self.input_area.setFixedWidth(90)
        self.input_year.setFixedWidth(90)
        self.select_button.setFixedWidth(80)
        self.download_button.setFixedWidth(80)
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
        row_1.addWidget(self.input_expt)
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

    def get_experiment_number(self):
        return self.input_expt.text()

    def log_message(self, message):
        self.output_web.insertPlainText(message)

    @staticmethod
    def launch(args=None):
        dialog = MusrDownloadDialog(args)
        return dialog.exec()


class MusrDownloadDialogPresenter(QtCore.QObject):
    def __init__(self, view: MusrDownloadDialog):
        super().__init__()

        self._view = view
        self._search_url = "http://musr.ca/mud/runSel.php"
        self._data_url = "http://musr.ca/mud/data/"
        self._new_files = False
        self.__file_service = services.FileService()
        self.__system_service = services.SystemService()

        self._set_callbacks()

    def _set_callbacks(self):
        self._view.search_button.released.connect(self._on_search_clicked)
        self._view.download_button.released.connect(self._on_download_clicked)
        self._view.done_button.released.connect(self._on_done_clicked)
        self._view.select_button.released.connect(self._on_save_to_clicked)
        self._view.download_selected.released.connect(self._on_download_selected_clicked)
        self._view.download_all.released.connect(self._on_download_all_clicked)

    @QtCore.pyqtSlot()
    def _on_search_clicked(self):
        self._view.set_status_message('Querying ... ')
        query = self._assemble_query()

        if query is None:
            return

        if len(query) < 2:
            self._view.log_message("No query parameters filled.\n")
        else:
            self._view.log_message("Sending query : {}\n".format(query))

        full_url = self._search_url + query

        try:
            response = requests.get(full_url)
        except requests.exceptions.ConnectionError:
            self._view.log_message("Error: Check your internet connection.\n")
            return

        if response.status_code != 200:
            self._view.log_message("Error : {}\n".format(response.status_code))
            return

        printed_response = False
        identifiers = []
        i = True
        for x in response.text.split('TR>'):
            y = x.split('<TD')

            if len(y) > 2:
                year = y[2][1:5]
                area = y[3].split('<i>')[1].split('</i>')[0]
                expt = y[4].split('>')[1].split('<')[0]
                expt_type = y[5].split('>')[3].split('<')[0]
                run_numbers = y[6].split('"')

                if len(run_numbers) > 4:

                    if i:
                        self._view.set_if_empty(expt, year, area)
                        i = False

                    title_string = x.split('tx=')[1].split('\"')[0]
                    title = parse.unquote(title_string)

                    run_number = run_numbers[3].split()[2]
                    identifier = '{} Title: {}, Year: {}, Area: {}'.format(run_number, title, year, area)

                    identifiers.append(identifier)
                    printed_response = True

        self._view.fill_list(identifiers)
        if not printed_response:
            self._view.log_message("No runs found.\n")

        self._view.set_status_message('Done.')

    @QtCore.pyqtSlot()
    def _on_download_clicked(self):
        self._view.set_status_message('Downloading ... ')

        downloads = self._assemble_downloads()
        if downloads is None:
            self._view.log_message('No runs specified.\n')
            self._view.set_status_message('Done.')
            return

        self._download(downloads)

    @QtCore.pyqtSlot()
    def _on_download_selected_clicked(self):
        self._view.set_status_message('Downloading ... ')

        downloads = self._assemble_downloads_from_search(True)
        if downloads is None:
            self._view.log_message('No runs specified.\n')
            self._view.set_status_message('Done.')
            return

        self._download(downloads)

    @QtCore.pyqtSlot()
    def _on_download_all_clicked(self):
        self._view.set_status_message('Downloading ... ')

        downloads = self._assemble_downloads_from_search(False)
        if downloads is None:
            self._view.log_message('Please finish filling in Expt Number, Year and Area.\n')
            self._view.set_status_message('Done.')
            return

        self._download(downloads)

    @QtCore.pyqtSlot()
    def _on_done_clicked(self):
        if self._new_files:
            self._view.done(MusrDownloadDialog.Codes.NEW_FILES)
        else:
            self._view.done(MusrDownloadDialog.Codes.NO_NEW_FILES)

    @QtCore.pyqtSlot()
    def _on_save_to_clicked(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self._view, 'Select directory to save MUD files to',
                                                          self.__system_service.get_last_used_directory(),
                                                          options=QtWidgets.QFileDialog.ShowDirsOnly)
        if path:
            self.__system_service.set_last_used_directory(path)
            self._view.set_file(path)

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

    def _download(self, downloads):
        good = 0
        if len(downloads) > 500:
            self._view.log_message("Error: TRIUMF limits downloads to 500 runs or less.")
            return
            
        new_files = []
        for i, download in enumerate(downloads):
            full_url = self._data_url + download

            try:
                response = requests.get(full_url)
            except requests.exceptions.ConnectionError as e:
                report.report_exception(e)
                self._view.log_message('Failed to download {}. Connection Error\n'.format(full_url))
                continue

            if response.status_code != 200:
                self._view.log_message('Failed to download {}. Error {}\n'.format(full_url, response.status_code))
                continue

            save_file = self._assemble_save(download)
            with open(save_file, 'wb') as fb:
                for chunk in response.iter_content(1048576):
                    fb.write(chunk)
            new_files.append(save_file)
            self._new_files = True
            good += 1

        self.__file_service.add_files(new_files)
        self._view.log_message('{}/{} Files downloaded successfully.\n'.format(good, len(downloads)))
        self._view.set_status_message('Done.')
