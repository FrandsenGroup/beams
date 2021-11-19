import logging
import os

from PyQt5 import QtWidgets, QtCore

from app.gui.dialogs.dialog_isis_download import ISISDownloadDialog
from app.gui.dialogs.dialog_misc import AddFileDialog, PermissionsMessageDialog, WarningMessageDialog
from app.gui.dialogs.dialog_musr_download import MusrDownloadDialog
from app.gui.dialogs.dialog_psi_download import PSIDownloadDialog
from app.gui.dialogs.dialog_write_data import WriteDataDialog
from app.gui.dialogs.dialog_plot_file import PlotFileDialog
from app.gui.gui import PanelPresenter
from app.model import files, services, objects
from app.util import qt_widgets, qt_constants


class MainConsolePanel(QtWidgets.QDockWidget):
    class Tree(QtWidgets.QTreeWidget):
        def __init__(self):
            super().__init__()
            self.__manager = MainConsolePanel.TreeManager(self)
            self.setHeaderHidden(True)
            self.setContextMenuPolicy(qt_constants.CustomContextMenu)
            self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self._set_callbacks()

        def _set_callbacks(self):
            self.customContextMenuRequested.connect(self._launch_menu)

        def _launch_menu(self, point):
            index = self.indexAt(point)

            if not index.isValid():
                return

            item = self.itemAt(point)
            menu = item.menu(self.selectedItems())
            menu.exec_(self.mapToGlobal(point))

        def set_tree(self, tree):
            self.clear()
            self.addTopLevelItems(tree)

        def get_file_ids(self):
            # noinspection PyTypeChecker
            iterator = QtWidgets.QTreeWidgetItemIterator(self, QtWidgets.QTreeWidgetItemIterator.Checked)

            ids = []
            while iterator.value():
                if isinstance(iterator.value().model, objects.FileDataset):
                    ids.append(iterator.value().model.id)

                iterator += 1

            return ids

        def set_checked_by_ids(self, ids):
            # noinspection PyTypeChecker
            for i in range(self.topLevelItemCount()):
                if self.topLevelItem(i).model.id in ids:
                    self.topLevelItem(i).setCheckState(0, qt_constants.Checked)

        def set_all_checked(self, checked):
            for i in range(self.topLevelItemCount()):
                self.topLevelItem(i).setCheckState(0, checked)

    class TreeManager(PanelPresenter):
        def __init__(self, view):
            super().__init__(view)
            self.__view = view
            self.__logger = logging.getLogger("MainConsolePanelTreeManager")
            self.__run_service = services.RunService()
            self.__fit_service = services.FitService()
            self.__file_service = services.FileService()

            self.__run_service.signals.added.connect(self.update)
            self.__file_service.signals.changed.connect(self.update)
            self.__fit_service.signals.added.connect(self.update)

        def _create_tree_model(self, file_datasets):
            file_nodes = []
            for dataset in file_datasets:
                file_nodes.append(MainConsolePanel.FileNode(dataset))
            return file_nodes

        @QtCore.pyqtSlot()
        def update(self):
            ids = self.__view.get_file_ids()
            file_datasets = self.__file_service.get_files()
            tree = self._create_tree_model(file_datasets)
            self.__view.set_tree(tree)
            self.__view.set_checked_by_ids(ids)

    class HeadingNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, title):
            super(MainConsolePanel.HeadingNode, self).__init__([str(title)])
            self.__selected_items = None

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            expanded = 'Expand' if not self.isExpanded() else 'Collapse'
            menu.addAction(expanded, self._action_expand)
            return menu

        def _action_expand(self):
            self.setExpanded(not self.isExpanded())

        def _set_callbacks(self):
            pass

        def _expand(self):
            pass

    class FileNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, file_data):
            super(MainConsolePanel.FileNode, self).__init__([file_data.title])
            self.model = file_data
            self.__selected_items = None
            self.__file_service = services.FileService()
            self.setFlags(self.flags()
                          | qt_constants.ItemIsUserCheckable)
            self.setCheckState(0, qt_constants.Unchecked)

            data_object = file_data.dataset

            if isinstance(data_object, objects.RunDataset):
                if data_object.isLoaded:
                    histogram_node = MainConsolePanel.HeadingNode("Histograms")
                    if data_object.histograms:
                        for histogram in data_object.histograms.values():
                            histogram_node.addChild(MainConsolePanel.HistogramNode(histogram))
                        self.addChild(histogram_node)

                    asymmetry_node = MainConsolePanel.HeadingNode("Asymmetries")
                    for asymmetry in data_object.asymmetries.values():
                        if asymmetry is not None:
                            asymmetry_node.addChild(MainConsolePanel.AsymmetryNode(asymmetry))
                        else:
                            asymmetry_node = MainConsolePanel.HeadingNode("Asymmetries")
                    self.addChild(asymmetry_node)
                else:
                    self.addChild(MainConsolePanel.HeadingNode("Histograms - not loaded"))
                    self.addChild(MainConsolePanel.HeadingNode("Asymmetries - not loaded"))

                self.addChild(MainConsolePanel.MetaNode(data_object.meta))

            elif isinstance(data_object, dict):
                for run_number, parameters in data_object.items():
                    run_node = MainConsolePanel.HeadingNode(run_number)
                    for symbol, value in parameters.items():
                        run_node.addChild(MainConsolePanel.KeyValueNode(symbol, value))
                    self.addChild(run_node)

            elif isinstance(data_object, objects.FitDataset):
                self.addChild(MainConsolePanel.HeadingNode("Expression: {}".format(data_object.expression)))
                fits_node = MainConsolePanel.HeadingNode("Fits")
                for f in data_object.fits.values():
                    fits_node.addChild(MainConsolePanel.FitNode(f))
                self.addChild(fits_node)

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            menu.addAction("Load", self._action_load)
            return menu

        def _action_load(self):
            if isinstance(self.model.file, files.BeamsSessionFile):
                code = PermissionsMessageDialog.launch(["Loading a saved session will remove all current session data, do you wish to continue?"])
                if code == PermissionsMessageDialog.Codes.OKAY:
                    try:
                        self.__file_service.load_session(self.model.id)
                    except files.BeamsFileReadError as e:
                        WarningMessageDialog.launch([str(e)])

    class FitNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, fit):
            super(MainConsolePanel.FitNode, self).__init__([fit.title])
            self.__model = fit
            self.__selected_items = None
            for symbol, par in fit.parameters.items():
                self.addChild(MainConsolePanel.KeyValueNode(symbol, '{}({})'.format(par.value, par.uncertainty)))

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            return menu

    class HistogramNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, histogram):
            super(MainConsolePanel.HistogramNode, self).__init__([histogram.title])
            self.__model = histogram
            self.__selected_items = None
            # self.addChild(MetaNode())

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            expanded = 'Expand' if not self.isExpanded() else 'Collapse'
            menu.addAction(expanded, self._action_expand)
            menu.addSeparator()
            menu.addAction("Combine", self._action_combine)
            menu.addAction("Asymmetry", self._action_asymmetry)
            menu.addAction("Edit", self._action_edit)
            menu.addAction("Write", self._action_write)
            return menu

        def _action_expand(self):
            self.setExpanded(not self.isExpanded())

        def _action_combine(self):
            pass

        def _action_asymmetry(self):
            pass

        def _action_edit(self):
            pass

        def _action_write(self):
            pass

    class AsymmetryNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, asymmetry):
            title = "{}ns packing".format(asymmetry.bin_size)
            super(MainConsolePanel.AsymmetryNode, self).__init__([title])
            self.__model = asymmetry
            self.__selected_items = None

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            expanded = 'Expand' if not self.isExpanded() else 'Collapse'
            menu.addAction(expanded, self._action_expand)
            menu.addSeparator()
            menu.addAction("Combine", self._action_combine)
            menu.addAction("Plot", self._action_plot)
            menu.addAction("Edit", self._action_edit)
            menu.addAction("Write", self._action_write)
            return menu

        def _action_expand(self):
            self.setExpanded(not self.isExpanded())

        def _action_combine(self):
            pass

        def _action_plot(self):
            pass

        def _action_edit(self):
            pass

        def _action_write(self):
            pass

    class UncertaintyNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, uncertainty):
            super(MainConsolePanel.UncertaintyNode, self).__init__(['Uncertainty'])
            self.__model = uncertainty
            self.__selected_items = None

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            return menu

    class MetaNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, meta):
            super(MainConsolePanel.MetaNode, self).__init__(["Meta"])
            self.__model = meta
            self.__selected_items = None
            for k, v in meta.items():
                self.addChild(MainConsolePanel.KeyValueNode(k, v))

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            expanded = 'Expand' if not self.isExpanded() else 'Collapse'
            menu.addAction(expanded, self._action_expand)
            return menu

        def _action_expand(self):
            self.setExpanded(not self.isExpanded())

    class KeyValueNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, key, value):
            super(MainConsolePanel.KeyValueNode, self).__init__(["{}: {}".format(key, value)])
            self.__model = (key, value)
            self.__selected_items = None

        def menu(self, items):
            self.__selected_items = items
            menu = QtWidgets.QMenu()
            menu.addAction("Edit", self._action_edit)
            return menu

        def _action_edit(self):
            pass

    class SessionNode(QtWidgets.QTreeWidgetItem):
        def __init__(self, session_file_dataset):
            title = os.path.split(session_file_dataset.file.file_path)[1]
            super(MainConsolePanel.SessionNode, self).__init__([title])
            self.model = session_file_dataset

        def menu(self, items):
            menu = QtWidgets.QMenu()
            menu.addAction("Load")
            return menu

        def _set_callbacks(self):
            pass

        def _load(self):
            pass

    def __init__(self):
        super(MainConsolePanel, self).__init__()
        self.setTitleBarWidget(QtWidgets.QWidget())
        self.setWindowTitle("Files")

        # Create our widget which will hold everything for this panel.
        self._full_widget = QtWidgets.QWidget()

        # Create Widgets
        self.file_list_box = qt_widgets.CollapsibleBox("Files")
        self.file_list = qt_widgets.StyleOneListWidget()
        self.select_all = QtWidgets.QCheckBox()
        self.write_button = qt_widgets.StyleOneButton("Write")
        self.import_button = qt_widgets.StyleTwoButton("+")
        self.remove_button = qt_widgets.StyleTwoButton('-')
        self.load_button = qt_widgets.StyleOneButton("Load")
        self.convert_button = qt_widgets.StyleOneButton("Convert")
        self.tree_view = self.Tree()

        # Set Widget Dimensions

        self.select_all.setFixedWidth(20)
        self.import_button.setFixedWidth(20)
        self.remove_button.setFixedWidth(20)
        self.setMaximumHeight(350)

        # Set Widget Tooltips
        self.write_button.setToolTip('Write currently plotted data to .asy files')
        self.import_button.setToolTip('Add files')
        self.remove_button.setToolTip('Remove currently selected files.')
        self.load_button.setToolTip('Load currently selected files')
        self.convert_button.setToolTip('Convert .msr formatted files to .dat ')
        self.select_all.setToolTip('Select all files.')

        # Layout Widgets
        hbox_one = QtWidgets.QHBoxLayout()
        hbox_one.addWidget(self.select_all)
        hbox_one.addWidget(self.import_button)
        hbox_one.addWidget(self.remove_button)
        hbox_one.addWidget(self.convert_button)
        hbox_one.addWidget(self.load_button)
        hbox_one.addWidget(self.write_button)
        hbox_one.addStretch()

        self.tree_view.setHorizontalScrollBarPolicy(qt_constants.ScrollBarAsNeeded)
        self.tree_view.header().setMinimumSectionSize(600)
        self.tree_view.header().setDefaultSectionSize(900)
        self.tree_view.header().setStretchLastSection(False)

        vbox_one = QtWidgets.QVBoxLayout()
        vbox_one.addLayout(hbox_one)
        vbox_one.addWidget(self.tree_view, 2)
        self._full_widget.setLayout(vbox_one)

        # Set DockWidget to be fully laid out widget.
        self.setWidget(self._full_widget)
        self.setFloating(False)

        self._presenter = MainConsolePanelPresenter(self)

    def get_checked_items(self):
        return self.tree_view.get_file_ids()


