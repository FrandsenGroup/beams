# Model for BEAMS application

# BEAMS specific modules
import BeamsUtility

# Standard Library modules
import os
import uuid

# Installed modules
import numpy as np
import scipy.interpolate as sp

# Signals from Model to Controllers
STYLE_CHANGE = 1
FILE_CHANGE = 2
RUN_LIST_CHANGE = 3
RUN_DATA_CHANGE = 4


# Style Keys
STYLE_TITLE = 'Title'
STYLE_COLOR = 'Color'
STYLE_MARKER = 'Marker'
STYLE_VISIBILITY = 'Visibility'


class RunService:
    class __ServiceResources:
        def __init__(self):
            self.database = Database()
            self.styler = RunStyler()

            # fixme consolidate these three
            # fixme if nobody else needs to know the files that aren't plotted just keep them in file manager
            # fixme there really is no reason for the files to be stored in the run service, factor it out.
            self.runs = []
            self.files = set()
            self.run_id_file = dict()

            # The controllers will register themselves in this dictionary to the signals they need to be notified of.
            self.observers = {STYLE_CHANGE: [],
                              FILE_CHANGE: [],
                              RUN_DATA_CHANGE: [],
                              RUN_LIST_CHANGE: []}

            # For debugging currently
            self.debugging_signals = {STYLE_CHANGE: 'STYLE_CHANGE',
                                      FILE_CHANGE: 'FILE_CHANGE',
                                      RUN_DATA_CHANGE: 'RUN_DATA_CHANGE',
                                      RUN_LIST_CHANGE: 'RUN_LIST_CHANGE'}

    instance = None

    def __init__(self):
        if not RunService.instance:
            RunService.instance = RunService.__ServiceResources()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def remove_file(self, filename):
        """ @Param Expects a full file path. """
        if filename in self.run_id_file.keys():
            self.remove_run_by_id(self.run_id_file[filename])
        else:
            self.files.remove(filename)

    def clear_runs(self):
        for file in self.run_id_file.keys():
            self.remove_file(file)
        self._notify(RUN_LIST_CHANGE)

    def remove_run_by_id(self, run_id):
        run = self.database.get_run_by_id(run_id)

        self.styler.clear_style(run.style)
        self.runs.remove(run_id)
        self.files.remove(run.filename)
        self.run_id_file.pop(run.filename)
        self.database.remove_run(run)

    def add_run(self, file, visible=True):
        print(file)
        file_path = file.get_file_path()

        if file_path in self.run_id_file.keys():
            return self.run_id_file[file_path]

        if file.get_type() == BeamsUtility.FileReader.ASYMMETRY_FILE:
            data = file.get_data()
            meta = file.get_meta()

            run = Run(data.loc[:,'Asymmetry'].values, data.loc[:,'Uncertainty'].values, data.loc[:,'Time'].values,
                      meta, file_path, meta[BeamsUtility.T0_KEY])
            print(run)

        elif file.get_type() == BeamsUtility.FileReader.HISTOGRAM_FILE:
            run = self._generate_run_data(file_path, file.get_meta())

        else:
            return None

        run_id = uuid.uuid1()
        run.run_id = run_id
        run.type = file.get_type()

        style = self.styler.create_style(run)
        style.visibility = visible
        run.style = style

        self.database.add_run(run)
        self.runs.append(run_id)
        self.run_id_file[file_path] = run_id

        print(run)
        return run_id

    # Updating Functions
    def update_file_list(self, files, remove=False):
        """
        :param files: is an array of FULL file paths
        :param remove: is a boolean indicating if the files should be removed from the model
        :raises FILE_CHANGE and possible RUN_LIST_CHANGE signal: RUN_LIST_CHANGE signal if a loaded run is removed.
        """
        run_list_changed = False

        if remove:
            for filename in files:
                if filename in self.run_id_file.keys():
                    self.remove_run_by_id(self.run_id_file[filename])
                    run_list_changed = True
                else:
                    self.files.remove(filename)
        else:
            for file in files:
                self.files.add(file)

        if run_list_changed:
            self._notify(RUN_LIST_CHANGE)

        self._notify(FILE_CHANGE)

    def update_run_list(self, files, metas=None, visible=True):
        """
        :param files: an array of FULL file paths
        :param metas: a dictionary holding meta data for run
        :raises RUN_LIST_CHANGE signal:
        """

        print(files)
        current_files = [file for file in self.run_id_file.keys()]
        new_file_paths = [new_file.get_file_path() for new_file in files]
        new_file_ext = os.path.splitext(new_file_paths[0])[1]
        for file in current_files:
            if os.path.splitext(file)[1] == new_file_ext and file not in new_file_paths:
                self.remove_file(file)
                self.files.add(file)

        for file in files:
            if file.get_file_path() not in self.run_id_file.keys():
                self.add_run(file)

        self._notify(RUN_LIST_CHANGE)

    def update_run_style(self, run_id, style_key, style_value):
        """
        USE update_visible_runs() FOR UPDATING VISIBILITY STYLE
        :param run_id: array of run IDs that will be changed
        :param style_key: style var to be changed
        :param style_value: value assigned to style var
        :raises STYLE_CHANGE signal:
        """
        run = self.database.get_run_by_id(run_id)
        self.styler.update_style(run, style_key, style_value)
        self._notify(STYLE_CHANGE)

    def update_visible_runs(self, run_ids):
        """
        :param run_ids: ID's of runs that will be shown on plot.
        :raises STYLE_CHANGE signal:
        """
        for run in self.get_runs():
            if run.run_id not in run_ids:
                self.styler.update_style(run, STYLE_VISIBILITY, False)
            else:
                self.styler.update_style(run, STYLE_VISIBILITY, True)

        self._notify(STYLE_CHANGE)

    def update_run_meta(self, run_id, meta_key, meta_value):
        """
        :param run_id: ID of the run that will be changed
        :param meta_key: key of meta var to changed
        :param meta_value: new value for meta var
        """
        run = self.database.get_run_by_id(run_id)
        run.meta[meta_key] = meta_value

    def update_run_correction(self, run_ids, alpha):
        for run_id in run_ids:
            run = self.database.get_run_by_id(run_id)

            histogram_data = BeamsUtility.get_histograms(run.filename, skiprows=int(run.meta['HeaderRows']))
            histogram_data.columns = run.meta['HistTitles']

            start_bin_one, start_bin_two, end_bin_one, end_bin_two, t0 = calculate_start_end(run.meta)

            hist_one_title = run.meta['CalcHists'][0]
            hist_one = histogram_data.loc[start_bin_one - 1: end_bin_one, hist_one_title].values
            bkgd_one = calculate_bkgd_radiation(run.meta, histogram_data[hist_one_title], run.meta['BkgdOne'][hist_one_title],
                                                run.meta['BkgdTwo'][hist_one_title])
            hist_two_title = run.meta['CalcHists'][1]
            hist_two = histogram_data.loc[start_bin_two - 1: end_bin_two, hist_two_title].values
            bkgd_two = calculate_bkgd_radiation(run.meta, histogram_data[hist_two_title], run.meta['BkgdOne'][hist_two_title],
                                                run.meta['BkgdTwo'][hist_two_title])

            asymmetry = calculate_asymmetry(run.meta, hist_one, hist_two, bkgd_one, bkgd_two)

            run.alpha = alpha
            run.asymmetry = correct_asymmetry(run.meta, asymmetry, alpha)

        self._notify(RUN_DATA_CHANGE)

    # Getter Functions
    def get_run_by_id(self, run_id):
        return self.database.get_run_by_id(run_id)

    def get_run_id_by_filename(self, filename):
        """ @Param Expects a full file path. """
        run = self.database.get_run_by_filename(filename)
        if run is None:
            return None
        else:
            return run.run_id

    def get_run_binned(self, run_id, bin_size, keep_uncertainty):
        run = self.database.get_run_by_id(run_id)
        return bin_asymmetry(run.meta, run.asymmetry, run.time, run.uncertainty, run.t0, bin_size, keep_uncertainty)

    def get_run_style(self, run_id):
        run = self.database.get_run_by_id(run_id)
        return run.style

    def get_run_asymmetry(self, run_id):
        run = self.database.get_run_by_id(run_id)
        return run.asymmetry

    def get_run_uncertainty(self, run_id):
        run = self.database.get_run_by_id(run_id)
        return run.uncertainty

    def get_run_time(self, run_id):
        run = self.database.get_run_by_id(run_id)
        return run.time

    def get_run_fft(self, run_id, spline=True):
        run = self.database.get_run_by_id(run_id)
        return calculate_fft(run.asymmetry, run.time, spline)

    def get_run_histogram(self, run_id, hist_title):
        run = self.database.get_run_by_id(run_id)
        histogram_data = BeamsUtility.get_histograms(run.filename, skiprows=int(run.meta['HeaderRows']))
        histogram_data.columns = run.meta['HistTitles']
        return histogram_data[hist_title]

    def get_run_ids(self):
        return self.runs

    def get_runs(self):
        return self.database.runs

    def get_run_files(self):
        return self.files

    def get_run_integrations(self, run_ids):
        return [np.trapz(run.asymmetry, run.time) for run in self.get_runs() if run.run_id in run_ids]

    def get_run_temperatures(self, run_ids):
        return [float(run.meta[BeamsUtility.TEMPERATURE_KEY].split('(')[0]) for run in self.get_runs() if run.run_id in run_ids]

    def get_run_fields(self, run_ids):
        return [float(run.meta[BeamsUtility.FIELD_KEY].split('G')[0]) for run in self.get_runs() if run.run_id in run_ids]

    # Protected Functions for RunService
    def send_signal(self, signal):
        self._notify(signal)

    def _notify(self, signal):
        """ Calls the update() function in any controller registered with the passed in signal. """
        for controller in self.observers[signal]:
            if 'update' in dir(controller):
                print('Notifying {} of {}'.format(str(controller), self.debugging_signals[signal]))
                controller.update(signal)

    @staticmethod
    def _generate_run_data(filename, meta):
        file = BeamsUtility.FileReader(filename)
        histogram_data = file.get_data()

        start_bin_one, start_bin_two, end_bin_one, end_bin_two, t0 = calculate_start_end(meta)

        hist_one_title = meta['CalcHists'][0]
        hist_one = histogram_data.loc[start_bin_one-1: end_bin_one, hist_one_title].values
        bkgd_one = calculate_bkgd_radiation(meta, histogram_data[hist_one_title], meta['BkgdOne'][hist_one_title],
                                            meta['BkgdTwo'][hist_one_title])
        hist_two_title = meta['CalcHists'][1]
        hist_two = histogram_data.loc[start_bin_two-1: end_bin_two, hist_two_title].values
        bkgd_two = calculate_bkgd_radiation(meta, histogram_data[hist_two_title], meta['BkgdOne'][hist_two_title],
                                            meta['BkgdTwo'][hist_two_title])

        asymmetry = calculate_asymmetry(meta, hist_one, hist_two, bkgd_one, bkgd_two)

        uncertainty = calculate_uncertainty(meta, hist_one, hist_two)

        time = (np.arange(len(asymmetry)) * float(meta['BinSize']) / 1000) + \
               (t0 * float(meta['BinSize']) / 1000)

        new_run = Run(asymmetry, uncertainty, time, meta, filename, t0)

        return new_run


