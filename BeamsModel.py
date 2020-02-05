# Model for BEAMS application

# BEAMS specific modules
import BeamsUtility

# Standard Library modules
import os
import uuid
import logging

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


logging.basicConfig(level=logging.DEBUG)


class RunService:
    class __ServiceResources:
        def __init__(self):
            logging.debug('BeamsModel.RunService.__ServiceResources.__init__')
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
        logging.debug('BeamsModel.RunService.__init__')
        if not RunService.instance:
            RunService.instance = RunService.__ServiceResources()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    # Updating Functions
    def clear_database(self):
        logging.debug('BeamsModel.RunService.clear_database')
        run_ids = [run.run_id for run in self.database.runs]
        for run in run_ids:
            self._remove_run_by_id(run, True)

        self._notify(RUN_LIST_CHANGE)

    def update_file_list(self, files, remove=False):
        """
        :param files: is an array of FULL file paths
        :param remove: is a boolean indicating if the files should be removed from the model
        :raises FILE_CHANGE and possible RUN_LIST_CHANGE signal: RUN_LIST_CHANGE signal if a loaded run is removed.
        """
        logging.debug('BeamsModel.RunService.update_file_list')
        run_list_changed = False

        logging.error(files)
        if remove:
            for filename in files:
                if filename in self.run_id_file.keys():
                    self._remove_run_by_id(self.run_id_file[filename])
                    run_list_changed = True
                else:
                    self.files.remove(filename)
        else:
            for file in files:
                self.files.add(file)

        if run_list_changed:
            self._notify(RUN_LIST_CHANGE)

        self._notify(FILE_CHANGE)

    def update_run_list(self, files=None, visible=True, remove_ext=None):
        """
        :param visible:
        :param files: an array of FULL file paths
        :raises RUN_LIST_CHANGE signal:
        """
        logging.debug('BeamsModel.RunService.update_run_list')
        current_files = [file for file in self.run_id_file.keys()]
        if files:

            new_file_paths = [new_file.get_file_path() for new_file in files]
            new_file_ext = os.path.splitext(new_file_paths[0])[1]
            for file in current_files:
                if os.path.splitext(file)[1] == new_file_ext and file not in new_file_paths:
                    self._remove_file(file)
                    self.files.add(file)

            for file in files:
                if file.get_file_path() not in self.run_id_file.keys():
                    self._add_run(file, visible)

        if remove_ext:
            for file in current_files:
                if os.path.splitext(file)[1] == remove_ext:
                    self._remove_file(file)
                    self.files.add(file)

        self._notify(RUN_LIST_CHANGE)

    def update_run_style(self, run_id, style_key, style_value):
        """
        USE update_visible_runs() FOR UPDATING VISIBILITY STYLE
        :param run_id: array of run IDs that will be changed
        :param style_key: style var to be changed
        :param style_value: value assigned to style var
        :raises STYLE_CHANGE signal:
        """
        logging.debug('BeamsModel.RunService.update_run_style')
        run = self.database.get_run_by_id(run_id)
        self.styler.update_style(run, style_key, style_value)
        self._notify(STYLE_CHANGE)

    def update_visible_runs(self, run_ids):
        """
        :param run_ids: ID's of runs that will be shown on plot.
        :raises STYLE_CHANGE signal:
        """
        logging.debug('BeamsModel.RunService.update_visible_runs')
        for run in self.get_runs():
            if run.run_id not in run_ids:
                self.styler.update_style(run, STYLE_VISIBILITY, False)
            else:
                self.styler.update_style(run, STYLE_VISIBILITY, True)

        self._notify(STYLE_CHANGE)

    def update_run_correction(self, run_ids, alpha):
        logging.debug('BeamsModel.RunService.update_run_correction')
        for run_id in run_ids:
            run = self.database.get_run_by_id(run_id)

            file = BeamsUtility.FileReader(run.filename)
            histogram_data = file.get_data()

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
        logging.debug('BeamsModel.RunService.get_run_by_id')
        return self.database.get_run_by_id(run_id)

    def get_run_id_by_filename(self, filename):
        """ @Param Expects a full file path. """
        logging.debug('BeamsModel.RunService.get_run_id_by_filename')
        run = self.database.get_run_by_filename(filename)
        if run is None:
            return None
        else:
            return run.run_id

    def get_run_binned(self, run_id, bin_size, keep_uncertainty):
        logging.debug('BeamsModel.RunService.get_run_binned')
        run = self.database.get_run_by_id(run_id)
        return bin_asymmetry(run.meta, run.asymmetry, run.time, run.uncertainty, run.t0, bin_size, keep_uncertainty)

    def get_run_style(self, run_id):
        logging.debug('BeamsModel.RunService.get_run_style')
        run = self.database.get_run_by_id(run_id)
        return run.style

    def get_run_asymmetry(self, run_id):
        logging.debug('BeamsModel.RunService.get_run_asymmetry')
        run = self.database.get_run_by_id(run_id)
        return run.asymmetry

    def get_run_uncertainty(self, run_id):
        logging.debug('BeamsModel.RunService.get_run_uncertainty')
        run = self.database.get_run_by_id(run_id)
        return run.uncertainty

    def get_run_time(self, run_id):
        logging.debug('BeamsModel.RunService.get_run_time')
        run = self.database.get_run_by_id(run_id)
        return run.time

    def get_run_fft(self, run_id, asymmetry=None, time=None, fmin=None, fmax=None, fstep=None):
        logging.debug('BeamsModel.RunService.get_run_fft')

        if asymmetry is None or time is None:
            run = self.database.get_run_by_id(run_id)
            asymmetry = run.asymmetry
            time = run.time

        return musr_FFT(time, asymmetry, fmin, fmax, fstep)

    def get_run_histogram(self, run_id, hist_title):
        logging.debug('BeamsModel.RunService.get_run_histogram')
        run = self.database.get_run_by_id(run_id)
        file = BeamsUtility.FileReader(run.filename)
        histogram_data = file.get_data()
        return histogram_data[hist_title]

    def get_run_ids(self):
        logging.debug('BeamsModel.RunService.get_run_ids')
        return self.runs

    def get_runs(self):
        logging.debug('BeamsModel.RunService.get_runs')
        return self.database.runs

    def get_run_files(self):
        logging.debug('BeamsModel.RunService.get_run_files')
        return self.files

    def get_run_integrations(self, run_ids):
        logging.debug('BeamsModel.RunService.get_run_integration')
        return [np.trapz(run.asymmetry, run.time) for run in self.get_runs() if run.run_id in run_ids]

    def get_run_temperatures(self, run_ids):
        logging.debug('BeamsModel.RunService.get_run_temperature')
        return [float(run.meta[BeamsUtility.TEMPERATURE_KEY].split('(')[0].split('K')[0])for run in self.get_runs() if run.run_id in run_ids]

    def get_run_fields(self, run_ids):
        logging.debug('BeamsModel.RunService.get_run_fields')
        return [float(run.meta[BeamsUtility.FIELD_KEY].split('(')[0].split('G')[0]) for run in self.get_runs() if run.run_id in run_ids]

    # Protected Functions for RunService
    def _notify(self, signal):
        """ Calls the update() function in any controller registered with the passed in signal. """
        logging.debug('BeamsModel.RunService._notify')
        for controller in self.observers[signal]:
            if 'update' in dir(controller):
                print('Notifying {} of {}'.format(str(controller), self.debugging_signals[signal]))
                controller.update(signal)

    @staticmethod
    def _generate_run_data(filename, meta):
        logging.debug('BeamsModel.RunService._generate_run_data')
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

    def _remove_file(self, filename):
        """ @Param Expects a full file path. """
        logging.debug('BeamsModel.RunService._remove_file')
        if filename in self.run_id_file.keys():
            self._remove_run_by_id(self.run_id_file[filename])
        else:
            self.files.remove(filename)

    def _remove_run_by_id(self, run_id, keep_file=False):
        logging.debug('BeamsModel.RunService._remove_file_by_id')
        run = self.database.get_run_by_id(run_id)

        self.styler.clear_style(run.style)
        self.runs.remove(run_id)

        if not keep_file:
            self.files.remove(run.filename)

        self.run_id_file.pop(run.filename)
        self.database.remove_run(run)

    def _add_run(self, file, visible=True):
        logging.debug('BeamsModel.RunService._add_run')
        file_path = file.get_file_path()

        if file_path in self.run_id_file.keys():
            return self.run_id_file[file_path]

        if file.get_type() == BeamsUtility.FileReader.ASYMMETRY_FILE:
            data = file.get_data()
            meta = file.get_meta()

            run = Run(data.loc[:, 'Asymmetry'].values, data.loc[:, 'Uncertainty'].values, data.loc[:, 'Time'].values,
                      meta, file_path, meta[BeamsUtility.T0_KEY])

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

        return run_id


