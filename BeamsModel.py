# Model for BEAMS application

# BEAMS specific modules
import BeamsUtility

# Standard Library modules
import os
import time

# Installed modules
import numpy as np
import scipy.interpolate as sp
import scipy.fftpack as spf

# Signals from Model to Controllers
FILE_CHANGED = 1
PARAMETER_CHANGED = 2
RUN_LIST_CHANGED = 3
RUN_DATA_CHANGED = 4


class BEAMSModel:
    """ Manages the data, logic and rules of the application. """
    def __init__(self):
        """Initializes the empty model"""
        self.all_full_filepaths = {}
        self.plot_parameters = {}
        self.used_colors = []
        self.run_list = []
        self.current_formats = {}

        # The controllers will register themselves in this dictionary to the signals they need to be notified of.
        self.observers = {FILE_CHANGED: [],
                          PARAMETER_CHANGED: [],
                          RUN_LIST_CHANGED: [],
                          RUN_DATA_CHANGED: []}

        # For debugging currently
        self.debugging_signals = {FILE_CHANGED: 'FILE_CHANGED',
                                  PARAMETER_CHANGED: 'PARAMETER_CHANGED',
                                  RUN_LIST_CHANGED: 'RUN_LIST_CHANGED',
                                  RUN_DATA_CHANGED: 'RUN_DATA_CHANGED'}

        self.color_options = ["blue", "red", "green", "orange", "purple",
                              "brown", "yellow", "gray", "olive", "cyan", "pink"]

    def update_colors(self, color=None, used=False, custom=False):
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

    def update_run_color(self, file=None, color=None):
        """ Updates the color of a specific run. Calls update_colors() to update the used and available color lists. """
        if color in self.color_options:
            self.update_colors(color=color, used=True)

        for run in self.run_list:
            if run.filename == file:
                if run.color in self.used_colors:
                    self.update_colors(color=run.color, used=False)
                if run.color == color:
                    return
                run.color = color

        self.notify(RUN_DATA_CHANGED)

    def update_runs(self, formats):
        """ Updates the list of runs by removing any old runs not selected by user and adding the new ones."""
        current_files = [file for file in self.current_formats.keys()]
        for filename in current_files:  # First checks if any old filenames are not in the new list
            if filename not in formats.keys():
                for run in self.run_list:
                    if run.filename == filename:
                        self.update_colors(color=run.color, used=False)  # Update color availability
                        self.run_list.remove(run)  # Remove the no longer selected run.
                self.current_formats.pop(filename)

        for filename in formats.keys():  # Second checks if any filenames in the new list are not in the old
            if filename not in self.current_formats.keys():
                # print('Adding', formats[filename])
                self.run_list.append(RunData(filename=filename, f_format=formats[filename],
                                             color=self.color_options[0]))
                self.update_colors(color=self.color_options[0], used=True)
                self.current_formats.update({filename: formats[filename]})

        self.notify(RUN_DATA_CHANGED)
        self.notify(RUN_LIST_CHANGED)  # Notifies the Run Display Panel

    def update_plot_parameters(self):
        """ Prompts the re-plotting of data by notifying the PlotPanel"""
        self.notify(PARAMETER_CHANGED)  # Notifies the Plot Panel

    def update_file_list(self, file_name=None, file_path=None, remove=False):
        """ Adds full filepaths to model file dictionary. """
        if remove:
            self.all_full_filepaths.pop(file_name)
        else:
            # If file path is not reachable, add 'Not Found' tag to the file name.
            if not BeamsUtility.is_found(file_path):
                file_name = file_name + ' (Not Found) '
                # e.g. user opened a session with deleted files or files from another computer.

            # If it is reached and their is a tagged version of it in the list, remove it (user specified correct path)
            elif (file_name + ' (Not Found) ') in self.all_full_filepaths.keys():
                self.all_full_filepaths.pop((file_name + ' (Not Found) '))

            self.all_full_filepaths[file_name] = file_path

        self.notify(FILE_CHANGED)  # Notifies the File Manager Panel

    def update_visibilities(self, file=None, isolate=False):
        """ Updates the visibility of specified plot. """
        if isolate:  # If a run is isolated, set visibility of all other runs to False
            for run in self.run_list:
                if run.filename == file:
                    run.visibility = True
                else:
                    run.visibility = False
        else:  # If no runs are isolated set all visibilities to True
            for run in self.run_list:
                run.visibility = True

        self.notify(RUN_DATA_CHANGED)

    def update_title(self, file=None, new_title=None):
        for run in self.run_list:
            if run.filename == file:
                run.f_formats['Title'] = new_title
                self.notify(RUN_DATA_CHANGED)

    def open_save_session(self, run_list):
        self.run_list = run_list
        for run in run_list:
            file_root = os.path.split(run.filename)[1]
            self.update_file_list(file_root, run.filename)
            self.current_formats[run.filename] = run.f_formats
        self.notify(RUN_LIST_CHANGED)
        self.notify(RUN_DATA_CHANGED)

    def notify(self, signal):
        """ Calls the update() function in any controller registered with the passed in signal. """
        for controller in self.observers[signal]:
            if 'update' in dir(controller):
                print('Notifying {} of {}'.format(str(controller), self.debugging_signals[signal]))
                controller.update(signal)


