import enum
import json
import os
import logging
import pickle
import re
from collections.abc import Sequence, Iterable
import gzip

from PyQt5 import QtCore

import app.model.data_access as dao
from app.model import objects, files, api
from app.resources import resources
from app.util import report


class Service:
    def __init__(self):
        self.__observers = {}

    def register(self, observer, signal):
        self.__observers[signal] = [observer] if signal not in self.__observers.keys() else self.__observers[
            signal].append(observer)

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
            cls._instance.__logger = logging.getLogger(__name__)
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
            cls._instance.__logger = logging.getLogger(__name__)
            cls._instance.signals = RunService.Signals()
            cls._instance._system_service = SystemService()
        return cls._instance

    def get_runs(self):
        return self.__dao.get_runs()

    def get_runs_by_ids(self, ids):
        return self.__dao.get_runs_by_ids(ids)

    def get_runs_by_numbers(self, numbers):
        return self.__dao.get_runs_by_numbers(numbers)

    def get_loaded_runs(self):
        loaded_runs = []
        for run in self.__dao.get_runs():
            if run.is_loaded:
                loaded_runs.append(run)
        return loaded_runs

    def recalculate_asymmetries(self, ids):
        report.log_debug("Updated Asymmetry for Runs=({})".format(str(ids)))
        for run in self.__dao.get_runs_by_ids(ids):
            if len(run.histograms_used) == 2:
                run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] = objects.Asymmetry(
                    histogram_one=run.histograms[run.histograms_used[0]],
                    histogram_two=run.histograms[run.histograms_used[1]],
                    alpha=run.asymmetries[objects.RunDataset.FULL_ASYMMETRY].alpha)

                if run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                    run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[
                        objects.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                    run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[
                        objects.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        self.signals.changed.emit()

    def integrate_asymmetries(self, ids, independent_variable_key):
        """ Gets the runs with the given ids and integrates the asymmetries as they are currently binned on the left
        and right.

        RETURNS
        -------
        integrations : dict[str, Sequence[float]]
            Two arrays of floats, one for the asymmetries binned on the left, on for the ones on the right.

        """

        runs = [(r, float(re.search("[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?",
                                    r.meta[independent_variable_key])[0]))
                for r in self.get_runs_by_ids(ids)]

        runs.sort(key=lambda r: r[1])

        if independent_variable_key == files.RUN_NUMBER_KEY:
            runs = [(r, int(f)) for r, f in runs]

        left_integrations = []
        left_uncertainties = []
        right_integrations = []
        right_uncertainties = []

        for run, _ in runs:
            if run.asymmetries[run.LEFT_BINNED_ASYMMETRY] is None or \
                    run.asymmetries[run.RIGHT_BINNED_ASYMMETRY] is None:
                raise Exception("Asymmetries have not been calculated for runs selected to integrate.")

            integration, uncertainty = run.asymmetries[run.LEFT_BINNED_ASYMMETRY].integrate()
            left_integrations.append(integration)
            left_uncertainties.append(uncertainty)

            integration, uncertainty = run.asymmetries[run.RIGHT_BINNED_ASYMMETRY].integrate()
            right_integrations.append(integration)
            right_uncertainties.append(uncertainty)

        return {
            independent_variable_key: [i for _, i in runs],
            objects.RunDataset.LEFT_BINNED_ASYMMETRY: (left_integrations, left_uncertainties),
            objects.RunDataset.RIGHT_BINNED_ASYMMETRY: (right_integrations, right_uncertainties)
        }

    def add_runs(self, paths):
        builder = objects.DataBuilder()
        for path in paths:
            run = builder.build_minimal(path)
            self.__dao.add_runs([run])

        self.signals.added.emit()

    def remove_runs_by_ids(self, ids):
        report.log_debug("Removing Run Datasets=({})".format(str(ids)))
        self.__dao.remove_runs_by_ids(ids)

        self.signals.loaded.emit()

    def add_dataset(self, datasets, suppress_signal):
        report.log_debug("Adding Run Datasets=({})".format(str(datasets)))
        self.__dao.add_runs(datasets)

        if not suppress_signal:
            self.signals.added.emit()

    def update_alphas(self, ids, alphas):
        report.log_debug("Updating Alphas for Runs=({}) with Alphas=({})".format(str(ids), str(alphas)))
        if len(alphas) == 1:  # When we update alpha from plotting panel we send one alpha for multiple runs
            alpha = alphas[0]
            alphas = [alpha for _ in ids]

        for rid, alpha in zip(ids, alphas):
            run = self.__dao.get_runs_by_ids([rid])[0]

            run.asymmetries[objects.RunDataset.FULL_ASYMMETRY] = run.asymmetries[
                objects.RunDataset.FULL_ASYMMETRY].correct(alpha)

            if run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[
                    objects.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[objects.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[
                    objects.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[objects.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        self.signals.changed.emit()

    def changed(self):
        self.signals.changed.emit()

    def add_run_from_histograms(self, histograms, meta):
        run = objects.RunDataset()

        for hist in histograms.values():
            hist.id = run.id

        run.histograms = histograms
        run.meta = meta
        run.is_loaded = True
        self.__dao.add_runs([run])
        self.signals.added.emit()
        return run

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

    color_options_values = {'Blue': '#5050EC', 'Red': '#ff0000', 'Purple': '#9900ff', 'Green': '#009933',
                            'Orange': '#ff9900', 'Maroon': '#800000', 'Pink': '#ff66ff',
                            'Dark Green': '#006600', 'Light Blue': '#0099ff', 'Light Purple': '#cc80ff',
                            'Dark Orange': '#ff6600', 'Yellow': '#ffcc00', 'Light Red': '#ff6666',
                            'Light Green': '#00cc66', 'Black': '#000000'}
    color_options = {v: k for k, v in color_options_values.items()}

    color_options_extra_values = {'Default': 'Default', 'Blue': '#5050EC', 'Red': '#ff0000', 'Purple': '#9900ff',
                                  'Orange': '#ff9900', 'Maroon': '#800000', 'Pink': '#ff66ff',
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
            cls._instance.__logger = logging.getLogger(__name__)
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

        if len(StyleService._unused_markers.keys()) == 0:
            StyleService._unused_markers = StyleService._used_markers.copy()
        marker = list(StyleService._unused_markers.keys())[0]
        StyleService._update_markers(marker, True)

        if len(StyleService._unused_colors.keys()) == 0:
            StyleService._unused_colors = StyleService._used_colors.copy()
        color = list(StyleService._unused_colors.keys())[0]
        StyleService._update_colors(color, True)

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

        report.log_debug("Style Created for Run ({}) = {}".format(run.id, style))
        self.__dao.add_style(run.id, style)

    def change_color_for_run(self, run_id, color, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        color = StyleService.color_options_values[color]
        if color in StyleService._unused_colors.keys():
            StyleService._update_colors(color, used=True)
        if style[StyleService.Keys.DEFAULT_COLOR] in StyleService._used_colors.keys():
            StyleService._update_colors(style[StyleService.Keys.DEFAULT_COLOR], used=False)
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
            StyleService._update_markers(marker=marker, used=True)

        if style[StyleService.Keys.MARKER] in StyleService._used_markers.keys():
            StyleService._update_markers(marker=style[StyleService.Keys.MARKER], used=False)
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

    @staticmethod
    def _update_markers(marker, used):
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

    @staticmethod
    def _update_colors(color, used):
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
        THEME_PREFERENCE = "THEME_PREFERENCE"
        VERSION = "VERSION"
        LATEST = "LATEST"
        NOTIFY_OF_UPDATE = "NOTIFY_OF_UPDATE"

    class Themes:
        DARK = "DARK"
        LIGHT = "LIGHT"
        DEFAULT = "DEFAULT"

    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()
        theme_changed = QtCore.pyqtSignal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__dao = dao.SystemDAO()
            cls._instance.__logger = logging.getLogger(__name__)
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
                report.log_info("Unable to load the configuration file.")
                self._set_default_configuration()

    def write_configuration_file(self):
        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(self.__dao.get_configuration(), f, indent=2)

    def get_user_defined_functions(self):
        try:
            functions = self.__dao.get_configuration(self.ConfigKeys.USER_FUNCTIONS)
        except dao.BeamsRequestedDataNotInDatabaseError:
            functions = None

        if functions is not None:
            return functions
        else:
            self.__dao.set_configuration(self.ConfigKeys.USER_FUNCTIONS, {})
            return {}

    def add_user_defined_function(self, name, function):
        functions = self.get_user_defined_functions()
        functions[name] = function

        self.__dao.set_configuration(self.ConfigKeys.USER_FUNCTIONS, functions)

    def get_last_used_directory(self):
        try:
            last_directory = self.__dao.get_configuration(self.ConfigKeys.LAST_DIRECTORY)
        except dao.BeamsRequestedDataNotInDatabaseError:
            last_directory = None

        if last_directory is not None:
            return last_directory
        else:
            return os.getcwd()

    def set_last_used_directory(self, directory):
        if os.path.exists(directory):
            self.__dao.set_configuration(self.ConfigKeys.LAST_DIRECTORY, directory)
        else:
            self.__logger.warning("Tried to set last used directory to invalid path: {}".format(directory))

    def get_theme_preference(self):
        try:
            preference = self.__dao.get_configuration(self.ConfigKeys.THEME_PREFERENCE)
        except dao.BeamsRequestedDataNotInDatabaseError:
            preference = None

        if preference is None:
            preference = self.Themes.DEFAULT
            self.set_theme_preference(preference)
        return preference

    def set_theme_preference(self, preference):
        self.__dao.set_configuration(self.ConfigKeys.THEME_PREFERENCE, preference)
        self.signals.theme_changed.emit()

    def get_current_version(self):
        try:
            return self.__dao.get_configuration(self.ConfigKeys.VERSION)
        except dao.BeamsRequestedDataNotInDatabaseError:
            self.__dao.set_configuration(self.ConfigKeys.VERSION, "unknown")
            return "unknown"

    def get_latest_version(self):
        try:
            latest_old = self.__dao.get_configuration(self.ConfigKeys.LATEST)
        except dao.BeamsRequestedDataNotInDatabaseError:
            latest_old = "unknown"

        try:
            latest_version = api.get_latest_release_version()
            latest_version = latest_version if latest_version else "unknown"
        except api.BeamsNetworkError:
            latest_version = "unknown"

        if latest_old != latest_version:
            self.__dao.set_configuration(self.ConfigKeys.LATEST, latest_version)

        return latest_old, latest_version

    def get_notify_user_of_update(self):
        try:
            notify = self.__dao.get_configuration(self.ConfigKeys.NOTIFY_OF_UPDATE)
        except dao.BeamsRequestedDataNotInDatabaseError:
            notify = True

        version = self.get_current_version()
        latest_old, latest = self.get_latest_version()

        # We want to notify if the latest version of beams does not match the current version AND the user
        # wants to be notified of this OR a new release has been made since they last silenced the notification
        notify = latest != version and (notify or latest_old != latest)

        self.__dao.set_configuration(self.ConfigKeys.NOTIFY_OF_UPDATE, notify)
        return notify

    def set_notify_user_of_update(self, notify):
        self.__dao.set_configuration(self.ConfigKeys.NOTIFY_OF_UPDATE, notify)

    def _set_default_configuration(self):
        user_data = {
            self.ConfigKeys.LAST_DIRECTORY: os.getcwd(),
            self.ConfigKeys.USER_FUNCTIONS: {},
            self.ConfigKeys.THEME_PREFERENCE: self.Themes.DEFAULT,
            self.ConfigKeys.VERSION: "unknown",
            self.ConfigKeys.LATEST: "unknown",
            self.ConfigKeys.NOTIFY_OF_UPDATE: True
        }

        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(user_data, f, indent=2)

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
            cls._instance.__logger = logging.getLogger(__name__)
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

    def add_files(self, paths, loaded_data=None):
        if len(paths) == 0:
            return

        file_sets = []
        for path in paths:
            if self.__dao.get_files_by_path(path) is not None:
                continue

            try:
                f = files.file(path)
                data_set = loaded_data if loaded_data else objects.DataBuilder.build_minimal(f)
            except files.BeamsFileReadError:
                f = files.UnknownFile(file_path=path)
                data_set = None

            file_set = objects.FileDataset(f)
            file_set.dataset = data_set

            if loaded_data:
                file_set.title = loaded_data.meta[files.TITLE_KEY]
                file_set.is_loaded = True

            file_sets.append(file_set)
            if data_set and loaded_data is None:
                try:
                    file_set.title = data_set.meta[files.TITLE_KEY]
                except AttributeError:
                    file_set.title = os.path.split(path)[-1]

                if isinstance(data_set, objects.RunDataset):
                    self.__run_service.add_dataset([data_set], suppress_signal=True)
                elif isinstance(data_set, objects.FitDataset):
                    self.__fit_service.add_dataset([data_set])

            self.__dao.add_files([file_set])
        self.signals.changed.emit()

        return file_sets

    def load_files(self, ids):
        is_changed = False

        for file_dataset in self.__dao.get_files_by_ids(ids):
            if not file_dataset.is_loaded:
                is_changed = True
                try:
                    objects.DataBuilder.build_full(file_dataset.file, file_dataset.dataset)
                except ValueError as e:
                    raise files.BeamsFileReadError("File was not correctly formatted.")
                file_dataset.is_loaded = True

        if is_changed:
            self.signals.changed.emit()
            self.__run_service.changed()
            self.__fit_service.changed()

    def remove_files(self, checked_items):
        file_datasets = self.__dao.get_files_by_ids(checked_items)

        fit_datasets = []
        run_datasets = []

        for fd in file_datasets:
            if fd.dataset is None:
                pass
            elif isinstance(fd.dataset, objects.FitDataset):
                fit_datasets.append(fd.dataset.id)
            elif isinstance(fd.dataset, objects.RunDataset):
                run_datasets.append(fd.dataset.id)
            else:
                raise Exception("This file dataset ({}) is not recognized.".format(type(fd.dataset)))

            self.__dao.remove_files_by_id(fd.id)

        self.__run_service.remove_runs_by_ids(run_datasets)
        self.__fit_service.remove_dataset(fit_datasets)

        self.signals.changed.emit()

    def save_session(self, save_path):
        if not os.path.splitext(save_path)[-1] == '.beams':
            raise RuntimeError("Session file needs to have a .beams extension.")

        with gzip.GzipFile(save_path, 'wb') as session_file_object:
            pickle.dump(self.__system_dao.get_database(), session_file_object)

        self.add_files([save_path])

    def load_session(self, file_id):
        file_dataset = self.__dao.get_files_by_ids([file_id])

        if len(file_dataset) == 0:
            raise RuntimeError("No file dataset exists for id.")

        file_dataset = file_dataset[0]
        if file_dataset.file.DATA_FORMAT != files.Format.PICKLED:
            raise files.BeamsFileReadError("File was not of correct format for session file.")

        database = file_dataset.file.read_data()

# We will add this back after we merge, but a little different. Right now this check no longer makes sense with my recent changes.
#         if not isinstance(database, dao.Database):
#             error = "Unpickling file did not result in a Database object."
#             raise files.BeamsFileReadError(error)

        self.__system_dao.set_database(database)

        self.signals.changed.emit()
        self.__fit_service.signals.added.emit()
        self.__run_service.signals.added.emit()
        self.__run_service.signals.loaded.emit()
        self.__run_service.signals.changed.emit()
        self.__system_service.signals.changed.emit()
        self.__style_service.signals.changed.emit()
