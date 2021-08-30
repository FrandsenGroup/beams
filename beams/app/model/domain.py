import enum
import os
import time

import numpy as np
import uuid

from app.model import files, services
from app.model.files import File


class Histogram(np.ndarray):
    """
    A class to represent a histogram. Inherits a numpy array so we can perform numpy
    operations on it along with storing custom methods and attributes.
    
    ...

    Attributes
    ----------
    id : str
        Id of the run associated with this histogram (generated by beams, not in .dat file).
    time_zero : int
        Bin at which the clock starts.
    good_bin_start : int
        First bin that could be used in calculating asymmetry.
    good_bin_end : int
        Last bin that could be used in calculating asymmetry.
    background_start : int
        First bin that could be used in calculating background radiation.
    background_end : int
        Last bin that could be used in calculating background radiation.
    bin_size : float
        Time (ns) per bin.
    title: string
        Title of the histogram (e.g. 'Forw', 'Back' etc).

    Methods
    -------
    intersect(other)
        Finds the intersection of two histograms.
    background_radiation()
        Finds the background radiation of the histogram.
    combine(other)
        Combines this histogram with another histogram (returns new histogram).
    
    """

    def __new__(cls, input_array, time_zero, good_bin_start, good_bin_end,
                background_start, background_end, title, run_id, bin_size, **kwargs):
        """ Initializes a new Histogram.

        Parameters
        ----------
        input_array : Iterable
            Full histogram.
        time_zero : int
            Bin at which the clock starts
        good_bin_start : int
            First bin that could be used in calculating asymmetry.
        good_bin_end : int
            Last bin that could be used in calculating asymmetry.
        background_start : int
            First bin that could be used in calculating background radiation.
        background_end : int
            Last bin that could be used in calculating background radiation.
        run_id : str
            Id of the run associated with this histogram (generated by beams, not in .dat file).
        bin_size : float
            Time (ns) per bin.
        title: string
            Title of the histogram (e.g. 'Forw', 'Back' etc).

        Returns
        -------
        self : Histogram
            A shiny new Histogram!
        
        """

        self = np.asarray(input_array).view(cls)
        self.id = run_id
        self.time_zero = int(time_zero)
        self.good_bin_start = int(good_bin_start)
        self.good_bin_end = int(good_bin_end)
        self.background_start = int(background_start)
        self.background_end = int(background_end)
        self.bin_size = float(bin_size)
        self.title = title

        return self

    def __reduce__(self):
        pickled_state = super(Histogram, self).__reduce__()

        new_state = pickled_state[2] + (self.__dict__,)

        # Parenthesis are not redundant, don't remove.
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state, **kwargs):
        self.__dict__.update(state[-1])
        super(Histogram, self).__setstate__(state[0:-1])

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self.id = getattr(obj, 'id', None)
        self.time_zero = getattr(obj, 'time_zero', None)
        self.good_bin_start = getattr(obj, 'good_bin_start', None)
        self.good_bin_end = getattr(obj, 'good_bin_end', None)
        self.background_start = getattr(obj, 'background_start', None)
        self.background_end = getattr(obj, 'background_end', None)
        self.bin_size = getattr(obj, 'bin_size', None)
        self.title = getattr(obj, 'title', None)

    def intersect(self, other):
        """ Finds useable intersection of two histograms.

        Two histograms we want to calculate asymmetries from may have different time_zero bins,
        or different good_bin ranges (the range that can be used for calculating the asymmetry)
        so this function finds the largest range of bins that can be used for calculating the
        asymmetry and the new time_zero.

        Parameters
        ----------
        other : Histogram
            The histogram we are finding an intersection with.

        Returns
        -------
        start_bin_one : int
            The first bin that can be used in calculating the asymmetry with the first histogram.
        start_bin_two : int
            The first bin that can be used in calculating the asymmetry with the second histogram.
        end_bin_one : int
            The last bin that can be used in calculating the asymmetry with the first histogram.
        end_bin_two : int
            The last bin that can be used in calculating the asymmetry with the second histogram.
        init_dif : int
            New adjusted time zero for the asymmetry.

        """
        t_one = int(self.time_zero)
        t_two = int(other.time_zero)
        start_one = int(self.good_bin_start)
        start_two = int(other.good_bin_start)
        end_one = int(self.good_bin_end)
        end_two = int(other.good_bin_end)

        dif_one = start_one - t_one
        dif_two = start_two - t_two

        init_dif = dif_one if dif_one > dif_two else dif_two
        start_bin_one = t_one + init_dif
        start_bin_two = t_two + init_dif

        num_good_one = end_one - start_bin_one
        num_good_two = end_two - start_bin_two

        num_cross_good = num_good_one if num_good_one < num_good_two else num_good_two
        end_bin_one = start_bin_one + num_cross_good - 1
        end_bin_two = start_bin_two + num_cross_good - 1

        return start_bin_one, start_bin_two, end_bin_one, end_bin_two, init_dif

    def background_radiation(self):
        """ Calculates background radiation of histogram.

        Calculates based on the range indicated by the background_start and background_end
        attributes.

        Returns
        -------
        float
            Background radiation.
        """
        return np.mean(self[int(self.background_start):int(self.background_end) - 1])

    def combine(self, *other):
        """ Combines two or more histograms and returns the resulting Histogram.

        Does not alter the histogram objects being combined.

        Parameters
        ----------
        other : *Histogram
            The histgram(s) to be combined with this one.

        Returns
        -------
        Histogram   
            The resulting combined histogram.
        """
        raise NotImplementedError("Combining histograms is not currently implemented.")