class RunStyler:
    class __StyleResources:
        def __init__(self):
            self.database = Database()

            self.plot_parameters = {}
            self.used_colors = []
            self.unused_markers = dict()
            self.used_markers = dict()
            self.color_options = ["blue", "red", "green", "orange", "purple",
                                  "brown", "yellow", "gray", "olive", "cyan", "pink"]
            self.marker_options_values = {'point': '.', 'triangle_down': 'v', 'triangle_up': '^', 'triangle_left': '<',
                                          'triangle_right': '>', 'octagon': '8', 'square': 's', 'pentagon': 'p',
                                          'plus': 'P',
                                          'star': '*', 'hexagon_1': 'h', 'hexagon_2': 'H', 'x': 'X', 'diamond': 'D',
                                          'thin_diamond': 'd'}
            self.marker_options = {v: k for k, v in self.marker_options_values.items()}
            self.unused_markers = self.marker_options.copy()

    instance = None

    def __init__(self):
        if not RunStyler.instance:
            RunStyler.instance = RunStyler.__StyleResources()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def update_style(self, run, style_key, style_value):
        if style_key == STYLE_TITLE:
            self._update_run_title(run, style_value)
        elif style_key == STYLE_COLOR:
            self._update_run_color(run, style_value)
        elif style_key == STYLE_MARKER:
            self._update_run_marker(run, style_value)
        elif style_key == STYLE_VISIBILITY:
            self._update_run_visibilities(run, style_value)
        else:
            print('Invalid Style Key')

    def create_style(self, run=None):
        style = Style()
        style.visibility = True

        if len(self.unused_markers.keys()) == 0:
            self.unused_markers = self.used_markers.copy()
        style.marker = list(self.unused_markers.keys())[0]
        self._update_markers(style.marker, True)

        if len(self.color_options) == 0:
            self.color_options = self.used_colors.copy()
        style.color = self.color_options[0]
        self._update_colors(style.color, True)

        if run:
            style.run_id = run.run_id
            style.title = run.meta[BeamsUtility.TITLE_KEY]
        else:
            style.run_id = 0
            style.title = "Null"

        return style

    def clear_style(self, style):
        self._update_colors(style.color, False)
        self._update_markers(style.marker, False)

    def _update_markers(self, marker=None, used=False):
        if used:
            if marker not in self.used_markers.keys():
                self.used_markers[marker] = self.marker_options[marker]
            if marker in self.unused_markers.keys():
                self.unused_markers.pop(marker)
        else:
            if marker not in self.unused_markers.keys():
                self.unused_markers[marker] = self.marker_options[marker]
            if marker in self.used_markers.keys():
                self.used_markers.pop(marker)
        return True

    def _update_colors(self, color=None, used=False, custom=False):
        """ Updates the used and un-used color lists so as to keep track of which colors are available
                when plotting new runs without having two runs of identical color."""
        if not custom:  # Don't want to save custom colors in the library
            if used:
                if color in self.color_options:
                    self.color_options.remove(color)
                if color not in self.used_colors:
                    self.used_colors.append(color)
            else:
                if color in self.used_colors:
                    self.used_colors.remove(color)
                if color not in self.color_options:
                    self.color_options.append(color)

        return True

    def _update_run_color(self, run, color):
        """ Updates the color of a specific run. Calls update_colors() to update the used and available color lists. """
        if color in self.color_options:
            self._update_colors(color=color, used=True)

        if run.style.color in self.used_colors:
            self._update_colors(color=run.style.color, used=False)
        if run.style.color == color:
            return  # No change
        run.style.color = color

    def _update_run_marker(self, run, marker):
        marker = self.marker_options_values[marker]

        if marker in self.unused_markers.keys():
            self._update_markers(marker=marker, used=True)

        if run.style.marker in self.used_markers.keys():
            self._update_markers(marker=run.style.marker, used=False)
        if run.style.marker == marker:
            return
        run.style.marker = marker

    @staticmethod
    def _update_run_visibilities(run, visibility):
        """ Updates the visibility of specified plot. """
        run.style.visibility = visibility

    @staticmethod
    def _update_run_title(run, new_title):
        run.meta['Title'] = new_title
        run.style.title = new_title


