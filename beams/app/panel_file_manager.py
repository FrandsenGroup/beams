
import os

from PyQt5 import QtWidgets, QtCore

from app.util import widgets
from app.model.model import FileContext, MuonDataContext, PlotContext
from app.model import files
from app.dialog_misc import AddFileDialog, WarningMessageDialog, PermissionsMessageDialog
from app.dialog_musr_download import MusrDownloadDialog
from app.dialog_plot_file import PlotFileDialog
from app.dialog_write_data import WriteDataDialog
from app.beams import BEAMS


# noinspection PyArgumentList
class FileManagerPanel(QtWidgets.QDockWidget):
    def __init__(self):
        super(FileManagerPanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setWindowTitle("File Manager")

        # Create our widget which will hold everything for this panel.
        self._full_widget = QtWidgets.QWidget()

        # Create Widgets
        self.file_list = QtWidgets.QListWidget()
        self.select_all = QtWidgets.QCheckBox()
        self.write_button = widgets.StyleOneButton("Write")
        self.import_button = widgets.StyleTwoButton("+")
        self.remove_button = widgets.StyleTwoButton('-')
        self.plot_button = widgets.StyleOneButton("Plot")
        self.convert_button = widgets.StyleOneButton("Convert")

        # Set Widget Dimensions

        self.select_all.setFixedWidth(20)
        self.import_button.setFixedWidth(25)
        self.remove_button.setFixedWidth(25)
        self.convert_button.setFixedWidth(60)
        self.setMaximumWidth(350)
        '''
        self.write_button.setFixedWidth(60)
        self.plot_button.setFixedWidth(60)
        self.convert_button.setFixedWidth(60)
        '''

        # Set Widget Tooltips
        self.write_button.setToolTip('Write currently plotted data to .asy files')
        self.import_button.setToolTip('Add files')
        self.remove_button.setToolTip('Remove currently selected files.')
        self.plot_button.setToolTip('Plot currently selected files')
        self.convert_button.setToolTip('Convert .msr formatted files to .dat ')
        self.select_all.setToolTip('Select all files.')

        # Layout Widgets
        hbox_one = QtWidgets.QHBoxLayout()
        hbox_one.addWidget(self.select_all)
        hbox_one.addWidget(self.import_button)
        hbox_one.addWidget(self.remove_button)
        hbox_one.addWidget(self.convert_button)
        hbox_one.addWidget(self.plot_button)
        hbox_one.addWidget(self.write_button)

        hbox_two = QtWidgets.QHBoxLayout()
        hbox_two.addWidget(self.file_list)

        vbox_one = QtWidgets.QVBoxLayout()
        vbox_one.addLayout(hbox_one)
        vbox_one.addLayout(hbox_two)
        self._full_widget.setLayout(vbox_one)

        # Set DockWidget to be fully laid out widget.
        self.setWidget(self._full_widget)
        self.setFloating(False)

        # Connect to presenter
        self._presenter = FileManagerPanelPresenter(self)

    def get_select_all_state(self):
        """
        Gets the check state of the 'select all' box.
        """
        return self.select_all.checkState()

    def get_all_items(self):
        """
        Gets all items currently listed.
        :return files: an array of files as titled in the view
        """
        file_items = []

        for i in range(self.file_list.count()):
            file_items.append(self.file_list.item(i).text())

        return file_items

    def get_checked_items(self):
        """
        Gets all items currently listed and checked.
        :return checked_files: an array of checked files as titled in the view
        """
        checked_files = []

        for i in range(self.file_list.count()):
            if self.file_list.item(i).checkState() == QtCore.Qt.Checked:
                checked_files.append(self.file_list.item(i).text())

        return checked_files

    def remove_item(self, title):
        """
        Removes an item matching 'title' from the view.
        :param title: title of item to be removed
        """
        for i in range(self.file_list.count()):
            if self.file_list.item(i).text() == title:
                self.file_list.takeItem(i)
                break

    def replace_item(self, original_title, new_title):
        """
        Replaces an item matching 'original_title' with 'new_title.'
        :param original_title: the title to be replaced
        :param new_title: the title replacing the original
        """
        for i in range(self.file_list.count()):
            if self.file_list.item(i).text() == original_title:
                self.file_list.item(i).setText(new_title)
                break

    def add_item(self, title):
        """
        Adds an item with the specified 'title' to the view
        :param title: title of item to be added to the view
        """
        file_item = QtWidgets.QListWidgetItem(title, self.file_list)
        file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
        file_item.setCheckState(QtCore.Qt.Unchecked)

    def add_items(self, titles):
        for title in titles:
            file_item = QtWidgets.QListWidgetItem(title, self.file_list)
            file_item.setFlags(file_item.flags() | QtCore.Qt.ItemIsUserCheckable)
            file_item.setCheckState(QtCore.Qt.Unchecked)

    def check_all_items(self):
        """
        Sets check state of all items to 'checked.'
        """
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(QtCore.Qt.Checked)

    def uncheck_all_items(self):
        """
        Sets check state of all items to 'unchecked.'
        """
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(QtCore.Qt.Unchecked)

    def clear_items(self):
        for i in range(self.file_list.count()-1, -1, -1):
            self.file_list.takeItem(i)


class FileManagerPanelPresenter:
    def __init__(self, view):
        self._view = view
        self._model = FileManagerPanelModel(self)
        self._set_callbacks()

    def _set_callbacks(self):
        """
        Sets the callbacks presenter to handle relevant signals from the view.
        """
        self._view.import_button.released.connect(lambda: self._add_file_clicked())
        self._view.write_button.released.connect(lambda: self._write_file_clicked())
        self._view.plot_button.released.connect(lambda: self._plot_file_clicked())
        self._view.convert_button.released.connect(lambda: self._convert_file_clicked())
        self._view.remove_button.released.connect(lambda: self._remove_file_clicked())
        self._view.select_all.stateChanged.connect(lambda: self._select_all_checked())

    def _add_file_clicked(self):
        code = AddFileDialog.launch()

        if code == AddFileDialog.Codes.FILE_SYSTEM:
            self._get_files_from_system()
        else:
            MusrDownloadDialog.launch()

    def _remove_file_clicked(self):
        checked_items = self._view.get_checked_items()

        code = PermissionsMessageDialog.launch(["Remove {} file(s)?".format(len(checked_items))])

        if code == PermissionsMessageDialog.Codes.OKAY:
            self._model.remove_files(checked_items)

    def _convert_file_clicked(self):
        self._model.convert_files(self._view.get_checked_items())

    def _plot_file_clicked(self):
        file_paths = self._model.get_file_paths_from_titles(self._view.get_checked_items())

        muon_files = []
        for file_path in file_paths:
            reader = files.file(file_path)
            if reader.DATA_TYPE == files.DataType.MUON:
                muon_files.append(file_path)

            if reader.DATA_FORMAT == files.Format.BINARY or reader.DATA_FORMAT == files.Format.UNKNOWN:
                WarningMessageDialog.launch(["Files selected which can not be plotted."])
                return

        if muon_files:
            PlotFileDialog.launch([muon_files])

    def _write_file_clicked(self):
        current_items = self._model.get_file_paths_from_titles(self._view.get_checked_items())

        if current_items:
            WriteDataDialog.launch([current_items])
        else:
            WarningMessageDialog.launch(["No files selected."])

    def _select_all_checked(self):
        """
        Handles the user checking or unchecking the 'select all' box.
        """
        if self._view.get_select_all_state():
            self._view.check_all_items()
        else:
            self._view.uncheck_all_items()

    def _get_files_from_system(self):
        # noinspection PyArgumentList
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self._view, 'Add file',
                                                           BEAMS.load_last_used_directory())[0]
        if len(filenames) > 0:
            path = os.path.split(filenames[0])
            BEAMS.set_last_used_directory(path[0])

        self._model.add_files(filenames)
        self._view.clear_items()
        self._view.add_items(self._model.get_file_titles())

    def update(self):
        print('Updating the File Manager')
        self._view.clear_items()
        self._view.add_items(self._model.get_file_titles())