class Asymmetry(np.ndarray):
    """
    A class to represent an asymmetry of two histograms with the corresponding attributes. Inherits from numpy.ndarray
    so we can perform numpy calculations on it with casting it to an numpy array.

    ...

    Attributes
    ----------
    bin_size : float
        Time (ns) per bin.
    time_zero : float
        Bin at which the clock starts.
    alpha : float
        Alpha for correcting the run. Alpha should match the alpha of the actual asymmetry, not set without correcting.
    time : Time
        Time object (inherits from np.ndarray).
    uncertainty : Uncertainty
        Uncertainty object (inherits from np.ndarray).

    Methods
    -------
    bin(packing)
        Returns a new asymmetry binned to the provided value.
    correct(alpha)
        Returns a new asymmetry corrected to the provided value.
    raw()
        Returns a new asymmetry where alpha is equal to 1.
    cut(min_time, max_time)
        Returns a new asymmetry between the specified times.
    """

    def __new__(cls, input_array=None, time_zero=None, bin_size=None, histogram_one=None, histogram_two=None,
                uncertainty=None, time=None, alpha=None, **kwargs):
        """ Initializes a new Asymmetry.

        Parameters
        ----------
        FIRST CONSTRUCTOR OPTIONS
            input_array : Iterable
                Precalculated asymmetry.
            time_zero : int
                Bin at which the clock starts.
            bin_size : float
                Time (ns) per bin.
            uncertainty : Uncertainty
                Precalculated uncertainty.
            time : Time
                Precalculated time.

        SECOND CONSTRUCTOR OPTIONS
            histogram_one, histogram_two : Histogram
                Histograms to be used in calculating the new asymmetry.

        OPTIONAL
            alpha : float
                Alpha value to correct the asymmetry after it is calculated.
        """
        if (input_array is None or time_zero is None or bin_size is None or uncertainty is None or time is None) \
                and (histogram_one is None or histogram_two is None):
            raise ValueError("Not enough constructor parameters satisfied")

        if input_array is None:
            start_bin_one, start_bin_two, end_bin_one, end_bin_two, time_zero = histogram_one.intersect(histogram_two)
            background_one = histogram_one.background_radiation()
            background_two = histogram_two.background_radiation()
            histogram_one_good = histogram_one[start_bin_one - 1: end_bin_one + 1]
            histogram_two_good = histogram_two[start_bin_two - 1: end_bin_two + 1]
            input_array = ((histogram_one_good - background_one) - (histogram_two_good - background_two)) / \
                          ((histogram_two_good - background_two) + (histogram_one_good - background_one))

            if alpha is not None:
                input_array = ((alpha - 1) + ((alpha + 1) * input_array)) / \
                              ((alpha + 1) + ((alpha - 1) * input_array))

            if histogram_one.bin_size != histogram_two.bin_size:
                raise ValueError("Histograms do not have the same bin size")
            bin_size = histogram_one.bin_size

        if uncertainty is None:
            uncertainty = Uncertainty(histogram_one=histogram_one, histogram_two=histogram_two)
        else:
            uncertainty = Uncertainty(input_array=uncertainty, bin_size=bin_size)

        if time is None:
            time = Time(bin_size=bin_size, length=len(input_array), time_zero=time_zero)
        else:
            time = Time(input_array=time, bin_size=bin_size, length=len(input_array), time_zero=time_zero)

        self = np.asarray(input_array).view(cls)
        self.uncertainty = uncertainty
        self.time = time
        self.bin_size = float(bin_size)
        self.time_zero = float(time_zero)
        self.alpha = alpha if alpha is not None else 1

        return self

    def __reduce__(self):
        pickled_state = super(Asymmetry, self).__reduce__()

        new_state = pickled_state[2] + (self.__dict__,)

        # Parenthesis are not redundant, don't remove.
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state, **kwargs):
        self.__dict__.update(state[-1])
        super(Asymmetry, self).__setstate__(state[0:-1])

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self.uncertainty = getattr(obj, 'uncertainty', None)
        self.time = getattr(obj, 'time', None)
        self.bin_size = getattr(obj, 'bin_size', None)
        self.time_zero = getattr(obj, 'time_zero', None)
        self.alpha = getattr(obj, 'alpha', None)

    @classmethod
    def from_array(cls):
        pass

    @classmethod
    def from_histogram(cls):
        pass

    def bin(self, packing):
        """ Returns new asymmetry binned to the provided packing value.

        Does not alter asymmetry object.

        Parameters
        ----------
        packing : float
            Value (in nanoseconds) to bin the asymmetry to.

        Returns
        -------
        asymmetry: Asymmetry
            A new asymmetry object binned to the provided value.
        """

        bin_full = self.bin_size / 1000
        bin_binned = float(packing) / 1000
        num_bins = len(self)

        if bin_binned <= bin_full:
            return self

        binned_indices_per_bin = int(np.round(bin_binned / bin_full))
        binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
        leftover_bins = int(num_bins % binned_indices_per_bin)

        if leftover_bins:
            reshaped_asymmetry = np.reshape(self[:-leftover_bins],
                                            (binned_indices_total, binned_indices_per_bin))
        else:
            reshaped_asymmetry = np.reshape(self, (binned_indices_total, binned_indices_per_bin))

        binned_asymmetry = np.apply_along_axis(np.mean, 1, reshaped_asymmetry)

        return Asymmetry(input_array=binned_asymmetry, time_zero=self.time_zero, bin_size=packing,
                         time=self.time.bin(packing), uncertainty=self.uncertainty.bin(packing), alpha=self.alpha)

    def correct(self, alpha):
        """ Returns a new asymmetry corrected to the provided value.

        Does not alter the asymmetry object. Asymmetry is first correct back to a value of 1 before being corrected
        to the provided value. If alpha of asymmetry is already equal to provided value, the current asymmetry object
        is returned.

        Parameters
        ----------
        alpha : float
            Alpha value to correct the current asymmetry to.

        Returns
        -------
        asymmetry : Asymmetry
            A new asymmetry object corrected to the provided value.
        """
        if self.alpha == alpha:
            return Asymmetry(input_array=self, time_zero=self.time_zero, bin_size=self.bin_size,
                             time=self.time, uncertainty=self.uncertainty, alpha=1)

        current_asymmetry = self

        if self.alpha != 1:
            current_asymmetry = self.raw()

        input_array = ((alpha - 1) + ((alpha + 1) * current_asymmetry)) / \
                      ((alpha + 1) + ((alpha - 1) * current_asymmetry))

        return Asymmetry(input_array=input_array, time_zero=self.time_zero, bin_size=self.bin_size,
                         time=self.time, uncertainty=self.uncertainty, alpha=alpha)

    def raw(self):
        """ Returns a new asymmetry corrected (or uncorrected) to a value of 1.

        Does not alter the current asymmetry object. If alpha of asymmetry is already 1, the current asymmetry object
        is returned.

        Returns
        -------
        asymmetry : Asymmetry
            A new asymmetry object corrected to a value of 1.
        """
        if self.alpha == 1:
            return Asymmetry(input_array=self, time_zero=self.time_zero, bin_size=self.bin_size,
                         time=self.time, uncertainty=self.uncertainty, alpha=1)

        input_array = ((1 - self.alpha) + (1 + self.alpha) * self) / \
                      ((1 + self.alpha) + (1 - self.alpha) * self)

        return Asymmetry(input_array=input_array, time_zero=self.time_zero, bin_size=self.bin_size,
                         time=self.time, uncertainty=self.uncertainty, alpha=1)

    def cut(self, min_time, max_time):
        """ Returns a new asymmetry cut between the specified times.

        Does not alter the current asymmetry object. Based on the Time attribute of the asymmetry.

        Parameters
        ----------
        min_time : float
            Lower boundary of the time for the new asymmetry.
        max_time : float
            Upper boundary of the time for the new asymmetry.

        Returns
        -------
        asymmetry : Asymmetry
            A new asymmetry object cut between the specified times.
        """
        start_index = 0

        if min_time is None:
            min_time = self.time[0] - 1

        if max_time is None:
            max_time = self.time[-1] + 1

        for i, n in enumerate(self.time):
            if n >= min_time:
                start_index = i
                break

        for i, n in enumerate(self.time):
            if n >= max_time:
                end_index = i
                break
        else:
            end_index = len(self)

        return Asymmetry(input_array=self[start_index: end_index], time_zero=self.time_zero, bin_size=self.bin_size,
                         time=self.time[start_index: end_index], uncertainty=self.uncertainty[start_index: end_index],
                         alpha=self.alpha)


