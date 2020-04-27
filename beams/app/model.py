
from enum import Enum

from util import muon, files


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
            if run.file == run_id:
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

    __instance = None

    _color_options_values = {'Blue': '#0000ff', 'Red': '#ff0000', 'Purple': '#9900ff', 'Green': '#009933',
                            'Orange': '#ff9900', 'Maroon': '#800000', 'Pink': '#ff66ff', 'Dark Blue': '#000099',
                            'Dark Green': '#006600', 'Light Blue': '#0099ff', 'Light Purple': '#cc80ff',
                            'Dark Orange': '#ff6600', 'Yellow': '#ffcc00', 'Light Red': '#ff6666',
                            'Light Green': '#00cc66'}

    _color_options = {v: k for k, v in _color_options_values.items()}
    _unused_colors = _color_options.copy()
    _used_colors = dict()

    _marker_options_values = {'point': '.', 'triangle_down': 'v', 'triangle_up': '^', 'triangle_left': '<',
                             'triangle_right': '>', 'octagon': '8', 'square': 's', 'pentagon': 'p',
                             'plus': 'P',
                             'star': '*', 'hexagon_1': 'h', 'hexagon_2': 'H', 'x': 'X', 'diamond': 'D',
                             'thin_diamond': 'd'}

    _marker_options = {v: k for k, v in _marker_options_values.items()}
    _unused_markers = _marker_options.copy()
    _used_markers = dict()

    def __init__(self):
        if PlotContext.__instance is None:
            PlotContext.__instance = PlotContext.__DataStore()

    def get_style_by_run_id(self, run_id):
        return self.__instance.styles[run_id]

    def get_visible_styles(self):
        visible_styles = set()
        for style in self.__instance.styles:
            if style[PlotContext.Keys.VISIBLE]:
                visible_styles.add(style)
        return visible_styles

    def add_style_for_run(self, run, visible=True, error_bars=True, stop_signal=False):
        if self.get_style_by_run_id(run.run_id):
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
        style[PlotContext.Keys.ID] = run.run_id
        style[PlotContext.Keys.LABEL] = run.meta[files.TITLE_KEY]
        style[PlotContext.Keys.ERROR_BARS] = error_bars
        style[PlotContext.Keys.VISIBLE] = visible
        style[PlotContext.Keys.LINE] = 'none'
        style[PlotContext.Keys.MARKER] = marker
        style[PlotContext.Keys.LINE_COLOR] = color
        style[PlotContext.Keys.MARKER_COLOR] = color
        style[PlotContext.Keys.FILLSTYLE] = 'none'

        self.__instance.styles[run.run_id] = style

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_color_for_run(self, run, color, stop_signal=None):
        color = self._color_options_values[color]
        if color in self._unused_colors.keys():
            self._update_colors(color=color, used=True)
        if run.style.color in self._used_colors.keys():
            self._update_colors(color=run.style.color, used=False)
        if run.style.color == color:
            return

        style = self.get_style_by_run_id(run.run_id)
        style[PlotContext.Keys.MARKER_COLOR] = color
        style[PlotContext.Keys.LINE_COLOR] = color

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_marker_for_run(self, run, marker, stop_signal=None):
        marker = self._marker_options_values[marker]

        if marker in self._unused_markers.keys():
            self._update_markers(marker=marker, used=True)

        if run.style.marker in self._used_markers.keys():
            self._update_markers(marker=run.style.marker, used=False)
        if run.style.marker == marker:
            return

        style = self.get_style_by_run_id(run.run_id)
        style[PlotContext.Keys.MARKER] = marker

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_visibilities(self, visible, run_id=None, stop_signal=None):
        if run_id:
            style = self.get_style_by_run_id(run_id)
            style[PlotContext.Keys.VISIBLE] = visible
        else:
            for style in self.__instance.styles:
                style[PlotContext.Keys.VISIBLE] = visible

        if not stop_signal:
            self.__instance.notifier.notify()

    def change_label(self, label, run_id, stop_signal=None):
        style = self.get_style_by_run_id(run_id)
        style[PlotContext.Keys.LABEL] = label

        if not stop_signal:
            self.__instance.notifier.notify()

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
                self._used_colors[color] = self._color_options[color]
            if color in self._unused_colors.keys():
                self._unused_colors.pop(color)
        else:
            if color not in self._unused_colors.keys():
                self._unused_colors[color] = self._color_options[color]
            if color in self._used_colors.keys():
                self._used_colors.pop(color)
        return True

    def clear_plot_parameters(self, run_id=None, stop_signal=None):
        if run_id:
            style = self.get_style_by_run_id(run_id)
            self.__instance.styles.remove(style)
            self._update_markers(style[PlotContext.Keys.MARKER], False)
            self._update_colors(style[PlotContext.Keys.MARKER_COLOR], False)
        else:
            for style in self.__instance.styles:
                self._update_markers(style[PlotContext.Keys.MARKER], False)
                self._update_colors(style[PlotContext.Keys.MARKER_COLOR], False)
            self.__instance.styles = set()

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