class FileManagerPanelModel:
    def __init__(self, observer=None):
        self._data_context = MuonDataContext()
        self._file_context = FileContext()
        self._plot_context = PlotContext()
        self._file_context.subscribe(self)

        self._title_to_file_path = {}
        self._observer = observer

    def get_file_paths_from_titles(self, titles):
        return [self._title_to_file_path[title] for title in titles]

    def remove_files(self, titles):
        files_to_remove = [self._title_to_file_path[title] for title in titles]
        for file_path in files_to_remove:
            run = self._data_context.get_run_by_filename(file_path)
            if run is not None:
                self._plot_context.clear_plot_parameters(run.id, stop_signal=True)
        self._file_context.remove_files(files_to_remove)
        self._data_context.remove_runs_by_filename(files_to_remove)

    def add_files(self, file_paths):
        for file_path in file_paths:
            file_reader = files.file(file_path)
            if file_reader.SOURCE == files.Source.BEAMS:
                title = os.path.split(file_path)[1] + " - " + file_reader.read_meta()[files.TITLE_KEY]
                if title not in self._title_to_file_path.keys():
                    self._title_to_file_path[title] = file_path
            else:
                title = os.path.split(file_path)[1]
                if title not in self._title_to_file_path.keys():
                    self._title_to_file_path[title] = file_path

        self._file_context.add_files(file_paths, stop_signal=True)

    def update_files(self, file_paths):
        self._title_to_file_path = {}
        self.add_files(file_paths)

    def convert_files(self, file_paths):
        titles = []
        removed_titles = []

        for file_path in file_paths:
            file_reader = files.file(self._title_to_file_path[file_path])
            if file_reader.DATA_FORMAT == files.Format.BINARY:
                title = os.path.split(file_path)[1]
                removed_titles.append(title)

                out_file = os.path.splitext(self._title_to_file_path[title])[0] + '.dat'
                file_reader = file_reader.convert(out_file)

                title = os.path.split(out_file)[1] + " - " + file_reader.read_meta()[files.TITLE_KEY]
                titles.append(title)
                self._title_to_file_path[title] = file_reader.file_path

        self._file_context.remove_files([self._title_to_file_path[title] for title in removed_titles], stop_signal=True)

        for title in removed_titles:
            self._title_to_file_path.pop(title)

        self._file_context.add_files([self._title_to_file_path[title] for title in titles])

    def get_files(self):
        return sorted(list(self._file_context.get_files()))

    def get_file_titles(self):
        return sorted(list(self._title_to_file_path.keys()))

    def update(self):
        self.update_files(self._file_context.get_files())
        self.notify()

    def notify(self):
        self._observer.update()
