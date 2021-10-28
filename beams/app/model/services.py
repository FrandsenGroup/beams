import enum
import json
import os
import logging
import pickle

from PyQt5 import QtCore

import app.model.data_access as dao
from app.model import objects, files
from app.resources import resources


class Service:
    def __init__(self):
        self.__observers = {}

    def register(self, observer, signal):
        self.__observers[signal] = [observer] if signal not in self.__observers.keys() else self.__observers[signal].append(observer)

    def notify(self, signal):
        pass


class FitService:
    class Signals(QtCore.QObject):
        added = QtCore.pyqtSignal()
        changed = QtCore.pyqtSignal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__dao = dao.FitDAO()
            cls._instance.__logger = logging.getLogger("FitService")
            cls._instance.signals = FitService.Signals()
        return cls._instance

    def get_fit_datasets(self):
        return self.__dao.get_fits()

    def add_dataset(self, datasets, suppress_signal=False):
        self.__dao.add_fits(datasets)

        if not suppress_signal:
            self.signals.added.emit()

    def remove_dataset(self, ids):
        self.__dao.remove_fits_by_ids(ids)
        self.signals.changed.emit()

    def remove_fits_from_datasets(self, id_mappings):
        raise NotImplementedError()

    def changed(self):
        self.signals.changed.emit()


class RunService:
    class Signals(QtCore.QObject):
        added = QtCore.pyqtSignal()
        changed = QtCore.pyqtSignal()
        loaded = QtCore.pyqtSignal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__dao = dao.RunDAO()
            cls._instance.__logger = logging.getLogger("RunService")
            cls._instance.signals = RunService.Signals()
        return cls._instance

    def get_runs(self):
        return self.__dao.get_runs()

    def get_runs_by_ids(self, ids):
        return self.__dao.get_runs_by_ids(ids)

    def get_loaded_runs(self):
        loaded_runs = []
        for run in self.__dao.get_runs():
            if run.isLoaded:
                loaded_runs.append(run)
        return loaded_runs

    def load_runs(self, ids):
        pass

    def combine_histograms(self, ids, titles):
        pass

    def recalculate_asymmetries(self, ids):
        self.__logger.debug("Updated Asymmetry for Runs=({})".format(str(ids)))
        for run in self.__dao.get_runs_by_ids(ids):
            if len(run.histograms_used) == 2:
                run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] = objects.Asymmetry(
                    histogram_one=run.histograms[run.histograms_used[0]],
                    histogram_two=run.histograms[run.histograms_used[1]],
                    alpha=run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].alpha)

                if run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                    run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                    run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        self.signals.changed.emit()

    def add_runs(self, paths):
        builder = objects.DataBuilder()
        for path in paths:
            run = builder.build_minimal(path)
            self.__dao.add_runs([run])

        self.signals.added.emit()

    def remove_runs_by_ids(self, ids):
        self.__logger.debug("Removing Run Datasets=({})".format(str(ids)))
        self.__dao.remove_runs_by_ids(ids)

        self.signals.loaded.emit()

    def add_dataset(self, datasets, suppress_signal):
        self.__logger.debug("Adding Run Datasets=({})".format(str(datasets)))
        self.__dao.add_runs(datasets)

        if not suppress_signal:
            self.signals.added.emit()

    def update_runs_by_ids(self, ids, asymmetries):
        self.__logger.debug("Updating Asymmetries for Runs=({}) with Asymmetries=({})".format(str(ids), str(asymmetries)))
        self.__dao.update_runs_by_id(ids, asymmetries)
        self.signals.changed.emit()

    def update_alphas(self, ids, alphas):
        self.__logger.debug("Updating Alphas for Runs=({}) with Alphas=({})".format(str(ids), str(alphas)))
        if len(alphas) == 1:  # When we update alpha from plotting panel we send one alpha for multiple runs
            alpha = alphas[0]
            alphas = [alpha for _ in ids]

        for rid, alpha in zip(ids, alphas):
            run = self.__dao.get_runs_by_ids([rid])[0]

            run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].correct(alpha)

            if run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        self.signals.changed.emit()

    def changed(self):
        self.signals.changed.emit()