class RunStyler:
    class __StyleResources:
        def __init__(self):
            logging.debug('BeamsModel.RunStyler.__StyleResources.__init__')
            self.database = Database()

            self.plot_parameters = {}

            self.color_options_values = {'Blue': '#0000ff', 'Red': '#ff0000', 'Purple': '#9900ff', 'Green': '#009933',
                                        'Orange': '#ff9900', 'Maroon': '#800000', 'Pink': '#ff66ff', 'Dark Blue': '#000099',
                                        'Dark Green': '#006600', 'Light Blue': '#0099ff', 'Light Purple': '#cc80ff',
                                        'Dark Orange': '#ff6600', 'Yellow': '#ffcc00', 'Light Red': '#ff6666', 'Light Green': '#00cc66'}

            self.color_options = {v: k for k, v in self.color_options_values.items()}
            self.unused_colors = self.color_options.copy()
            self.used_colors = dict()

            self.marker_options_values = {'point': '.', 'triangle_down': 'v', 'triangle_up': '^', 'triangle_left': '<',
                                          'triangle_right': '>', 'octagon': '8', 'square': 's', 'pentagon': 'p',
                                          'plus': 'P',
                                          'star': '*', 'hexagon_1': 'h', 'hexagon_2': 'H', 'x': 'X', 'diamond': 'D',
                                          'thin_diamond': 'd'}

            self.marker_options = {v: k for k, v in self.marker_options_values.items()}
            self.unused_markers = self.marker_options.copy()
            self.used_markers = dict()

    instance = None

    def __init__(self):
        logging.debug('BeamsModel.RunStyler.__init__')
        if not RunStyler.instance:
            RunStyler.instance = RunStyler.__StyleResources()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def update_style(self, run, style_key, style_value):
        logging.debug('BeamsModel.RunStyler.update_style')
        if run is None or style_key is None or style_value is None:
            return

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
        logging.debug('BeamsModel.RunStyler.create_style')
        style = Style()
        style.visibility = True

        if len(self.unused_markers.keys()) == 0:
            self.unused_markers = self.used_markers.copy()
        style.marker = list(self.unused_markers.keys())[0]
        self._update_markers(style.marker, True)

        if len(self.unused_colors.keys()) == 0:
            self.unused_colors = self.used_colors.copy()
        style.color = list(self.unused_colors.keys())[0]
        self._update_colors(style.color, True)

        if run:
            style.run_id = run.run_id
            style.title = run.meta[BeamsUtility.TITLE_KEY]
        else:
            style.run_id = 0
            style.title = "Null"

        return style

    def clear_style(self, style):
        logging.debug('BeamsModel.RunStyler.clear_style')
        self._update_colors(style.color, False)
        self._update_markers(style.marker, False)

    def _update_markers(self, marker=None, used=False):
        logging.debug('BeamsModel.RunStyler._update_markers')
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

    def _update_colors(self, color=None, used=False):
        """ Updates the used and un-used color lists so as to keep track of which colors are available
                when plotting new runs without having two runs of identical color."""
        logging.debug('BeamsModel.RunStyler._update_colors')
        if used:
            if color not in self.used_colors.keys():
                self.used_colors[color] = self.color_options[color]
            if color in self.unused_colors.keys():
                self.unused_colors.pop(color)
        else:
            if color not in self.unused_colors.keys():
                self.unused_colors[color] = self.color_options[color]
            if color in self.used_colors.keys():
                self.used_colors.pop(color)
        return True

    def _update_run_color(self, run, color):
        """ Updates the color of a specific run. Calls update_colors() to update the used and available color lists. """
        logging.debug('BeamsModel.RunStyler._update_run_color')
        print(0)
        print(color)
        print(color, self.color_options_values)
        color = self.color_options_values[color]
        print(1)
        if color in self.unused_colors.keys():
            self._update_colors(color=color, used=True)
            print(2)
        if run.style.color in self.used_colors.keys():
            self._update_colors(color=run.style.color, used=False)
            print(3)
        if run.style.color == color:
            return
        print(4)
        run.style.color = color

    def _update_run_marker(self, run, marker):
        logging.debug('BeamsModel.RunStyler._update_run_marker')
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
        logging.debug('BeamsModel.RunStyler._update_run_visibilities')
        run.style.visibility = visibility

    @staticmethod
    def _update_run_title(run, new_title):
        logging.debug('BeamsModel.RunStyler._update_run_title')
        run.meta['Title'] = new_title
        run.style.title = new_title


