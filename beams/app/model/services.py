import enum
import json
import os
import logging
import pickle

from PyQt5 import QtCore

import app.model.data_access as dao
from app.model import domain, files
from app.resources import resources


class FitService:
    class Signals(QtCore.QObject):
        added = QtCore.pyqtSignal()
        changed = QtCore.pyqtSignal()

    __dao = dao.FitDAO()
    __logger = logging.getLogger('FitService')
    signals = Signals()

    @staticmethod
    def get_fit_datasets():
        return FitService.__dao.get_fits()

    @staticmethod
    def add_dataset(datasets, suppress_signal=False):
        FitService.__dao.add_fits(datasets)

        if not suppress_signal:
            FitService.__logger.debug("Emitted: added")
            FitService.signals.added.emit()

    @staticmethod
    def remove_dataset(ids):
        FitService.__dao.remove_fits_by_ids(ids)
        FitService.__logger.debug("Emitted: changed")
        FitService.signals.changed.emit()

    @staticmethod
    def remove_fits_from_datasets(id_mappings):
        raise NotImplementedError()

    @staticmethod
    def changed():
        FitService.__logger.debug("Emitted: changed")
        FitService.signals.changed.emit()


class RunService:
    class Signals(QtCore.QObject):
        added = QtCore.pyqtSignal()
        changed = QtCore.pyqtSignal()
        loaded = QtCore.pyqtSignal()

    signals = Signals()
    __dao = dao.RunDAO()
    __logger = logging.getLogger("RunService")

    @staticmethod
    def get_runs():
        return RunService.__dao.get_runs()

    @staticmethod
    def get_runs_by_ids(ids):
        return RunService.__dao.get_runs_by_ids(ids)

    @staticmethod
    def get_loaded_runs():
        loaded_runs = []
        for run in RunService.__dao.get_runs():
            if run.isLoaded:
                loaded_runs.append(run)
        return loaded_runs

    def load_runs(self, ids):
        pass

    def combine_histograms(self, ids, titles):
        pass

    @staticmethod
    def recalculate_asymmetries(ids):
        for run in RunService.__dao.get_runs_by_ids(ids):
            if len(run.histograms_used) == 2:
                run.asymmetries[domain.RunDataset.FULL_ASYMMETRY] = domain.Asymmetry(
                    histogram_one=run.histograms[run.histograms_used[0]],
                    histogram_two=run.histograms[run.histograms_used[1]],
                    alpha=run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].alpha)

                if run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                    run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                    run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                        run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()

    @staticmethod
    def add_runs(paths):
        builder = domain.DataBuilder()
        for path in paths:
            run = builder.build_minimal(path)
            RunService.__dao.add_runs([run])

        RunService.__logger.debug("Emitted: added")
        RunService.signals.added.emit()

    @staticmethod
    def remove_runs_by_ids(ids):
        RunService.__dao.remove_runs_by_ids(ids)

        RunService.__logger.debug("Emitted: loaded")
        RunService.signals.loaded.emit()

    @staticmethod
    def add_dataset(datasets, suppress_signal):
        RunService.__dao.add_runs(datasets)

        if not suppress_signal:
            RunService.__logger.debug("Emitted: added")
            RunService.signals.added.emit()

    @staticmethod
    def update_runs_by_ids(ids, asymmetries):
        RunService.__dao.update_runs_by_id(ids, asymmetries)
        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()

    @staticmethod
    def update_alphas(ids, alphas):
        if len(alphas) == 1:  # When we update alpha from plotting panel we send one alpha for multiple runs
            alpha = alphas[0]
            alphas = [alpha for _ in ids]

        for rid, alpha in zip(ids, alphas):
            run = RunService.__dao.get_runs_by_ids([rid])[0]

            run.asymmetries[domain.RunDataset.FULL_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].correct(alpha)

            if run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[domain.RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[domain.RunDataset.FULL_ASYMMETRY].bin(
                    run.asymmetries[domain.RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()

    @staticmethod
    def changed():
        RunService.__logger.debug("Emitted: changed")
        RunService.signals.changed.emit()


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

    signals = Signals()

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

    __dao = dao.StyleDAO()
    __logger = logging.getLogger("StyleService")

    @staticmethod
    def get_style_by_run_id(run_id):
        try:
            return StyleService.__dao.get_styles([run_id])[0]
        except KeyError:
            StyleService.__logger.warning("Style for {} not found. Key Error.".format(run_id))
            return None

    @staticmethod
    def get_visible_styles():
        visible_styles = []
        for key, style in StyleService.__dao.get_styles().items():
            if style[StyleService.Keys.VISIBLE]:
                visible_styles.append(style)
        return visible_styles

    @staticmethod
    def add_style_for_run(run, visible=True, error_bars=True):
        if StyleService.get_style_by_run_id(run.id):
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

        StyleService.__dao.add_style(run.id, style)

    @staticmethod
    def change_color_for_run(run_id, color, stop_signal=None):
        style = StyleService.get_style_by_run_id(run_id)
        color = StyleService.color_options_values[color]
        if color in StyleService._unused_colors.keys():
            StyleService._update_colors(color, used=True)
        if style[StyleService.Keys.DEFAULT_COLOR] in StyleService._used_colors.keys():
            StyleService._update_colors(style[StyleService.Keys.DEFAULT_COLOR], used=False)
        if style[StyleService.Keys.DEFAULT_COLOR] == color:
            return

        StyleService.__dao.update_style(run_id, StyleService.Keys.DEFAULT_COLOR, color)
        StyleService.__dao.update_style(run_id, StyleService.Keys.LINE_COLOR, 'Default')
        StyleService.__dao.update_style(run_id, StyleService.Keys.ERRORBAR_COLOR, 'Default')
        StyleService.__dao.update_style(run_id, StyleService.Keys.MARKER_COLOR, 'Default')
        StyleService.__dao.update_style(run_id, StyleService.Keys.FIT_COLOR, 'Default')

    @staticmethod
    def change_marker_for_run(run_id, marker, stop_signal=None):
        style = StyleService.get_style_by_run_id(run_id)
        marker = StyleService.marker_options_values[marker]
        if marker in StyleService._unused_markers.keys():
            StyleService._update_markers(marker=marker, used=True)

        if style[StyleService.Keys.MARKER] in StyleService._used_markers.keys():
            StyleService._update_markers(marker=style[StyleService.Keys.MARKER], used=False)
        if style[StyleService.Keys.MARKER] == marker:
            return

        StyleService.__dao.update_style(run_id, StyleService.Keys.MARKER, marker)

    @staticmethod
    def change_visibilities(visible, run_id=None, stop_signal=None):
        if run_id is not None:
            for rid in run_id:
                StyleService.__dao.update_style(rid, StyleService.Keys.VISIBLE, visible)
        else:
            StyleService.__dao.update_style(run_id, StyleService.Keys.VISIBLE, visible)

    @staticmethod
    def change_style_parameter(run_ids, key, option_key, stop_signal=None):
        for run_id in run_ids:
            style = StyleService.get_style_by_run_id(run_id)

            if style is None:
                return

            if key == StyleService.Keys.LINESTYLE:
                StyleService.__dao.update_style(run_id, key, StyleService.linestyle_options_values[option_key])
            elif key == StyleService.Keys.FIT_LINESTYLE:
                StyleService.__dao.update_style(run_id, key, StyleService.linestyle_options_values[option_key])
            elif key == StyleService.Keys.ERRORBAR_COLOR or \
                    key == StyleService.Keys.MARKER_COLOR or \
                    key == StyleService.Keys.LINE_COLOR or \
                    key == StyleService.Keys.FIT_COLOR:
                StyleService.__dao.update_style(run_id, key, StyleService.color_options_extra_values[option_key])
            elif key == StyleService.Keys.ERRORBAR_WIDTH:
                StyleService.__dao.update_style(run_id, key, StyleService.errorbar_width_values[option_key])
            elif key == StyleService.Keys.LINE_WIDTH:
                StyleService.__dao.update_style(run_id, key, StyleService.line_width_options_values[option_key])
            elif key == StyleService.Keys.MARKER_SIZE:
                StyleService.__dao.update_style(run_id, key, StyleService.marker_size_options_values[option_key])
            elif key == StyleService.Keys.ERRORBAR_STYLE:
                StyleService.__dao.update_style(run_id, key, StyleService.errorbar_styles_values[option_key])
            elif key == StyleService.Keys.MARKER:
                StyleService.change_marker_for_run(run_id, option_key, True)
            elif key == StyleService.Keys.FILLSTYLE:
                StyleService.__dao.update_style(run_id, key, StyleService.fillstyle_options_values[option_key])
            elif key == StyleService.Keys.DEFAULT_COLOR:
                StyleService.change_color_for_run(run_id, option_key, True)

    @staticmethod
    def change_label(label, run_id, stop_signal=None):
        style = StyleService.get_style_by_run_id(run_id)
        style[StyleService.Keys.LABEL] = label

    @staticmethod
    def get_styles():
        return StyleService.__dao.get_styles()

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

    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    __dao = dao.SystemDAO()
    __logger = logging.getLogger("SystemService")

    signals = Signals()

    @staticmethod
    def load_configuration_file():
        if not os.path.exists(resources.CONFIGURATION_FILE):
            SystemService._set_default_configuration()

        with open(resources.CONFIGURATION_FILE, 'r') as fp:
            try:
                user_data = json.load(fp)
                SystemService._set_configuration(user_data)
            except json.JSONDecodeError:
                SystemService.__logger.error("Unable to load the configuration file.")
                SystemService._set_default_configuration()

    @staticmethod
    def write_configuration_file():
        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(SystemService.__dao.get_configuration(), f)

    @staticmethod
    def get_user_defined_functions():
        functions = SystemService.__dao.get_configuration(SystemService.ConfigKeys.USER_FUNCTIONS)
        if functions is not None:
            return functions
        else:
            return {}

    @staticmethod
    def add_user_defined_function(name, function):
        functions = SystemService.get_user_defined_functions()
        functions[name] = function

        SystemService.__dao.set_configuration(SystemService.ConfigKeys.USER_FUNCTIONS, functions)

    @staticmethod
    def get_last_used_directory():
        last_directory = SystemService.__dao.get_configuration(SystemService.ConfigKeys.LAST_DIRECTORY)

        if last_directory is not None:
            return last_directory
        else:
            return os.getcwd()

    @staticmethod
    def set_last_used_directory(directory):
        if os.path.exists(directory):
            SystemService.__dao.set_configuration(SystemService.ConfigKeys.LAST_DIRECTORY, directory)
        else:
            SystemService.__logger.warning("Tried to set last used directory to invalid path: {}".format(directory))

    @staticmethod
    def _set_default_configuration():
        user_data = {
            SystemService.ConfigKeys.LAST_DIRECTORY: os.getcwd(),
            SystemService.ConfigKeys.USER_FUNCTIONS: {}
        }
        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(user_data, f)

        for key, value in user_data.items():
            SystemService.__dao.set_configuration(key, value)

    @staticmethod
    def _set_configuration(user_data):
        for key, value in user_data.items():
            SystemService.__dao.set_configuration(key, value)


class FileService:
    class Signals(QtCore.QObject):
        changed = QtCore.pyqtSignal()

    __dao = dao.FileDAO()
    __system_dao = dao.SystemDAO()
    __logger = logging.getLogger("FileService")
    __run_service = RunService()
    __fit_service = FitService()
    __style_service = StyleService()
    __system_service = SystemService()

    signals = Signals()

    @staticmethod
    def get_files(ids=None):
        if ids is not None:
            return FileService.__dao.get_files_by_ids(ids)
        else:
            return FileService.__dao.get_files()

    @staticmethod
    def convert_files(ids):
        new_paths = []
        datasets = FileService.__dao.get_files_by_ids(ids)
        for dataset in datasets:
            if dataset.file.DATA_FORMAT == files.Format.BINARY:
                temp = os.path.splitext(dataset.file.file_path)[0]
                outfile = temp + ".dat"
                outfile_reader = dataset.file.convert(outfile)
                new_paths.append(outfile_reader.file_path)
                FileService.__dao.remove_files_by_id(dataset.id)

        FileService.add_files(new_paths)

    @staticmethod
    def add_files(paths):
        if len(paths) == 0:
            return

        for path in paths:
            if FileService.__dao.get_files_by_path(path) is not None:
                continue

            f = files.file(path)
            data_set = domain.DataBuilder.build_minimal(f)
            file_set = domain.FileDataset(f)

            if data_set is not None:
                file_set.dataset = data_set
                file_set.title = data_set.meta[files.TITLE_KEY]

                if isinstance(data_set, domain.RunDataset):
                    FileService.__run_service.add_dataset([data_set], suppress_signal=True)
                else:
                    FileService.__fit_service.add_dataset([data_set], suppress_signal=True)

            FileService.__dao.add_files([file_set])

        FileService.__logger.debug("Emitted: changed")
        FileService.signals.changed.emit()

    @staticmethod
    def load_files(ids):
        is_changed = False

        for file_dataset in FileService.__dao.get_files_by_ids(ids):
            if not file_dataset.isLoaded:
                is_changed = True
                domain.DataBuilder.build_full(file_dataset.file, file_dataset.dataset)
                file_dataset.isLoaded = True

        if is_changed:
            FileService.__logger.debug("Emitted: changed")
            FileService.signals.changed.emit()
            FileService.__run_service.changed()
            FileService.__fit_service.changed()

    @staticmethod
    def remove_files(checked_items):
        run_files = FileService.__dao.get_files_by_ids(checked_items)
        run_ids = []
        for rf in run_files:
            if rf.isLoaded:
                run_ids.append(rf.dataset.id)
            FileService.__dao.remove_files_by_id(rf.id)

        FileService.__run_service.remove_runs_by_ids(run_ids)
        FileService.__logger.debug("Emitted: changed")
        FileService.signals.changed.emit()

    @staticmethod
    def save_session(save_path):
        if not os.path.splitext(save_path)[-1] == '.beams':
            raise RuntimeError("Session file needs to have a .beams extension.")

        with open(save_path, 'wb') as session_file_object:
            # pickled = pickle.dumps(FileService.__system_dao.get_database())
            pickle.dump(FileService.__system_dao.get_database(), session_file_object)

        FileService.add_files([save_path])

    @staticmethod
    def load_session(file_id):
        file_dataset = FileService.__dao.get_files_by_ids([file_id])

        if len(file_dataset) == 0:
            raise RuntimeError("No file dataset exists for id.")

        file_dataset = file_dataset[0]

        if file_dataset.file.DATA_FORMAT != files.Format.PICKLED:
            raise RuntimeError("File was not of correct format for session file (should be a pickle file).")

        database = file_dataset.file.read_data()

        if not isinstance(database, dao.Database):
            raise RuntimeError("Unpickling file did not result in a Database object.")

        FileService.__system_dao.set_database(database)

        FileService.signals.changed.emit()
        FileService.__fit_service.signals.added.emit()
        FileService.__run_service.signals.added.emit()
        FileService.__run_service.signals.loaded.emit()
        FileService.__system_service.signals.changed.emit()
        FileService.__style_service.signals.changed.emit()
