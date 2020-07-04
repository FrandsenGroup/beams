
from enum import Enum

from app.model import muon, files, mufyt


class MuonDataContext:
    """
    A model object that acts purely as data storage and access object.
    """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.notifier = Notifier()
            self.runs = []

    __instance = None

    def __init__(self):
        if not MuonDataContext.__instance:
            MuonDataContext.__instance = MuonDataContext.__DataStore()

    def get_runs(self):
        return self.__instance.runs

    def get_run_by_filename(self, filename):
        """
        Gets a Run object associated with the given filename.
        :param filename: full file path associated with a run
        :return run:
        """
        for run in self.__instance.runs:
            if run.file == filename:
                return run

    def remove_runs_by_filename(self, filenames, stop_signal=None):
        """
        Removes a Run object associated with the given filename.
        :param filenames: array of full file paths associated with a run
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        for filename in filenames:
            for run in self.__instance.runs:
                if run.file == filename:
                    self.__instance.runs.remove(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_run_by_id(self, run_id):
        """
        Gets a Run object with the specified ID.
        :param run_id: ID of a run
        :return run:
        """

        for run in self.__instance.runs:
            if run.id == run_id:
                return run

    def remove_runs_by_id(self, run_ids, stop_signal=None):
        """
        Removes a Run object with the specified ID
        :param run_ids: array of IDs of runs
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        for run_id in run_ids:
            for run in self.__instance.runs:
                if run.file == run_id:
                    self.__instance.runs.remove(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_loaded_run_files(self):
        return [run.file for run in self.__instance.runs]

    def reload_run_by_id(self, run_id, stop_signal=None):
        run = self.get_run_by_id(run_id)
        reader = files.file(run.file)

        if reader.DATA_FORMAT == files.Format.ASYMMETRY:
            new_run = muon.build_muon_run_from_asymmetry_file(run.file, run.meta)
        elif reader.DATA_FORMAT == files.Format.HISTOGRAM:
            new_run = muon.build_muon_run_from_histogram_file(run.file, run.meta)
        else:
            return

        new_run.id = run.id
        for i, run2 in enumerate(self.__instance.runs):
            if run2.id == run.id:
                self.__instance.runs[i] = new_run

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_run_id_by_filename(self, filenames):
        run_ids = []
        for filename in filenames:
            for run in self.__instance.runs:
                if run.file == filename:
                    run_ids.append(run.id)
        return run_ids

    def add_run(self, run, stop_signal=None):
        """
        Adds a Run object to the data store.
        :param run:
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        self.__instance.runs.append(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_runs(self, runs, stop_signal=None):
        """
        Adds an array of run objects to the data store.
        :param runs: array of runs
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        self.__instance.runs.extend(runs)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_run_from_histogram_file(self, histogram_file, meta=None, stop_signal=None):
        run = muon.build_muon_run_from_histogram_file(histogram_file, meta=meta)
        self.__instance.runs.append(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_run_from_asymmetry_file(self, asymmetry_file, meta=None, stop_signal=None):
        run = muon.build_muon_run_from_asymmetry_file(asymmetry_file, meta=meta)
        self.__instance.runs.append(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def clear_runs(self, stop_signal=None):
        """
        Clears all runs in the data store.
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        self.__instance.runs = []

        if not stop_signal:
            self.__instance.notifier.notify()

    def apply_correction_to_runs_by_id(self, run_ids, alpha, beta=None, stop_signal=None):
        for run_id in run_ids:
            run = self.get_run_by_id(run_id)
            muon.correct_muon_asymmetry(run, alpha, beta)

        if not stop_signal:
            self.__instance.notifier.notify()

    def set_fit_data_for_runs(self, run_ids, expression, independent_variable, variables, refine, stop_signal=None):
        for run_id in run_ids:
            new_fit = mufyt.Fit()
            new_fit.expression = expression
            new_fit.independent_variable = independent_variable
            new_fit.free_variables = variables
            new_fit.is_fitted = True
            new_fit.refine = refine

            run = self.get_run_by_id(run_id)
            run.fit = new_fit

        if not stop_signal:
            self.__instance.notifier.notify()

    def send_signal(self):
        self.__instance.notifier.notify()

    @staticmethod
    def subscribe(observer):
        MuonDataContext.__instance.notifier.subscribe(observer)


class FileContext:
    """
        A model object that acts purely as data storage and access object.
        """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.notifier = Notifier()
            self.files = set()

    __instance = None

    def __init__(self):
        if FileContext.__instance is None:
            FileContext.__instance = FileContext.__DataStore()

    def add_files(self, new_files, stop_signal=None):
        self.__instance.files.update(new_files)

        if not stop_signal:
            self.__instance.notifier.notify()

    def remove_files(self, files, stop_signal=None):
        self.__instance.files.difference_update(files)

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_files(self):
        return self.__instance.files

    @staticmethod
    def subscribe(observer):
        FileContext.__instance.notifier.subscribe(observer)


class PlotContext:
    """
    A model object that acts purely as data storage and access object.
    https://matplotlib.org/gallery/lines_bars_and_markers/line_styles_reference.html
    https://matplotlib.org/3.2.1/api/markers_api.html
    https://matplotlib.org/3.1.0/gallery/color/named_colors.html
    """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.notifier = Notifier()
            self.styles = dict()

    class Keys(Enum):
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

    __instance = None

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

    def __init__(self):
        if PlotContext.__instance is None:
            PlotContext.__instance = PlotContext.__DataStore()

    def get_style_by_run_id(self, run_id):
        try:
            return self.__instance.styles[run_id]
        except KeyError:
            return None

    def get_visible_styles(self):
        visible_styles = []
        for key in self.__instance.styles:
            style = self.__instance.styles[key]
            if style[PlotContext.Keys.VISIBLE]:
                visible_styles.append(style)
        return visible_styles

    def add_style_for_run(self, run, visible=True, error_bars=True, stop_signal=False):
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
        style[PlotContext.Keys.ID] = run.id
        style[PlotContext.Keys.LABEL] = run.meta[files.TITLE_KEY]
        style[PlotContext.Keys.ERROR_BARS] = error_bars
        style[PlotContext.Keys.VISIBLE] = visible
        style[PlotContext.Keys.LINE] = 'none'
        style[PlotContext.Keys.MARKER] = marker
        style[PlotContext.Keys.LINE_COLOR] = 'Default'
        style[PlotContext.Keys.MARKER_COLOR] = 'Default'
        style[PlotContext.Keys.FILLSTYLE] = 'none'
        style[PlotContext.Keys.DEFAULT_COLOR] = color
        style[PlotContext.Keys.LINESTYLE] = ''
        style[PlotContext.Keys.LINE_WIDTH] = 1
        style[PlotContext.Keys.MARKER_SIZE] = 5
        style[PlotContext.Keys.ERRORBAR_STYLE] = 0
        style[PlotContext.Keys.ERRORBAR_COLOR] = 'Default'
        style[PlotContext.Keys.ERRORBAR_WIDTH] = 1
        style[PlotContext.Keys.FIT_COLOR] = 'Default'
        style[PlotContext.Keys.FIT_LINESTYLE] = '-'

        self.__instance.styles[run.id] = style

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_color_for_run(self, run_id, color, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        color = self.color_options_values[color]
        if color in self._unused_colors.keys():
            self._update_colors(color=color, used=True)
        if style[PlotContext.Keys.DEFAULT_COLOR] in self._used_colors.keys():
            self._update_colors(color=style[PlotContext.Keys.DEFAULT_COLOR], used=False)
        if style[PlotContext.Keys.DEFAULT_COLOR] == color:
            return

        style[PlotContext.Keys.DEFAULT_COLOR] = color
        style[PlotContext.Keys.LINE_COLOR] = 'Default'
        style[PlotContext.Keys.ERRORBAR_COLOR] = 'Default'
        style[PlotContext.Keys.MARKER_COLOR] = 'Default'
        style[PlotContext.Keys.FIT_COLOR] = 'Default'

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_marker_for_run(self, run_id, marker, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        marker = self.marker_options_values[marker]
        if marker in self._unused_markers.keys():
            self._update_markers(marker=marker, used=True)

        if style[PlotContext.Keys.MARKER] in self._used_markers.keys():
            self._update_markers(marker=style[PlotContext.Keys.MARKER], used=False)
        if style[PlotContext.Keys.MARKER] == marker:
            return

        style = self.get_style_by_run_id(run_id)
        style[PlotContext.Keys.MARKER] = marker

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_visibilities(self, visible, run_id=None, stop_signal=None):
        if run_id is not None:
            for rid in run_id:
                style = self.get_style_by_run_id(rid)
                style[PlotContext.Keys.VISIBLE] = visible
        else:
            for style in self.__instance.styles.values():
                style[PlotContext.Keys.VISIBLE] = visible

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_style_parameter(self, run_ids, key, option_key, stop_signal=None):
        for run_id in run_ids:
            style = self.get_style_by_run_id(run_id)

            if style is None:
                return

            if key == PlotContext.Keys.LINESTYLE:
                style[key] = self.linestyle_options_values[option_key]
            elif key == PlotContext.Keys.FIT_LINESTYLE:
                style[key] = self.linestyle_options_values[option_key]
            elif key == PlotContext.Keys.ERRORBAR_COLOR or \
                    key == PlotContext.Keys.MARKER_COLOR or \
                    key == PlotContext.Keys.LINE_COLOR or \
                    key == PlotContext.Keys.FIT_COLOR:
                style[key] = self.color_options_extra_values[option_key]
            elif key == PlotContext.Keys.ERRORBAR_WIDTH:
                style[key] = self.errorbar_width_values[option_key]
            elif key == PlotContext.Keys.LINE_WIDTH:
                style[key] = self.line_width_options_values[option_key]
            elif key == PlotContext.Keys.MARKER_SIZE:
                style[key] = self.marker_size_options_values[option_key]
            elif key == PlotContext.Keys.ERRORBAR_STYLE:
                style[key] = self.errorbar_styles_values[option_key]
            elif key == PlotContext.Keys.MARKER:
                self.change_marker_for_run(run_id, option_key, True)
            elif key == PlotContext.Keys.FILLSTYLE:
                style[key] = self.fillstyle_options_values[option_key]
            elif key == PlotContext.Keys.DEFAULT_COLOR:
                self.change_color_for_run(run_id, option_key, True)

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_label(self, label, run_id, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        style[PlotContext.Keys.LABEL] = label

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_styles(self):
        return self.__instance.styles

    def _update_markers(self, marker, used):
        if used:
            if marker not in self._used_markers.keys():
                self._used_markers[marker] = self._marker_options[marker]
            if marker in self._unused_markers.keys():
                self._unused_markers.pop(marker)
        else:
            if marker not in self._unused_markers.keys():
                self._unused_markers[marker] = self._marker_options[marker]
            if marker in self._used_markers.keys():
                self._used_markers.pop(marker)
        return True

    def _update_colors(self, color, used):
        if used:
            if color not in self._used_colors.keys():
                self._used_colors[color] = self.color_options[color]
            if color in self._unused_colors.keys():
                self._unused_colors.pop(color)
        else:
            if color not in self._unused_colors.keys():
                self._unused_colors[color] = self.color_options[color]
            if color in self._used_colors.keys():
                self._used_colors.pop(color)
        return True

    def clear_plot_parameters(self, run_id=None, stop_signal=None):
        if run_id:
            style = self.get_style_by_run_id(run_id)
            self.__instance.styles.pop(run_id)
            self._update_markers(style[PlotContext.Keys.MARKER], False)
            self._update_colors(style[PlotContext.Keys.DEFAULT_COLOR], False)
        else:
            for style in self.__instance.styles:
                self._update_markers(style[PlotContext.Keys.MARKER], False)
                self._update_colors(style[PlotContext.Keys.DEFAULT_COLOR], False)
            self.__instance.styles = dict()

        if not stop_signal:
            self.__instance.notifier.notify()

    def subscribe(self, observer):
        self.__instance.notifier.subscribe(observer)


class Notifier:
    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def notify(self):
        for observer in self.observers:
            observer.update()