class Database:
    class __RunData:
        def __init__(self):
            self.runs = []

    instance = None

    def __init__(self):
        if not Database.instance:
            Database.instance = Database.__RunData()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_run_by_filename(self, filename):
        for run in self.runs:
            if run.filename == filename:
                return run
        return None

    def get_run_by_id(self, run_id):
        for run in self.runs:
            if run.run_id == run_id:
                return run
        return None

    def add_run(self, run):
        self.runs.append(run)

    def remove_run(self, run):
        self.runs.remove(run)


class Run:
    def __init__(self, asymmetry, uncertainty, time, meta, filename, t0, type=None):
        self.asymmetry = np.array(asymmetry)
        self.uncertainty = np.array(uncertainty)
        self.time = np.array(time)

        self.t0 = t0
        self.alpha = 1
        self.beta = 1
        self.meta = meta
        self.run_id = None
        self.filename = filename
        self.style = None
        self.type = type

    def __str__(self):
        return self.meta[BeamsUtility.TITLE_KEY] + ": len(asymmetry)=" + str(len(self.asymmetry)) \
               + ": len(uncertainty)=" + str(len(self.uncertainty)) \
               + ": len(time)=" + str(len(self.time))


class Style:
    def __init__(self):
        self.run_id = None
        self.color = None
        self.visibility = None
        self.marker = None
        self.title = None


