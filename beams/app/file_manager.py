
from PyQt5 import QtWidgets, QtCore

from util import widgets
from app.model import RunService


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
        self._set_callbacks()

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
        files = []

        for i in range(self.file_list.count()):
            files.append(self.file_list.item(i).text())

        return files

    def get_checked_items(self):
        """
        Gets all items currently listed and checked.
        :return checked_files: an array of checked files as titled in the view
        """
        checked_files = []

        for i in range(self.file_list.count()):
            if self.file_list.item(i).checkState() == QtCore.Qt.Checked:
                checked_files.append(self.file_list.item(i).text)

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

    def check_all_items(self):
        """
        Sets check state of all items to 'checked.'
        """
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(QtCore.Qt.Checked)

    def uncheck_all_item(self):
        """
        Sets check state of all items to 'unchecked.'
        """
        for i in range(self.file_list.count()):
            self.file_list.item(i).setCheckState(QtCore.Qt.Unchecked)


class FileManagerPanelPresenter:
    def __init__(self, view):
        self.view = view
        self.service = RunService()

        self._title_to_file_path = {}

    def _set_callbacks(self):
        """
        Sets the callbacks presenter to handle relevant signals from the view.
        """
        self.view.import_button.released.connect(lambda: self._add_file_clicked())
        self.view.write_button.released.connect(lambda: self._write_file_clicked())
        self.view.plot_button.released.connect(lambda: self._plot_file_clicked())
        self.view.convert_button.released.connect(lambda: self._convert_file_clicked())
        self.view.remove_button.released.connect(lambda: self._remove_file_clicked())
        self.view.select_all.stateChanged.connect(lambda: self._select_all_checked())

    def _add_file_clicked(self):
        pass

    def _remove_file_clicked(self):
        pass

    def _convert_file_clicked(self):
        pass

    def _plot_file_clicked(self):
        pass

    def _write_file_clicked(self):
        pass

    def _select_all_checked(self):
        """
        Handles the user checking or unchecking the 'select all' box.
        """
        if self.view.get_select_all_state():
            self.view.check_all_items()
        else:
            self.view.uncheck_all_items()