class StyleService:
    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    class Keys(enum.Enum):
        ID = 1
        LABEL = 2
        VISIBLE = 3
        ERROR_BARS = 4
        LINE = 5
        MARKER = 6
        LINE_COLOR = 7
        MARKER_COLOR = 8
        FILLSTYLE = 9
        DEFAULT_COLOR = 10
        LINESTYLE = 11
        LINE_WIDTH = 12
        MARKER_SIZE = 13
        ERRORBAR_STYLE = 14
        ERRORBAR_COLOR = 15
        ERRORBAR_WIDTH = 16
        FIT_COLOR = 17
        FIT_LINESTYLE = 18

    color_options_values = {'Blue': '#0000ff', 'Red': '#ff0000', 'Purple': '#9900ff', 'Green': '#009933',
                            'Orange': '#ff9900', 'Maroon': '#800000', 'Pink': '#ff66ff', 'Dark Blue': '#000099',
                            'Dark Green': '#006600', 'Light Blue': '#0099ff', 'Light Purple': '#cc80ff',
                            'Dark Orange': '#ff6600', 'Yellow': '#ffcc00', 'Light Red': '#ff6666',
                            'Light Green': '#00cc66', 'Black': '#000000'}
    color_options = {v: k for k, v in color_options_values.items()}

    color_options_extra_values = {'Default': 'Default', 'Blue': '#0000ff', 'Red': '#ff0000', 'Purple': '#9900ff',
                                  'Orange': '#ff9900', 'Maroon': '#800000', 'Pink': '#ff66ff', 'Dark Blue': '#000099',
                                  'Dark Green': '#006600', 'Light Blue': '#0099ff', 'Light Purple': '#cc80ff',
                                  'Dark Orange': '#ff6600', 'Yellow': '#ffcc00', 'Light Red': '#ff6666',
                                  'Light Green': '#00cc66', 'Green': '#009933', 'Black': '#000000'}

    color_options_extra = {v: k for k, v in color_options_extra_values.items()}

    marker_options_values = {'point': '.', 'triangle_down': 'v', 'triangle_up': '^', 'triangle_left': '<',
                             'triangle_right': '>', 'octagon': '8', 'square': 's', 'pentagon': 'p',
                             'plus': 'P',
                             'star': '*', 'hexagon_1': 'h', 'hexagon_2': 'H', 'x': 'X', 'diamond': 'D',
                             'thin_diamond': 'd'}

    marker_options = {v: k for k, v in marker_options_values.items()}

    linestyle_options_values = {'Solid': '-', 'Dashed': '--', 'Dash-Dot': '-.', 'Dotted': ':', 'None': ''}

    linestyle_options = {v: k for k, v in linestyle_options_values.items()}

    line_width_options_values = {'Very Thin': 1, 'Thin': 2, 'Medium': 3, 'Thick': 4, 'Very Thick': 5}

    line_width_options = {v: k for k, v in line_width_options_values.items()}

    marker_size_options_values = {'Very Thin': 1, 'Thin': 3, 'Medium': 5, 'Thick': 6, 'Very Thick': 9}

    marker_size_options = {v: k for k, v in marker_size_options_values.items()}

    fillstyle_options_values = {'Full': 'full', 'Left': 'left', 'Right': 'right', 'Bottom': 'bottom',
                                'Top': 'top', 'None': 'none'}

    fillstyle_options = {v: k for k, v in fillstyle_options_values.items()}

    errorbar_styles_values = {'Caps': 4, 'No Caps': 0, 'No Bars': 'none'}

    errorbar_styles = {v: k for k, v in errorbar_styles_values.items()}

    errorbar_width_values = {'Very Thin': 1, 'Thin': 2, 'Medium': 3, 'Thick': 4, 'Very Thick': 5}

    errorbar_width = {v: k for k, v in errorbar_width_values.items()}

    _unused_colors = color_options.copy()
    _used_colors = dict()

    _marker_options = {v: k for k, v in marker_options_values.items()}
    _unused_markers = _marker_options.copy()
    _used_markers = dict()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__dao = dao.StyleDAO()
            cls._instance.__logger = logging.getLogger("StyleService")
            cls._instance.signals = StyleService.Signals()
        return cls._instance

    def get_style_by_run_id(self, run_id):
        try:
            return self.__dao.get_styles([run_id])[0]
        except KeyError:
            return None

    def get_visible_styles(self):
        visible_styles = []
        for key, style in self.__dao.get_styles().items():
            if style[self.Keys.VISIBLE]:
                visible_styles.append(style)
        return visible_styles

    def add_style_for_run(self, run, visible=True, error_bars=True):
        if self.get_style_by_run_id(run.id):
            return

        if len(self._unused_markers.keys()) == 0:
            self._unused_markers = self._used_markers.copy()
        marker = list(self._unused_markers.keys())[0]
        self._update_markers(marker, True)

        if len(self._unused_colors.keys()) == 0:
            self._unused_colors = self._used_colors.copy()
        color = list(self._unused_colors.keys())[0]
        self._update_colors(color, True)

        style = dict()
        style[StyleService.Keys.ID] = run.id
        style[StyleService.Keys.LABEL] = run.meta[files.TITLE_KEY]
        style[StyleService.Keys.ERROR_BARS] = error_bars
        style[StyleService.Keys.VISIBLE] = visible
        style[StyleService.Keys.LINE] = 'none'
        style[StyleService.Keys.MARKER] = marker
        style[StyleService.Keys.LINE_COLOR] = 'Default'
        style[StyleService.Keys.MARKER_COLOR] = 'Default'
        style[StyleService.Keys.FILLSTYLE] = 'none'
        style[StyleService.Keys.DEFAULT_COLOR] = color
        style[StyleService.Keys.LINESTYLE] = ''
        style[StyleService.Keys.LINE_WIDTH] = 1
        style[StyleService.Keys.MARKER_SIZE] = 5
        style[StyleService.Keys.ERRORBAR_STYLE] = 0
        style[StyleService.Keys.ERRORBAR_COLOR] = 'Default'
        style[StyleService.Keys.ERRORBAR_WIDTH] = 1
        style[StyleService.Keys.FIT_COLOR] = 'Default'
        style[StyleService.Keys.FIT_LINESTYLE] = '-'

        self.__logger.debug("Style Created for Run ({}) = {}".format(run.id, style))
        self.__dao.add_style(run.id, style)

    def change_color_for_run(self, run_id, color, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        color = StyleService.color_options_values[color]
        if color in StyleService._unused_colors.keys():
            self._update_colors(color, used=True)
        if style[StyleService.Keys.DEFAULT_COLOR] in StyleService._used_colors.keys():
            self._update_colors(style[StyleService.Keys.DEFAULT_COLOR], used=False)
        if style[StyleService.Keys.DEFAULT_COLOR] == color:
            return

        self.__dao.update_style(run_id, StyleService.Keys.DEFAULT_COLOR, color)
        self.__dao.update_style(run_id, StyleService.Keys.LINE_COLOR, 'Default')
        self.__dao.update_style(run_id, StyleService.Keys.ERRORBAR_COLOR, 'Default')
        self.__dao.update_style(run_id, StyleService.Keys.MARKER_COLOR, 'Default')
        self.__dao.update_style(run_id, StyleService.Keys.FIT_COLOR, 'Default')

    def change_marker_for_run(self, run_id, marker, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        marker = StyleService.marker_options_values[marker]
        if marker in StyleService._unused_markers.keys():
            self._update_markers(marker=marker, used=True)

        if style[StyleService.Keys.MARKER] in StyleService._used_markers.keys():
            self._update_markers(marker=style[StyleService.Keys.MARKER], used=False)
        if style[StyleService.Keys.MARKER] == marker:
            return

        self.__dao.update_style(run_id, StyleService.Keys.MARKER, marker)

    def change_visibilities(self, visible, run_id=None, stop_signal=None):
        if run_id is not None:
            for rid in run_id:
                self.__dao.update_style(rid, StyleService.Keys.VISIBLE, visible)
        else:
            self.__dao.update_style(run_id, StyleService.Keys.VISIBLE, visible)

    def change_style_parameter(self, run_ids, key, option_key, stop_signal=None):
        for run_id in run_ids:
            style = self.get_style_by_run_id(run_id)

            if style is None:
                return

            if key == StyleService.Keys.LINESTYLE:
                self.__dao.update_style(run_id, key, StyleService.linestyle_options_values[option_key])
            elif key == StyleService.Keys.FIT_LINESTYLE:
                self.__dao.update_style(run_id, key, StyleService.linestyle_options_values[option_key])
            elif key == StyleService.Keys.ERRORBAR_COLOR or \
                    key == StyleService.Keys.MARKER_COLOR or \
                    key == StyleService.Keys.LINE_COLOR or \
                    key == StyleService.Keys.FIT_COLOR:
                self.__dao.update_style(run_id, key, StyleService.color_options_extra_values[option_key])
            elif key == StyleService.Keys.ERRORBAR_WIDTH:
                self.__dao.update_style(run_id, key, StyleService.errorbar_width_values[option_key])
            elif key == StyleService.Keys.LINE_WIDTH:
                self.__dao.update_style(run_id, key, StyleService.line_width_options_values[option_key])
            elif key == StyleService.Keys.MARKER_SIZE:
                self.__dao.update_style(run_id, key, StyleService.marker_size_options_values[option_key])
            elif key == StyleService.Keys.ERRORBAR_STYLE:
                self.__dao.update_style(run_id, key, StyleService.errorbar_styles_values[option_key])
            elif key == StyleService.Keys.MARKER:
                self.change_marker_for_run(run_id, option_key, True)
            elif key == StyleService.Keys.FILLSTYLE:
                self.__dao.update_style(run_id, key, StyleService.fillstyle_options_values[option_key])
            elif key == StyleService.Keys.DEFAULT_COLOR:
                self.change_color_for_run(run_id, option_key, True)

    def change_label(self, label, run_id, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        style[StyleService.Keys.LABEL] = label

    def get_styles(self):
        return self.__dao.get_styles()

    def _update_markers(self, marker, used):
        if used:
            if marker not in StyleService._used_markers.keys():
                StyleService._used_markers[marker] = StyleService._marker_options[marker]
            if marker in StyleService._unused_markers.keys():
                StyleService._unused_markers.pop(marker)
        else:
            if marker not in StyleService._unused_markers.keys():
                StyleService._unused_markers[marker] = StyleService._marker_options[marker]
            if marker in StyleService._used_markers.keys():
                StyleService._used_markers.pop(marker)
        return True

    def _update_colors(self, color, used):
        if used:
            if color not in StyleService._used_colors.keys():
                StyleService._used_colors[color] = StyleService.color_options[color]
            if color in StyleService._unused_colors.keys():
                StyleService._unused_colors.pop(color)
        else:
            if color not in StyleService._unused_colors.keys():
                StyleService._unused_colors[color] = StyleService.color_options[color]
            if color in StyleService._used_colors.keys():
                StyleService._used_colors.pop(color)
        return True


class SystemService:
    class ConfigKeys:
        LAST_DIRECTORY = "LAST_DIRECTORY"
        USER_FUNCTIONS = "USER-DEFINED_FUNCTIONS"

    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__dao = dao.SystemDAO()
            cls._instance.__logger = logging.getLogger("SystemService")
            cls._instance.signals = SystemService.Signals()
        return cls._instance

    def load_configuration_file(self):
        if not os.path.exists(resources.CONFIGURATION_FILE):
            self._set_default_configuration()

        with open(resources.CONFIGURATION_FILE, 'r') as fp:
            try:
                user_data = json.load(fp)
                self._set_configuration(user_data)
            except json.JSONDecodeError:
                self.__logger.error("Unable to load the configuration file.")
                self._set_default_configuration()

    def write_configuration_file(self):
        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(self.__dao.get_configuration(), f)

    def get_user_defined_functions(self):
        functions = self.__dao.get_configuration(self.ConfigKeys.USER_FUNCTIONS)
        if functions is not None:
            return functions
        else:
            return {}

    def add_user_defined_function(self, name, function):
        functions = self.get_user_defined_functions()
        functions[name] = function

        self.__dao.set_configuration(self.ConfigKeys.USER_FUNCTIONS, functions)

    def get_last_used_directory(self):
        last_directory = self.__dao.get_configuration(self.ConfigKeys.LAST_DIRECTORY)

        if last_directory is not None:
            return last_directory
        else:
            return os.getcwd()

    def set_last_used_directory(self, directory):
        if os.path.exists(directory):
            self.__dao.set_configuration(self.ConfigKeys.LAST_DIRECTORY, directory)
        else:
            self.__logger.warning("Tried to set last used directory to invalid path: {}".format(directory))

    def _set_default_configuration(self):
        user_data = {
            self.ConfigKeys.LAST_DIRECTORY: os.getcwd(),
            self.ConfigKeys.USER_FUNCTIONS: {}
        }
        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(user_data, f)

        for key, value in user_data.items():
            self.__dao.set_configuration(key, value)

    def _set_configuration(self, user_data):
        for key, value in user_data.items():
            self.__dao.set_configuration(key, value)


class FileService:
    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__dao = dao.FileDAO()
            cls._instance.__system_dao = dao.SystemDAO()
            cls._instance.__logger = logging.getLogger("FileService")
            cls._instance.__run_service = RunService()
            cls._instance.__fit_service = FitService()
            cls._instance.__style_service = StyleService()
            cls._instance.__system_service = SystemService()
            cls._instance.signals = FileService.Signals()
        return cls._instance

    def get_files(self, ids=None):
        if ids is not None:
            return self.__dao.get_files_by_ids(ids)
        else:
            return self.__dao.get_files()

    def get_file_by_path(self, path):
        return self.__dao.get_files_by_path(path)

    def convert_files(self, ids):
        new_paths = []
        datasets = self.__dao.get_files_by_ids(ids)
        for dataset in datasets:
            if dataset.file.DATA_FORMAT == files.Format.BINARY:
                temp = os.path.splitext(dataset.file.file_path)[0]
                outfile = temp + ".dat"
                outfile_reader = dataset.file.convert(outfile)
                new_paths.append(outfile_reader.file_path)
                self.__dao.remove_files_by_id(dataset.id)

        self.add_files(new_paths)

    def add_files(self, paths):
        if len(paths) == 0:
            return

        for path in paths:
            if self.__dao.get_files_by_path(path) is not None:
                continue

            f = files.file(path)
            data_set = objects.DataBuilder.build_minimal(f)
            file_set = objects.FileDataset(f)

            if data_set is not None:
                file_set.dataset = data_set
                file_set.title = data_set.meta[files.TITLE_KEY]

                if isinstance(data_set, objects.RunDataset):
                    self.__run_service.add_dataset([data_set], suppress_signal=True)
                else:
                    self.__fit_service.add_dataset([data_set], suppress_signal=True)

            self.__dao.add_files([file_set])

        self.signals.changed.emit()

    def load_files(self, ids):
        is_changed = False

        for file_dataset in self.__dao.get_files_by_ids(ids):
            if not file_dataset.isLoaded:
                is_changed = True
                objects.DataBuilder.build_full(file_dataset.file, file_dataset.dataset)
                file_dataset.isLoaded = True

        if is_changed:
            self.signals.changed.emit()
            self.__run_service.changed()
            self.__fit_service.changed()

    def remove_files(self, checked_items):
        run_files = self.__dao.get_files_by_ids(checked_items)
        run_ids = []
        for rf in run_files:
            if rf.isLoaded:
                run_ids.append(rf.dataset.id)
            self.__dao.remove_files_by_id(rf.id)

        self.__run_service.remove_runs_by_ids(run_ids)
        self.signals.changed.emit()

    def save_session(self, save_path):
        if not os.path.splitext(save_path)[-1] == '.beams':
            raise RuntimeError("Session file needs to have a .beams extension.")

        with open(save_path, 'wb') as session_file_object:
            pickle.dump(self.__system_dao.get_database(), session_file_object)

        self.add_files([save_path])

    def load_session(self, file_id):
        file_dataset = self.__dao.get_files_by_ids([file_id])

        if len(file_dataset) == 0:
            raise RuntimeError("No file dataset exists for id.")

        file_dataset = file_dataset[0]

        if file_dataset.file.DATA_FORMAT != files.Format.PICKLED:
            raise RuntimeError("File was not of correct format for session file (should be a pickle file).")

        database = file_dataset.file.read_data()

        if not isinstance(database, dao.Database):
            raise RuntimeError("Unpickling file did not result in a Database object.")

        self.__system_dao.set_database(database)

        print(self.signals.receivers(self.signals.changed), 'receivers')
        self.signals.changed.emit()
        self.__fit_service.signals.added.emit()
        self.__run_service.signals.added.emit()
        self.__run_service.signals.loaded.emit()
        self.__run_service.signals.changed.emit()
        self.__system_service.signals.changed.emit()
        self.__style_service.signals.changed.emit()