def calculate_start_end(meta):
    """ Based on the T0, GoodBin1 and GoodBin2 of each histogram, determine the sections
                to be used for the asymmetry. """
    # Worst Case Example (nothing matches):
    # Histogram 1: T0 is 979, GoodBin 1 is 1030, GoodBin2 is 27356
    # Histogram 2: T0 is 982, GoodBin 1 is 1000, GoodBin2 is 27648
    # 1)    We want to find the greater difference of the two between their T0 Bin and their GoodBin1. In this case
    #       that would be 51 (1030 - 979) rather then 18 (1000 - 982).
    # 2)    Add this greater separation to each histogram's T0 and this is our start bin for each histogram.
    #       (1030 for Histogram 1 and 1033 for Histogram 2)
    # 3)    Find the number of bins in the 'Good' area for each histogram.
    # 4)    Choose end bins such that we only use overlapping area.

    t_one = int(meta['T0'][meta['CalcHists'][0]])
    t_two = int(meta['T0'][meta['CalcHists'][1]])
    start_one = int(meta['GoodBinOne'][meta['CalcHists'][0]])
    start_two = int(meta['GoodBinOne'][meta['CalcHists'][1]])
    end_one = int(meta['GoodBinTwo'][meta['CalcHists'][0]])
    end_two = int(meta['GoodBinTwo'][meta['CalcHists'][1]])

    dif_one = start_one - t_one
    dif_two = start_two - t_two

    init_dif = dif_one if dif_one > dif_two else dif_two
    start_bin_one = t_one + init_dif
    start_bin_two = t_two + init_dif

    num_good_one = end_one - start_bin_one
    num_good_two = end_two - start_bin_two

    num_cross_good = num_good_one if num_good_one < num_good_two else num_good_two
    end_bin_one = start_bin_one + num_cross_good
    end_bin_two = start_bin_two + num_cross_good

    return [start_bin_one, start_bin_two, end_bin_one - 1, end_bin_two - 1, init_dif]


