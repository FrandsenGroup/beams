import os
import sys, traceback

import numpy as np
import uuid

from app.model import files, fit
from app.model.files import File


class Histogram(np.ndarray):
    """
    Represents a histogram with its accompanying attributes. Inherits from numpy.ndarray so we can perform
    numpy calculations on it with casting it to an numpy array.
    """

    def __new__(cls, input_array=None, time_zero=None, good_bin_start=None, good_bin_end=None,
                background_start=None, background_end=None, title=None, run_id=None, bin_size=None, **kwargs):

        if input_array is None or time_zero is None or good_bin_end is None or good_bin_start is None or \
                background_start is None or background_end is None or title is None or bin_size is None:
            raise ValueError("No parameters for Histogram constructor may be None")

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

    def intersect(self, other):
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
        return np.mean(self[int(self.background_start):int(self.background_end) - 1])

    def combine(self, histogram):
        pass


class Asymmetry(np.ndarray):
    """
    Represents an asymmetry of two histograms with the corresponding attributes. Inherits from numpy.ndarray so we
    can perform numpy calculations on it with casting it to an numpy array.
    """

    def __new__(cls, input_array=None, time_zero=None, bin_size=None, histogram_one=None, histogram_two=None,
                uncertainty=None, time=None, alpha=None, **kwargs):
        if (input_array is None or time_zero is None or bin_size is None or uncertainty is None or time is None) \
                and (histogram_one is None or histogram_two is None):
            raise ValueError("Not enough constructor parameters satisfied")

        if input_array is None:
            start_bin_one, start_bin_two, end_bin_one, end_bin_two, time_zero = histogram_one.intersect(histogram_two)
            background_one = histogram_one.background_radiation()
            background_two = histogram_two.background_radiation()
            histogram_one_good = histogram_one[start_bin_one - 1: end_bin_one + 1]
            histogram_two_good = histogram_two[start_bin_one - 1: end_bin_one + 1]
            input_array = ((histogram_one_good - background_one) - (histogram_two_good - background_two)) / \
                          ((histogram_two_good - background_two) + (histogram_one_good - background_one))

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

    def _bin_asymmetry(self, packing):
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

        return binned_asymmetry

    def bin(self, packing):
        return Asymmetry(input_array=self._bin_asymmetry(packing), time_zero=self.time_zero, bin_size=packing,
                         time=self.time.bin(packing), uncertainty=self.uncertainty.bin(packing), alpha=self.alpha)

    def correct(self, alpha):
        print('correct')
        # print(self)

        input_array = ((alpha - 1) + ((alpha + 1) * self)) / \
                      ((alpha + 1) + ((alpha - 1) * self))
        # print(input_array)

        return Asymmetry(input_array=input_array, time_zero=self.time_zero, bin_size=self.bin_size,
                         time=self.time, uncertainty=self.uncertainty, alpha=alpha)

    def raw(self):
        print('raw')
        # traceback.print_stack()
        # print(self)
        if self.alpha == 1:
            return self

        input_array = ((1 - self.alpha) + (1 + self.alpha) * self) / \
                      ((1 + self.alpha) + (1 - self.alpha) * self)
        # print(input_array)

        return Asymmetry(input_array=input_array, time_zero=self.time_zero, bin_size=self.bin_size,
                         time=self.time, uncertainty=self.uncertainty, alpha=1)

    def cut(self, min_time, max_time):
        start_index = 0

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
            input_array = np.array(np.sqrt(np.power((2 * histogram_one_good * d_histogram_two / np.power(histogram_two_good + histogram_one_good, 2)), 2) +
                                           np.power((2 * histogram_two_good * d_histogram_one / np.power(histogram_two_good + histogram_one_good, 2)), 2)))
            np.seterr(divide='warn', invalid='warn')
            np.nan_to_num(input_array, copy=False)

            if histogram_one.bin_size != histogram_two.bin_size:
                raise ValueError("Histograms do not have the same bin size")
            bin_size = histogram_one.bin_size

        self = np.asarray(input_array).view(cls)
        self.bin_size = float(bin_size)

        return self

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

    def __new__(cls, input_array=None, bin_size=None, length=None, time_zero=None, run_id=None, time_zero_exact=None, **kwargs):
        if (input_array is None) and (bin_size is None or length is None or (time_zero is None and time_zero_exact is None)):
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
        self.isLoaded = False

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.id == self.id

    def write(self, out_file, bin_size=None):
        meta_string = files.TITLE_KEY + ":" + str(self.meta[files.TITLE_KEY]) + "," \
                      + files.BIN_SIZE_KEY + ":" + str(bin_size) + "," \
                      + files.TEMPERATURE_KEY + ":" + str(self.meta[files.TEMPERATURE_KEY]) + "," \
                      + files.FIELD_KEY + ":" + str(self.meta[files.FIELD_KEY]) + "," \
                      + files.T0_KEY + ":" + str(self.meta[files.T0_KEY])

        if bin_size:
            asymmetry = self.asymmetries[RunDataset.FULL_ASYMMETRY].bin(bin_size)
        else:
            asymmetry = self.asymmetries[RunDataset.FULL_ASYMMETRY]

        np.savetxt(out_file, np.c_[asymmetry.time, asymmetry, asymmetry.uncertainty],
                   fmt='%2.9f, %2.4f, %2.4f', header="BEAMS\n" + meta_string + "\nTime, Asymmetry, Uncertainty")