class Uncertainty(np.ndarray):
    """
        Represents the calculated uncertainty from taking the asymmetry of two histograms with the corresponding
        attributes. Inherits from numpy.ndarray so we can perform numpy calculations on it with casting it to an
        numpy array.
        """

    def __new__(cls, input_array=None, bin_size=None, histogram_one=None, histogram_two=None, **kwargs):
        if (input_array is None or bin_size is None) and (histogram_one is None or histogram_two is None):
            raise ValueError("Not enough constructor parameters satisfied")

        if input_array is None:
            start_bin_one, start_bin_two, end_bin_one, end_bin_two, time_zero = histogram_one.intersect(histogram_two)
            histogram_one_good = histogram_one[start_bin_one - 1: end_bin_one + 1]
            histogram_two_good = histogram_two[start_bin_one - 1: end_bin_one + 1]
            d_histogram_one = np.sqrt(histogram_one_good)
            d_histogram_two = np.sqrt(histogram_two_good)
            np.nan_to_num(histogram_one_good)
            np.nan_to_num(histogram_two_good)
            np.seterr(divide='ignore', invalid='ignore')
            input_array = np.array(np.sqrt(np.power(
                (2 * histogram_one_good * d_histogram_two / np.power(histogram_two_good + histogram_one_good, 2)), 2) +
                                           np.power((2 * histogram_two_good * d_histogram_one / np.power(
                                               histogram_two_good + histogram_one_good, 2)), 2)))
            np.seterr(divide='warn', invalid='warn')
            np.nan_to_num(input_array, copy=False)

            if histogram_one.bin_size != histogram_two.bin_size:
                raise ValueError("Histograms do not have the same bin size")
            bin_size = histogram_one.bin_size

        self = np.asarray(input_array).view(cls)
        self.bin_size = float(bin_size)

        return self

    def __reduce__(self):
        pickled_state = super(Uncertainty, self).__reduce__()

        new_state = pickled_state[2] + (self.__dict__,)

        # Parenthesis are not redundant, don't remove.
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state, **kwargs):
        self.__dict__.update(state[-1])
        super(Uncertainty, self).__setstate__(state[0:-1])

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self.bin_size = getattr(obj, 'bin_size', None)

    @classmethod
    def from_array(cls):
        pass

    @classmethod
    def from_histogram(cls):
        pass

    def bin(self, packing):
        bin_full = self.bin_size / 1000
        bin_binned = float(packing) / 1000
        num_bins = len(self)

        if bin_binned <= bin_full:
            return self

        binned_indices_per_bin = int(np.round(bin_binned / bin_full))
        binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
        leftover_bins = int(num_bins % binned_indices_per_bin)

        if leftover_bins:
            reshaped_uncertainty = np.reshape(self[:-leftover_bins],
                                              (binned_indices_total, binned_indices_per_bin))
        else:
            reshaped_uncertainty = np.reshape(self, (binned_indices_total, binned_indices_per_bin))

        binned_uncertainty = 1 / binned_indices_per_bin * np.sqrt(np.apply_along_axis(np.sum, 1,
                                                                                      reshaped_uncertainty ** 2))

        return binned_uncertainty