def calculate_uncertainty(meta, hist_one, hist_two):
    """ Calculates the uncertainty based on histograms. Takes two numpy arrays as input."""
    d_one = np.sqrt(hist_one)
    d_two = np.sqrt(hist_two)

    np.nan_to_num(hist_one, copy=False)
    np.nan_to_num(hist_two, copy=False)

    np.seterr(divide='ignore', invalid='ignore')  # fixme getting errors with run in 1947, 2019, M20D, 28225
    uncertainty = np.array(np.sqrt(np.power((2 * hist_one * d_two / np.power(hist_two + hist_one, 2)), 2) +
                                   np.power((2 * hist_two * d_one / np.power(hist_two + hist_one, 2)), 2)))
    np.seterr(divide='warn', invalid='warn')

    np.nan_to_num(uncertainty, copy=False)

    return uncertainty


def calculate_bkgd_radiation(meta, hist, bkgd_start, bkgd_end):
    """ Calculates the background radiation based on histogram data before positrons are being detected. """
    background = hist[int(bkgd_start):int(bkgd_end) - 1]
    bkg = np.mean(background)
    return bkg


def calculate_fft(asymmetry, times, spline=True):
    """ Calculates fast fourier transform on asymmetry. """
    magnitudes = np.fft.fft(asymmetry)
    magnitudes[0] = 0
    frequencies = abs(np.fft.fftfreq(len(magnitudes), times[1] - times[0]))
    num_frequencies = len(frequencies)

    frequencies = frequencies[0:int(np.floor(num_frequencies / 2))]
    magnitudes = abs(magnitudes[0:int(np.floor(num_frequencies / 2))])

    if spline:
        x_smooth = np.linspace(frequencies.min(), frequencies.max(), 300)

        y_smooth = sp.UnivariateSpline(frequencies, magnitudes, k=5)
        y_smooth.set_smoothing_factor(0)
        y_smooth = y_smooth(x_smooth)
        return [x_smooth, y_smooth]
    else:
        return [frequencies, magnitudes]