class RunData:
    """ Stores all data relevant to a run.
        Required Parameters:
            filename : file path for the data to be used for this run.
            f_format : dictionary containing (at least):
                - Histogram titles for the file
                - Number of header rows for the file
                - Histograms to be used in calculating asymmetry [hist_one, hist_two]
                - Good bins 1 and 2, the initial and final bins for calculating asymmetry
                - Background 1 and 2, the initial and final bins for calculating background
                - Size of the time bins in the file (in µs)
            visibility : bool that will determine if this run is plotted
            color : color of the run on the plots

        Instance Variables (self.):
            [Parameters passed in]
            asymmetry : the full asymmetry calculated from the user specified histograms
            uncertainty : the full uncertainty array calculated from user specified histograms

        Public Methods:
            bin_data(self, final_bin_size, slider_moving) : Returns binned asymmetry, time and
                uncertainty arrays.
            calculate_fft(bin_size, asymmetry, times) : Returns smoothed frequencies and magnitudes for plotting.
    """
    def __init__(self, filename=None, f_format=None, visibility=True, color=None):
        """Initialize a RunData object based on filename and format"""
        self.f_formats = f_format
        self.visibility = visibility
        self.color = color
        self.filename = filename
        self.t0 = 0

        self.histogram_data = self.retrieve_histogram_data()

        bkg_one, bkg_two = self.calculate_background_radiation(hist_one=self.f_formats['CalcHists'][0],
                                                               hist_two=self.f_formats['CalcHists'][1])

        self.asymmetry = self.calculate_asymmetry(hist_one=self.f_formats['CalcHists'][0],
                                                  hist_two=self.f_formats['CalcHists'][1],
                                                  bkg_one=bkg_one, bkg_two=bkg_two)

        self.uncertainty = self.calculate_uncertainty(hist_one=self.f_formats['CalcHists'][0],
                                                      hist_two=self.f_formats['CalcHists'][1])

        self.time = (np.arange(len(self.asymmetry)) * float(self.f_formats['BinSize'])/1000) + \
                    (self.t0 * float(self.f_formats['BinSize'])/1000)

        self.binned_asymmetry = np.array([])
        self.binned_time = np.array([])
        self.binned_uncertainty = np.array([])

        del self.histogram_data

    def __bool__(self):
        return self.visibility

    def retrieve_histogram_data(self, specific_hist=None):
        """ Retrieves histogram data from a BEAMS formatted file. """
        histogram_data = BeamsUtility.get_histograms(self.filename, skiprows=int(self.f_formats['HeaderRows']))
        histogram_data.columns = self.f_formats['HistTitles']

        if not specific_hist:
            return histogram_data
        else:
            return histogram_data[specific_hist]

    def calculate_uncertainty(self, hist_one=None, hist_two=None):
        """ Calculates the uncertainty based on histograms. """

        start_bin_one, start_bin_two, end_bin_one, end_bin_two = self.calculate_start_end(hist_one, hist_two)

        d_one = np.sqrt(self.histogram_data.loc[start_bin_one-1:end_bin_one, hist_one])
        d_two = np.sqrt(self.histogram_data.loc[start_bin_two-1:end_bin_two, hist_two])
        h_one = self.histogram_data.loc[start_bin_one-1:end_bin_one, hist_one]
        h_two = self.histogram_data.loc[start_bin_two-1:end_bin_two, hist_two]

        uncertainty = np.array(np.sqrt(np.power((2 * h_one * d_two / np.power(h_two + h_one, 2)), 2) +
                                       np.power((2 * h_two * d_one / np.power(h_two + h_one, 2)), 2)))

        np.nan_to_num(uncertainty, copy=False)

        return uncertainty

    def calculate_background_radiation(self, hist_one=None, hist_two=None):
        """ Calculates the background radiation based on histogram data before positrons are being detected. """
        # Get the portion of histogram before positrons from muon decay are being detected

        background = self.histogram_data.loc[int(self.f_formats['BkgdOne'][hist_one]):
                                             int(self.f_formats['BkgdTwo'][hist_one])-1, hist_one].values
        bkg_one = np.mean(background)  # Find mean on new array

        background = self.histogram_data.loc[int(self.f_formats['BkgdOne'][hist_two]):
                                             int(self.f_formats['BkgdTwo'][hist_two])-1, hist_two].values
        bkg_two = np.mean(background)

        del background

        return [bkg_one, bkg_two]

    def calculate_start_end(self, hist_one=None, hist_two=None):
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

        t_one = int(self.f_formats['T0'][hist_one])
        t_two = int(self.f_formats['T0'][hist_two])
        start_one = int(self.f_formats['GoodBinOne'][hist_one])
        start_two = int(self.f_formats['GoodBinOne'][hist_two])
        end_one = int(self.f_formats['GoodBinTwo'][hist_one])
        end_two = int(self.f_formats['GoodBinTwo'][hist_two])

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

        self.t0 = init_dif

        return [start_bin_one, start_bin_two, end_bin_one, end_bin_two]

    def calculate_asymmetry(self, hist_one=None, hist_two=None, bkg_one=None, bkg_two=None):
        """ Calculate asymmetry based on the overlapping 'good' area of the histograms. """

        start_bin_one, start_bin_two, end_bin_one, end_bin_two = self.calculate_start_end(hist_one, hist_two)

        hist_good_one = self.histogram_data.loc[start_bin_one-1:end_bin_one, hist_one].values
        hist_good_two = self.histogram_data.loc[start_bin_two-1:end_bin_two, hist_two].values

        asymmetry = ((hist_good_one - bkg_one) - (hist_good_two - bkg_two)) / \
                    ((hist_good_two - bkg_two) + (hist_good_one - bkg_one))

        return asymmetry

    @staticmethod
    def calculate_fft(asymmetry, times):
        """ Calculates fast fourier transform on asymmetry. """
        magnitudes = np.fft.fft(asymmetry)
        frequencies = np.fft.fftfreq(len(magnitudes), times[1]-times[0])
        magnitudes[0] = 0

        x_smooth = np.linspace(frequencies.min(), frequencies.max(), 300)

        y_smooth = sp.UnivariateSpline(frequencies[0:int(np.floor(len(frequencies)/2))],
                                       abs(magnitudes[0:int(np.floor(len(frequencies)/2))]))
        y_smooth.set_smoothing_factor(0)
        y_smooth = y_smooth(x_smooth)

        return [x_smooth, y_smooth]

    def bin_data(self, final_bin_size=None, slider_moving=False):
        """ Bins the asymmetry based on user specified bin size. """

        bin_full = float(self.f_formats['BinSize'])/1000
        bin_binned = float(final_bin_size)/1000
        num_bins = len(self.asymmetry)

        if bin_binned <= bin_full:
            return [self.asymmetry, self.time, self.uncertainty]

        binned_indices_per_bin = int(np.round(bin_binned/bin_full))  # .floor?
        binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
        leftover_bins = int(num_bins % binned_indices_per_bin)
        time_per_binned = binned_indices_per_bin * bin_full

        self.binned_time = (np.arange(binned_indices_total) * time_per_binned) + (self.t0 * bin_full) + (time_per_binned / 2)

        if slider_moving:
            if leftover_bins:
                reshaped_asymmetry = np.reshape(self.asymmetry[:-leftover_bins],
                                              (binned_indices_total, binned_indices_per_bin))
            else:
                reshaped_asymmetry = np.reshape(self.asymmetry, (binned_indices_total, binned_indices_per_bin))

            self.binned_uncertainty = []
            self.binned_asymmetry = np.apply_along_axis(np.mean, 1, reshaped_asymmetry)

        else:
            if leftover_bins:
                reshaped_asymmetry = np.reshape(self.asymmetry[:-leftover_bins],
                                              (binned_indices_total, binned_indices_per_bin))
                reshaped_uncertainty = np.reshape(self.uncertainty[:-leftover_bins],
                                                (binned_indices_total, binned_indices_per_bin))
            else:
                reshaped_asymmetry = np.reshape(self.asymmetry, (binned_indices_total, binned_indices_per_bin))
                reshaped_uncertainty = np.reshape(self.uncertainty, (binned_indices_total, binned_indices_per_bin))

            self.binned_asymmetry = np.apply_along_axis(np.mean, 1, reshaped_asymmetry)
            self.binned_uncertainty = 1 / binned_indices_per_bin * np.sqrt(np.apply_along_axis(np.sum, 1,
                                                                                          reshaped_uncertainty**2))

        return [self.binned_asymmetry, self.binned_time, self.binned_uncertainty]