class FileDataset:
    def __init__(self, file: File):
        self.id = str(uuid.uuid4())

        self.file = file
        self.file_path = file.file_path
        self.title = os.path.split(file.file_path)[1]
        self.isLoaded = False
        self.dataset = None

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.id == self.id


class Database:
    runs = {}
    fits = {}
    files = {}


class RunDAO:
    __database = Database()

    def get_runs(self):
        return self.__database.runs.values()

    def get_runs_by_ids(self, ids):
        return [self.__database.runs[rid] for rid in ids]

    def add_runs(self, runs):
        for run in runs:
            self.__database.runs[run.id] = run

    def remove_runs_by_ids(self, ids):
        for rid in ids:
            self.__database.runs.pop(rid)

    def update_runs_by_id(self, ids, runs):
        for rid, run in zip(ids, runs):
            self.__database.runs[rid] = run

    def clear(self):
        self.__database.runs = {}


class FitDAO:
    __database = Database()

    def get_fits(self):
        return self.__database.fits.values()

    def get_fits_by_ids(self, ids):
        return [self.__database.fits[fid] for fid in ids]

    def add_fits(self, fits):
        for fit in fits:
            self.__database.fits[fit.id] = fit

    def remove_runs_by_ids(self, ids):
        for fid in ids:
            self.__database.fits.pop(fid)

    def clear(self):
        self.__database.fits = {}


class FileDAO:
    __database = Database()

    def get_files(self):
        return self.__database.files.values()

    def get_files_by_ids(self, ids):
        return [self.__database.files[file_id] for file_id in ids]

    def get_files_by_path(self, path):
        for file in self.__database.files.values():
            if file.file_path == path:
                return file

    def add_files(self, file_datasets):
        for dataset in file_datasets:
            self.__database.files[dataset.id] = dataset

    def remove_files_by_paths(self, paths):
        for path in paths:
            self.__database.files.pop(path)

    def remove_files_by_id(self, fid):
        self.__database.files.pop(fid)

    def clear(self):
        self.__database.files = {}


class NotificationService:
    __observers = {}

    def register(self, signal, observer):
        if signal not in self.__observers.keys():
            self.__observers[signal] = [observer]
        else:
            self.__observers[signal].append(observer)

    def notify(self, signal):
        if signal in self.__observers.keys():
            for observer in self.__observers[signal]:
                observer.update()


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
        if d is None or (not isinstance(d, RunDataset) and not isinstance(d, fit.FitDataset)):
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
            time_values = np.array(data['Values'].values)

            asymmetry = Asymmetry(input_array=asymmetry_values,
                                  time_zero=d.meta[files.T0_KEY],
                                  bin_size=d.meta[files.BIN_SIZE_KEY],
                                  uncertainty=uncertainty_values,
                                  time=time_values)

            d.asymmetries[d.FULL_ASYMMETRY] = asymmetry
            d.histograms = None
            d.isLoaded = True

        return d