class Time(np.ndarray):
    """
        Represents the calculated uncertainty from taking the asymmetry of two histograms with the corresponding
        attributes. Inherits from numpy.ndarray so we can perform numpy calculations on it with casting it to an
        numpy array.
        """

    def __new__(cls, input_array=None, bin_size=None, length=None, time_zero=None, run_id=None, time_zero_exact=None,
                **kwargs):
        if (input_array is None) and (
                bin_size is None or length is None or (time_zero is None and time_zero_exact is None)):
            raise ValueError("No parameters for time constructor may be None")
        if input_array is None and time_zero_exact is not None:
            input_array = (np.arange(length) * float(bin_size) / 1000) + time_zero_exact
        elif input_array is None:
            input_array = (np.arange(length) * float(bin_size) / 1000) + \
                          (time_zero * float(bin_size) / 1000)

        self = np.asarray(input_array).view(cls)
        self.bin_size = float(bin_size)
        self.length = float(length)
        self.time_zero = 0 if time_zero is None else float(time_zero)
        self.id = run_id

        return self

    def __reduce__(self):
        pickled_state = super(Time, self).__reduce__()

        new_state = pickled_state[2] + (self.__dict__,)

        # Parenthesis are not redundant, don't remove.
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state, **kwargs):
        self.__dict__.update(state[-1])
        super(Time, self).__setstate__(state[0:-1])

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self.length = getattr(obj, 'length', None)
        self.bin_size = getattr(obj, 'bin_size', None)
        self.time_zero = getattr(obj, 'time_zero', None)
        self.id = getattr(obj, 'id', None)

    def bin(self, packing):
        bin_full = float(self.bin_size) / 1000
        bin_binned = float(packing) / 1000
        num_bins = len(self)
        t0 = self.time_zero

        if bin_binned <= bin_full:
            return self

        binned_indices_per_bin = int(np.round(bin_binned / bin_full))
        binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
        time_per_binned = binned_indices_per_bin * bin_full

        return (np.arange(binned_indices_total) * time_per_binned) + (t0 * bin_full) + (time_per_binned / 2)