class Database:
    class __RunData:
        logging.debug('BeamsModel.Database.__RunData.__init__')
        def __init__(self):
            self.runs = []

    instance = None

    def __init__(self):
        logging.debug('BeamsModel.Database.__init__')
        if not Database.instance:
            Database.instance = Database.__RunData()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def get_run_by_filename(self, filename):
        logging.debug('BeamsModel.Database.get_run_by_filename')
        for run in self.runs:
            if run.filename == filename:
                return run
        return None

    def get_run_by_id(self, run_id):
        logging.debug('BeamsModel.Database.get_run_by_id')
        for run in self.runs:
            if run.run_id == run_id:
                return run
        return None

    def add_run(self, run):
        logging.debug('BeamsModel.Database.add_run')
        self.runs.append(run)

    def remove_run(self, run):
        logging.debug('BeamsModel.Database.remove_run')
        self.runs.remove(run)


class Run:
    def __init__(self, asymmetry, uncertainty, time, meta, filename, t0, type=None):
        logging.debug('BeamsModel.Run.__init__')
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
        logging.debug('BeamsModel.Style.__init__')
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
    logging.debug('BeamsModel.calculate_start_end')

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
    logging.debug('BeamsModel.calculate_uncertainty')
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
    logging.debug('BeamsModel.calculate_bkgd_radiation')
    background = hist[int(bkgd_start):int(bkgd_end) - 1]
    bkg = np.mean(background)
    return bkg