def calculate_asymmetry(meta, hist_one, hist_two, bkgd_one, bkgd_two):
    """ Calculate asymmetry based on the overlapping 'good' area of the histograms. """

    asymmetry = ((hist_one - bkgd_one) - (hist_two - bkgd_two)) / \
                ((hist_two - bkgd_two) + (hist_one - bkgd_one))
    return asymmetry


def correct_asymmetry(meta, asymmetry, alpha, beta=None):
    if not beta:
        beta = 1
    return ((alpha - 1) + (alpha + 1) * asymmetry) / ((alpha * beta + 1) + (alpha * beta - 1) * 2)


def bin_asymmetry(meta, asymmetry, time, uncertainty, t0, bin_size, slider_moving):
    """ Bins the asymmetry based on user specified bin size. """
    bin_full = float(meta[BeamsUtility.BIN_SIZE_KEY]) / 1000
    bin_binned = float(bin_size) / 1000
    num_bins = len(asymmetry)
    t0 = float(t0)
    if bin_binned <= bin_full:
        return [asymmetry, time, uncertainty]
    binned_indices_per_bin = int(np.round(bin_binned / bin_full))  # .floor?
    binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
    leftover_bins = int(num_bins % binned_indices_per_bin)
    time_per_binned = binned_indices_per_bin * bin_full

    binned_time = (np.arange(binned_indices_total) * time_per_binned) + (t0 * bin_full) + (time_per_binned / 2)
    if slider_moving:
        if leftover_bins:
            reshaped_asymmetry = np.reshape(asymmetry[:-leftover_bins],
                                            (binned_indices_total, binned_indices_per_bin))
        else:
            reshaped_asymmetry = np.reshape(asymmetry, (binned_indices_total, binned_indices_per_bin))

        binned_uncertainty = []
        binned_asymmetry = np.apply_along_axis(np.mean, 1, reshaped_asymmetry)

    else:
        if leftover_bins:
            reshaped_asymmetry = np.reshape(asymmetry[:-leftover_bins],
                                            (binned_indices_total, binned_indices_per_bin))
            reshaped_uncertainty = np.reshape(uncertainty[:-leftover_bins],
                                              (binned_indices_total, binned_indices_per_bin))
        else:
            reshaped_asymmetry = np.reshape(asymmetry, (binned_indices_total, binned_indices_per_bin))
            reshaped_uncertainty = np.reshape(uncertainty, (binned_indices_total, binned_indices_per_bin))

        binned_asymmetry = np.apply_along_axis(np.mean, 1, reshaped_asymmetry)
        binned_uncertainty = 1 / binned_indices_per_bin * np.sqrt(np.apply_along_axis(np.sum, 1,
                                                                                           reshaped_uncertainty ** 2))
    return [binned_asymmetry, binned_time, binned_uncertainty]