# min, max
class FFT:
    def __init__(self, asymmetry, time):
        f_min = 0
        f_max = 1
        f_step = (f_max - f_min) / 100
        z_min = 2 * np.pi * f_min
        z_max = 2 * np.pi * f_max
        z_step = 2 * np.pi * f_step

        low_step = int(np.ceil((z_min - 1e-8) / z_step))
        high_step = int(np.floor((z_max + 1e-8) / z_step)) + 1
        z = np.arange(low_step, high_step) * z_step

        try:
            x_step = time[1] - time[0]
        except IndexError:
            self.z = [0]
            self.fft = [0]
            return

        if (time[0] - 0.01 * x_step) > 0:
            nn = int(np.round(time[0] / x_step))
            add_me = np.linspace(0.0, time[0] - x_step, nn)
            time = np.concatenate((add_me, time))
            asymmetry = np.concatenate((0.0 * add_me, asymmetry))

        x_max_z_step = np.pi / z_step
        nin = len(time)
        n_base = max([nin, high_step, x_max_z_step / x_step])
        n_log_2 = int(np.ceil(np.log2(n_base)))
        n_out = 2 ** n_log_2
        x_max_db = 2 * n_out * x_step
        y_in_db = np.concatenate((asymmetry, np.zeros(2 * n_out - nin)))
        cy_out_db = np.fft.fft(y_in_db) * x_max_db
        fz_db = cy_out_db
        z_step_fine = 2 * np.pi / x_max_db
        z_fine = np.arange(n_out) * z_step_fine
        fz_fine = fz_db[:n_out]
        fzr = np.interp(z, z_fine, np.real(fz_fine))
        fzi = np.interp(z, z_fine, np.imag(fz_fine))

        if z[0] + 0.0001 * z_step < 0:
            nn = int(np.round(-z[0] / z_step))
            fzr[:nn] = 1.0 * fzr[2 * nn:nn:-1]
            fzi[:nn] = -1.0 * fzi[2 * nn:nn:-1]

        fz = fzr + 1j * fzi

        z = z / (2 * np.pi)
        fft = np.real(fz * np.conj(fz))

        self.z = z
        self.fft = fft