def fourier_transform(x, fx, zmin=0.0, zmax=10.0, zstep=0.1): # requires even q-grid
    """Compute the Fourier transform of a function.
    This method uses the FFT algorithm and returns correctly spaced x and
    y arrays on an even and specifiable grid. The input grid must be evenly
    spaced.
    Args:
        x (numpy array): independent variable for function to be transformed
        fx (numpy array): dependent variable for function to be transformed
        zmin (float, default = 0.0): min value of conjugate independent variable
            grid
        zmax (float, default = 10.0): maximum value of conjugate independent
            variable grid
        zstep (float, default = 0.1): grid spacing for conjugate independent
            variable
    Returns:
        r (numpy array): independent variable grid for transformed quantity
        fr (numpy array): Fourier transform of fq (complex)
    """
    logging.debug('BeamsModel.fourier_transform')
    lostep = int(np.ceil((zmin - 1e-8) / zstep))
    histep = int(np.floor((zmax + 1e-8) / zstep)) + 1
    z = np.arange(lostep,histep)*zstep
    xstep = x[1] - x[0]
    if (x[0]-0.01*xstep) > 0:
        nn = int(np.round(x[0]/xstep))
        addme = np.linspace(0.0,x[0]-xstep,nn)
        x = np.concatenate((addme,x))
        fx = np.concatenate((0.0*addme,fx))
    xmaxzstep = np.pi/zstep
    nin = len(x)
    nbase = max([nin,histep,xmaxzstep/xstep])
    nlog2 = int(np.ceil(np.log2(nbase)))
    nout = 2**nlog2
    xmaxdb = 2*nout*xstep
    yindb=np.concatenate((fx,np.zeros(2*nout - nin)))
    cyoutdb = np.fft.fft(yindb)*xmaxdb
    fzdb = cyoutdb
    zstepfine = 2*np.pi/xmaxdb
    zfine = np.arange(nout) * zstepfine
    fzfine = fzdb[:nout]
    fzr = np.interp(z, zfine, np.real(fzfine))
    fzi = np.interp(z, zfine, np.imag(fzfine))
    if z[0]+0.0001*zstep < 0:
        nn = int(np.round(-z[0]/zstep))
        fzr[:nn] = 1.0*fzr[2*nn:nn:-1]
        fzi[:nn] = -1.0*fzi[2*nn:nn:-1]
    fz = fzr + 1j*fzi
    return z, fz