class RunService:
    RUNS_ADDED = 0
    RUNS_LOADED = 1
    RUNS_CHANGED = 2

    __dao = RunDAO()
    __notifier = NotificationService()

    def register(self, signal, observer):
        self.__notifier.register(signal, observer)

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

    def add_runs(self, paths):
        builder = DataBuilder()
        for path in paths:
            run = builder.build_minimal(path)
            self.__dao.add_runs([run])

        self.__notifier.notify(RunService.RUNS_ADDED)

    def remove_runs_by_ids(self, ids):
        self.__dao.remove_runs_by_ids(ids)
        self.__notifier.notify(RunService.RUNS_LOADED)

    def add_dataset(self, datasets):
        self.__dao.add_runs(datasets)
        self.__notifier.notify(RunService.RUNS_ADDED)

    def update_runs_by_ids(self, ids, asymmetries):
        self.__dao.update_runs_by_id(ids, asymmetries)
        self.__notifier.notify(RunService.RUNS_CHANGED)

    def update_alphas(self, ids, alphas):
        for rid, alpha in zip(ids, alphas):
            run = self.__dao.get_runs_by_ids([rid])[0]

            if run.asymmetries[RunDataset.FULL_ASYMMETRY].alpha != 1:
                run.asymmetries[RunDataset.FULL_ASYMMETRY] = run.asymmetries[RunDataset.FULL_ASYMMETRY].raw()

            run.asymmetries[RunDataset.FULL_ASYMMETRY] = run.asymmetries[RunDataset.FULL_ASYMMETRY].correct(alpha)

            if run.asymmetries[RunDataset.LEFT_BINNED_ASYMMETRY] is not None:
                run.asymmetries[RunDataset.LEFT_BINNED_ASYMMETRY] = run.asymmetries[RunDataset.FULL_ASYMMETRY].bin(run.asymmetries[RunDataset.LEFT_BINNED_ASYMMETRY].bin_size)
                run.asymmetries[RunDataset.RIGHT_BINNED_ASYMMETRY] = run.asymmetries[RunDataset.FULL_ASYMMETRY].bin(run.asymmetries[RunDataset.RIGHT_BINNED_ASYMMETRY].bin_size)

        self.__notifier.notify(RunService.RUNS_CHANGED)

    def changed(self):
        self.__notifier.notify(RunService.RUNS_ADDED)


class FitService:
    FITS_ADDED = 1

    __dao = FitDAO()
    __notifier = NotificationService()

    def get_fit_datasets(self):
        return self.__dao.get_fits()

    def add_dataset(self, datasets):
        self.__dao.add_fits(datasets)
        self.__notifier.notify(FitService.FITS_ADDED)

    def changed(self):
        self.__notifier.notify(FitService.FITS_ADDED)

    def register(self, signal, observer):
        self.__notifier.register(signal, observer)


class FileService:
    FILES_CHANGED = 0

    __dao = FileDAO()
    __run_service = RunService()
    __fit_service = FitService()
    __notifier = NotificationService()

    def register(self, signal, observer):
        self.__notifier.register(signal, observer)

    def get_files(self, ids=None):
        if ids is not None:
            return self.__dao.get_files_by_ids(ids)
        else:
            return self.__dao.get_files()

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
        for path in paths:
            if self.__dao.get_files_by_path(path) is not None:
                continue

            f = files.file(path)
            data_set = DataBuilder.build_minimal(f)
            file_set = FileDataset(f)

            if data_set is not None:
                file_set.dataset = data_set
                file_set.title = data_set.meta[files.TITLE_KEY]

                if isinstance(data_set, RunDataset):
                    self.__run_service.add_dataset([data_set])
                else:
                    self.__fit_service.add_dataset([data_set])

            self.__dao.add_files([file_set])

        self.__notifier.notify(self.FILES_CHANGED)

    def load_files(self, ids):
        is_changed = False

        for file_dataset in self.__dao.get_files_by_ids(ids):
            if not file_dataset.isLoaded:
                is_changed = True
                DataBuilder.build_full(file_dataset.file, file_dataset.dataset)
                file_dataset.isLoaded = True

        if is_changed:
            self.__notifier.notify(self.FILES_CHANGED)
            self.__run_service.changed()
            self.__fit_service.changed()

    def remove_files(self, checked_items):
        rfiles = self.__dao.get_files_by_ids(checked_items)
        run_ids = []
        for rf in rfiles:
            if rf.isLoaded:
                run_ids.append(rf.dataset.id)
            self.__dao.remove_files_by_id(rf.id)

        self.__run_service.remove_runs_by_ids(run_ids)
        self.__notifier.notify(self.FILES_CHANGED)