class Fit:
    def __init__(self, parameters, expression, title, run_id, meta, asymmetry: Asymmetry):
        self.id = str(uuid.uuid4())
        self.parameters = parameters
        self.string_expression = expression
        self.expression = None
        self.title = title
        self.run_id = run_id
        self.meta = meta
        self.asymmetry = asymmetry

    def write(self, out_file, bin_size=None, x_min=None, x_max=None):
        meta_string = files.TITLE_KEY + ":" + str(self.title) + "," \
                      + files.BIN_SIZE_KEY + ":" + str(bin_size if bin_size else self.meta[files.BIN_SIZE_KEY]) + "," \
                      + files.TEMPERATURE_KEY + ":" + str(self.meta[files.TEMPERATURE_KEY]) + "," \
                      + files.FIELD_KEY + ":" + str(self.meta[files.FIELD_KEY]) + "," \
                      + files.T0_KEY + ":" + str(self.meta[files.T0_KEY])  # TODO not correct t0, need to fix that.

        runs = services.RunService().get_runs_by_ids([self.run_id])

        if len(runs) == 0:
            raise Exception("Run ID in fit '{}' did not match any in database.".format(self.title))

        run = runs[0]

        asymmetry = run.asymmetries[RunDataset.FULL_ASYMMETRY]
        for v in self.parameters.values():
            if v.symbol == "\u03B1":
                asymmetry = asymmetry.correct(v.value)

        if bin_size:
            asymmetry = asymmetry.bin(bin_size)

        if x_min or x_max:
            asymmetry = asymmetry.cut(x_min, x_max)

        if self.expression:
            calculated_asymmetry = self.expression(asymmetry.time, **{v.symbol: v.value for v in self.parameters.values()})
        else:
            raise Exception("Expression has not been created for fit '{}'".format(self.title))

        np.savetxt(out_file, np.c_[asymmetry.time, asymmetry, calculated_asymmetry, asymmetry.uncertainty],
                   fmt='%2.9f, %2.4f, %2.4f, %2.4f',
                   header="BEAMS\n" + meta_string + "\nTime, Asymmetry, Calculated, Uncertainty")