def musr_FFT(t, A, fmin=None, fmax=None, fstep=None):
    """Compute the Fourier transform of a muSR asymmetry spectrum.
    This method uses the FFT algorithm and returns correctly spaced x and
    y arrays on an even and specifiable grid. The input grid must be evenly
    spaced.
    Args:
        t (numpy array): time array of muSR spectrum to be transformed
        A (numpy array): asymmetry array of muSR spectrum to be transformed
        fmin (float, default = 0.0): min value of frequency grid (in MHz)
        fmax (float, default = 10.0): max value of frequency grid (in MHz)
        fstep (float, default = 0.1): frequency grid spacing
    Returns:
        f (numpy array): frequency grid (in MHz)
        fftSq (numpy array): Square of fft of A
    """
    logging.debug('BeamsModel.musr_FFT')
    fmin = fmin if fmin else 0
    fmax = fmax if fmax else 1
    fstep = fstep if fstep else (fmax-fmin)/100

    # fourierTransform needs frequency in rad/microsecond, not MHz, which
    # is why the factors of 2*pi are present
    w, fft = fourier_transform(t, A, 2*np.pi*fmin, 2*np.pi*fmax, 2*np.pi*fstep)
    fftSq = np.real(fft*np.conj(fft))
    return w/(2*np.pi), fftSq


def calculate_asymmetry(meta, hist_one, hist_two, bkgd_one, bkgd_two):
    """ Calculate asymmetry based on the overlapping 'good' area of the histograms. """
    logging.debug('BeamsModel.calculate_asymmetry')
    asymmetry = ((hist_one - bkgd_one) - (hist_two - bkgd_two)) / \
                ((hist_two - bkgd_two) + (hist_one - bkgd_one))
    return asymmetry


def correct_asymmetry(meta, asymmetry, alpha, beta=None):
    logging.debug('BeamsModel.correct_asymmetry')
    if not beta:
        beta = 1
    return ((alpha - 1) + (alpha + 1) * asymmetry) / ((alpha * beta + 1) + (alpha * beta - 1) * 2)


def bin_asymmetry(meta, asymmetry, time, uncertainty, t0, bin_size, slider_moving):
    """ Bins the asymmetry based on user specified bin size. """
    logging.debug('BeamsModel.bin_asymmetry')
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