class MainConsolePanelPresenter(PanelPresenter):
    def __init__(self, view: MainConsolePanel):
        super().__init__(view)
        
        self.__file_service = services.FileService()
        self.__system_service = services.SystemService()
        self.__logger = logging.getLogger("MainConsolePanelPresenter")
        
        self._set_callbacks()
        
    def _set_callbacks(self):
        self._view.import_button.released.connect(lambda: self._add_file_clicked())
        self._view.write_button.released.connect(lambda: self._write_file_clicked())
        self._view.load_button.released.connect(lambda: self._load_file_clicked())
        self._view.convert_button.released.connect(lambda: self._convert_file_clicked())
        self._view.remove_button.released.connect(lambda: self._remove_file_clicked())
        self._view.select_all.stateChanged.connect(lambda: self._select_all_checked())

    @QtCore.pyqtSlot()
    def update(self, signal):
        pass

    def _add_file_clicked(self):
        code = AddFileDialog.launch()

        if code == AddFileDialog.Codes.FILE_SYSTEM:
            self._get_files_from_system()
        elif code == AddFileDialog.Codes.MUSR_DOWNLOAD:
            MusrDownloadDialog.launch()
        elif code == AddFileDialog.Codes.PSI_DOWNLOAD:
            PSIDownloadDialog.launch()
        elif code == AddFileDialog.Codes.ISIS_DOWNLOAD:
            ISISDownloadDialog.launch()

    def _write_file_clicked(self):
        file_ids = self._view.tree_view.get_file_ids()
        WriteDataDialog.launch(*file_ids)

    def _load_file_clicked(self):
        file_ids = self._view.tree_view.get_file_ids()
        file_objects = services.FileService().get_files(file_ids)

        fit_file_ids = []
        dialog_message = 'Load fits from the following files?\n'
        
        unloaded_fit_files_present = False
        for f in file_objects:
            if f.file.DATA_FORMAT == files.Format.FIT_SET_VERBOSE and not f.dataset.is_loaded:
                unloaded_fit_files_present = True
                dialog_message += f"\u2022 {f.title}\n"
                fit_file_ids.append(f.id)
            elif f.file.DATA_FORMAT == files.Format.PICKLED:
                code = PermissionsMessageDialog.launch(["Loading a saved session will remove all current session data, do you wish to continue?"])
                if code == PermissionsMessageDialog.Codes.OKAY:
                    try:
                        self.__file_service.load_session(f.id)
                        return
                    except files.BeamsFileReadError as e:
                        WarningMessageDialog.launch([str(e)])

        runs = []
        if unloaded_fit_files_present:
            code = PermissionsMessageDialog.launch([dialog_message])
            if code == PermissionsMessageDialog.Codes.OKAY:
                for f in file_objects:
                    if f.file.DATA_FORMAT == files.Format.FIT_SET_VERBOSE and not f.dataset.is_loaded:
                        fits_by_ids = {}
                        bad_files_list = []

                        for fit in f.dataset.fits.values():
                            try:
                                # Try to add the file retrieved from the .fit file
                                run_file_list = self.__file_service.add_files([fit.meta[files.FILE_PATH_KEY]])
                            except FileNotFoundError:
                                # If the file does not exist then we still need a reference to the fit in the new dict
                                fits_by_ids[fit.run_id] = fit
                                bad_files_list.append(fit.meta[files.FILE_PATH_KEY])
                                continue

                            if len(run_file_list) == 0:
                                continue

                            # Link the fit to its corresponding run dataset
                            run_file = run_file_list[0]
                            file_ids.append(run_file.id)
                            fit.run_id = run_file.dataset.id
                            fits_by_ids[fit.run_id] = fit
                            runs.append(run_file.dataset)

                        if len(bad_files_list) > 0:
                            bad_files_str = "The following files could not be found:\n\u2022 "
                            bad_files_str += '\n\u2022 '.join(bad_files_list)
                            WarningMessageDialog.launch([bad_files_str])

                        f.dataset.fits = fits_by_ids
                        f.dataset.is_loaded = True
            else:
                # If the user doesn't want to load the .fit files then remove them from the list of files to be loaded.
                file_ids = [f for f in file_ids if f not in fit_file_ids]

        if len(file_ids) > 0:
            try:
                self.__file_service.load_files(file_ids)
            except files.BeamsFileReadError as e:
                WarningMessageDialog.launch([e.message])
                return

            if unloaded_fit_files_present:
                if len(runs) > 0:
                    PlotFileDialog.launch([runs])
                else:
                    WarningMessageDialog.launch(["None of the files listed in the .fit file(s) could be found."])

    def _convert_file_clicked(self):
        self.__file_service.convert_files(self._view.tree_view.get_file_ids())

    def _remove_file_clicked(self):
        checked_items = self._view.get_checked_items()

        code = PermissionsMessageDialog.launch(["Remove {} file(s)?".format(len(checked_items))])

        if code == PermissionsMessageDialog.Codes.OKAY:
            self.__file_service.remove_files(checked_items)

    def _select_all_checked(self):
        self._view.tree_view.set_all_checked(self._view.select_all.isChecked())

    def _get_files_from_system(self):
        filenames = QtWidgets.QFileDialog.getOpenFileNames(self._view, 'Add file',
                                                           self.__system_service.get_last_used_directory())[0]
        if len(filenames) > 0:
            path = os.path.split(filenames[0])
            self.__system_service.set_last_used_directory(path[0])

        self.__file_service.add_files(filenames)