class FitDataset:
    class Flags:
        GLOBAL = 1
        GLOBAL_PLUS = 2
        BATCH = 3

    def __init__(self):
        t = time.localtime()
        current_time = time.strftime("%d-%m-%YT%H:%M:%S", t)

        self.id = str(current_time)
        self.title = self.id
        self.fits = {}
        self.flags = 0
        self.expression = None

    def write(self, out_file, verbose_format=True):
        if verbose_format:
            fit_parameters_string = "# Fit Parameters\n\n# {:<8}{:<10}{:<8}{:<8}".format("Name", "Value", "Lower", "Upper") + "\n\n"
            if self.flags & FitDataset.Flags.GLOBAL or self.flags & FitDataset.Flags.GLOBAL_PLUS:
                fit_parameters_string += "# Common parameters for all runs\n\n"

                f = list(self.fits.values())[0]
                for name, v in f.parameters.items():
                    if v.is_global:
                        fit_parameters_string += "\t" + "{:<8}{:<10.5f}{:<10.5f}{:<8.5f}{:<8.5f}".format(v.symbol, v.value, v.uncertainty, v.lower, v.upper) + "\n"

                fit_parameters_string += "\n"

            for f in self.fits.values():
                run = services.RunService().get_runs_by_ids([f.run_id])[0]
                fit_parameters_string += "# Specific parameters for run {}\n\n".format(run.meta["RunNumber"])

                for name, v in f.parameters.items():
                    if not v.is_global:
                        fit_parameters_string += "\t" + "{:<8}{:<10.5f}{:<10.5f}{:<8.5f}{:<8.5f}".format(v.symbol, v.value, v.uncertainty, v.lower, v.upper) + "\n"

                fit_parameters_string += "\n"

            with open(out_file, 'w', encoding="utf-8") as out_file_object:
                out_file_object.write("#BEAMS\n"
                                      + fit_parameters_string
                                      + "# Expression\n\n\t"
                                      + "A(t) = " + self.expression)

        else:
            full_string = ""

            f = list(self.fits.values())[0]

            for name, v in f.parameters.items():
                full_string += "{:<8}\t".format(name)

            full_string += "{:<8}".format("RUN") + "\n"

            for f in self.fits.values():
                for name, v in f.parameters.items():
                    full_string += "{:<8}\t".format("{:.5f}".format(v.value))
                run = services.RunService().get_runs_by_ids([f.run_id])[0]
                full_string += "{:<8}".format(run.meta["RunNumber"]) + "\n"

            with open(out_file, 'w', encoding="utf-8") as out_file_object:
                out_file_object.write("#BEAMS\n"
                                      + full_string)


class RunDataset:
    FULL_ASYMMETRY = 1
    LEFT_BINNED_ASYMMETRY = 2
    RIGHT_BINNED_ASYMMETRY = 3

    def __init__(self):
        self.id = str(uuid.uuid4())

        self.histograms = {}

        self.asymmetries = {
            self.FULL_ASYMMETRY: None,
            self.LEFT_BINNED_ASYMMETRY: None,
            self.RIGHT_BINNED_ASYMMETRY: None
        }

        self.meta = None
        self.file = None
        self.histograms_used = []
        self.isLoaded = False

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.id == self.id

    def write(self, out_file, bin_size=None):
        if self.asymmetries[self.FULL_ASYMMETRY] is not None:
            meta_string = files.TITLE_KEY + ":" + str(self.meta[files.TITLE_KEY]) + "," \
                          + files.BIN_SIZE_KEY + ":" + str(bin_size) + "," \
                          + files.RUN_NUMBER_KEY + ":" + str(self.meta[files.RUN_NUMBER_KEY]) + "," \
                          + files.TEMPERATURE_KEY + ":" + str(self.meta[files.TEMPERATURE_KEY]) + "," \
                          + files.FIELD_KEY + ":" + str(self.meta[files.FIELD_KEY]) + "," \
                          + files.T0_KEY + ":" + str(self.asymmetries[self.FULL_ASYMMETRY].time.time_zero)

            if bin_size:
                asymmetry = self.asymmetries[RunDataset.FULL_ASYMMETRY].bin(bin_size)
            else:
                asymmetry = self.asymmetries[RunDataset.FULL_ASYMMETRY]

            np.savetxt(out_file, np.c_[asymmetry.time, asymmetry, asymmetry.uncertainty],
                       fmt='%2.9f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "\nTime, Asymmetry, Uncertainty")


class FileDataset:
    def __init__(self, file):
        self.id = str(uuid.uuid4())

        self.file = file
        self.file_path = file.file_path
        self.title = os.path.split(file.file_path)[1]
        self.isLoaded = False
        self.dataset = None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.id == self.id


class DataBuilder:
    @staticmethod
    def build_minimal(f):
        if not isinstance(f, File):
            f = files.file(f)

        # fixme add conditional for fits and sessions
        if f.DATA_FORMAT == files.Format.HISTOGRAM or \
                f.DATA_FORMAT == files.Format.ASYMMETRY:
            run = RunDataset()
            run.meta = f.read_meta()
            run.file = f
            return run
        else:
            return None

    @staticmethod
    def build_full(f, d=None):
        if not isinstance(f, File):
            f = files.file(f)

        # fixme add conditional for fits
        if d is None or (not isinstance(d, RunDataset) and not isinstance(d, FitDataset)):
            if f.DATA_FORMAT == files.Format.HISTOGRAM or \
                    f.DATA_FORMAT == files.Format.ASYMMETRY:
                d = RunDataset()
                d.meta = f.read_meta()
                d.file = f

        # fixme add conditional for fits and sessions
        if f.DATA_FORMAT == files.Format.HISTOGRAM:
            data = f.read_data()
            for histogram_title in d.meta[files.HIST_TITLES_KEY]:
                values = np.array(data[histogram_title].values)
                histogram = Histogram(time_zero=d.meta[files.T0_KEY][histogram_title],
                                      good_bin_start=d.meta[files.GOOD_BIN_ONE_KEY][histogram_title],
                                      good_bin_end=d.meta[files.GOOD_BIN_TWO_KEY][histogram_title],
                                      background_start=d.meta[files.BACKGROUND_ONE_KEY][histogram_title],
                                      background_end=d.meta[files.BACKGROUND_TWO_KEY][histogram_title],
                                      title=histogram_title,
                                      run_id=d.id,
                                      bin_size=d.meta[files.BIN_SIZE_KEY],
                                      input_array=values)
                d.histograms[histogram_title] = histogram
            d.isLoaded = True

        elif f.DATA_FORMAT == files.Format.ASYMMETRY:
            data = f.read_data()
            asymmetry_values = np.array(data['Asymmetry'].values)
            uncertainty_values = np.array(data['Uncertainty'].values)
            time_values = np.array(data['Time'].values)

            asymmetry = Asymmetry(input_array=asymmetry_values,
                                  time_zero=d.meta[files.T0_KEY],
                                  bin_size=d.meta[files.BIN_SIZE_KEY],
                                  uncertainty=uncertainty_values,
                                  time=time_values)

            d.asymmetries[d.FULL_ASYMMETRY] = asymmetry
            d.histograms = None
            d.isLoaded = True

        return d
