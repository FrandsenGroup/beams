# Standard Library Packages
import abc
import gzip
import os
import pickle
import re
import sys
import subprocess
import enum

# Installed Packages
import numpy as np
import h5py  # ISIS
import musr2py  # PSI
import regex  # python re doesn't support variable length look behinds

from app.resources import resources


# File Extensions
class Extensions:
    SESSION = ".beams"
    FIT_SUMMARY_VERBOSE = ".fit"
    FIT = ".calc"
    ASYMMETRY = ".asy"
    HISTOGRAM = ".dat"
    TRIUMF = '.msr'
    PSI_BIN = '.bin'
    PSI_MDU = '.mdu'
    ISIS_NXS = '.nxs'
    ISIS_NXS_V2 = '.nxs_v2'
    INTEGRATION = '.int'
    PARAMETER = '.prm'


# File Sources
@enum.unique
class Source(enum.Enum):
    UNKNOWN = -1
    TRIUMF = 0
    PSI = 1
    ISIS = 2
    JPARC = 3
    BEAMS = 4


# File Formats
@enum.unique
class Format(enum.Enum):
    UNKNOWN = -1
    HISTOGRAM = 0
    ASYMMETRY = 1
    BINARY = 2
    PICKLED = 3
    FIT = 4
    FIT_SET = 5
    FIT_SET_VERBOSE = 6


# File Data
@enum.unique
class DataType(enum.Enum):
    UNKNOWN = -1
    MUON = 0


# Meta Keys
FIELD_KEY = 'Field'
TEMPERATURE_KEY = 'Temperature'
BIN_SIZE_KEY = 'BinSize'
TITLE_KEY = 'Title'
HIST_TITLES_KEY = 'HistTitles'
BACKGROUND_ONE_KEY = 'BkgdOne'
BACKGROUND_TWO_KEY = 'BkgdTwo'
GOOD_BIN_ONE_KEY = 'GoodBinOne'
GOOD_BIN_TWO_KEY = 'GoodBinTwo'
RUN_NUMBER_KEY = 'RunNumber'
T0_KEY = 'T0'
CALC_HISTS_KEY = 'CalcHists'
COMBINED_RUNS_KEY = 'CombinedRuns'
FILE_PATH_KEY = 'FilePath'
LAB_KEY = "Lab"
AREA_KEY = "Area"
SAMPLE_KEY = "Sample"
ORIENTATION_KEY = "Orientation"


# TODO Maybe we should have these files inherit from the actual File object
#   this way we can use 'with'. Not super necessary, kinda fun though.
class File(abc.ABC):
    """
    Abstract base class for file objects, establishes some static constants and a constructor.
    """

    DATA_TYPE = None
    DATA_FORMAT = None
    SOURCE = None

    def __init__(self, file_path):
        self.file_path = file_path


class ReadableFile(File, abc.ABC):
    """
    Abstract base class for a readable file object, this is any file for which we can directly read
    data with which the program can interact with.
    """
    HEADER_ROWS = None

    @abc.abstractmethod
    def read_data(self):
        """
        Reads the data (starting after HEADER_ROWS # of rows) and returns a structure expected for
        the given file data type and source (handled by the RunBuilder)

        :return data: An array structure expected for that file type (handled by RunBuilder)
        """
        raise NotImplemented()

    @abc.abstractmethod
    def read_meta(self):
        """
        Reads HEADER_ROWS # of rows and returns the associated meta data as a dictionary.

        :return meta: A dictionary of key: value pairs associated with given headers
        """
        raise NotImplemented()

    def __repr__(self):
        return f'ReadableFile({self.file_path}, {self.SOURCE}, {self.DATA_FORMAT}, {self.DATA_TYPE})'


class ConvertibleFile(File, abc.ABC):
    """
    Abstract base class for a convertible file object, which is any file which we can't read
    data from directly but have to convert to a readable BEAMS data file.
    """

    @abc.abstractmethod
    def convert(self, out_file) -> ReadableFile:
        """
        Takes as an argument the file path to which the converted data will be written and returns
        a ReadableFile object referencing that file path.

        :param out_file: the file path to which the converted data will be written
        :return: ReadableFile: returns a ReadableFile object
        :raises: ConversionError: if there is a subprocess or similar error converting the file
        """
        raise NotImplemented()

    def __repr__(self):
        return f'ConvertibleFile({self.file_path}, {self.SOURCE}, {self.DATA_FORMAT}, {self.DATA_TYPE})'


class UnknownFile(File):
    DATA_TYPE = DataType.UNKNOWN
    DATA_FORMAT = Format.UNKNOWN
    SOURCE = Source.UNKNOWN

    def __repr__(self):
        return f'UnknownFile({self.file_path}, {self.SOURCE}, {self.DATA_FORMAT}, {self.DATA_TYPE})'


class BeamsSessionFile(ReadableFile):
    HEADER_ROWS = 0
    DATA_FORMAT = Format.PICKLED

    def read_data(self):
        with gzip.GzipFile(self.file_path, 'rb') as session_file_object:
            try:
                return pickle.load(session_file_object)
            except Exception as e:
                raise BeamsFileReadError("This session file is not supported by your current version of BEAMS.") from e

    def read_meta(self):
        return self.file_path


class TRIUMFMuonFile(ConvertibleFile):
    SOURCE = Source.TRIUMF
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        flags = ['-all']
        if is_found(self.file_path) and check_ext(self.file_path, Extensions.TRIUMF) and check_ext(out_file,
                                                                                                   Extensions.HISTOGRAM):
            system_args = {'win32': [resources.TRIUMF_WINDOWS_CONVERSION, self.file_path, out_file],
                           'linux': ['./' + resources.TRIUMF_LINUX_CONVERSION, self.file_path, out_file],
                           'darwin': [resources.TRIUMF_MAC_CONVERSION, self.file_path, out_file]}

            if sys.platform in system_args.keys():
                args = system_args[sys.platform]

                if flags:
                    args.extend(flags)  # -v (verbose) -all (all metadata) See BEAMS_MUD.c to see other flags.

                if sys.platform == 'win32':
                    shell = True
                else:
                    shell = False
            else:
                raise EnvironmentError("Not on a recognized system.")

            try:
                subprocess.check_call(args, shell=shell)
            except subprocess.CalledProcessError as e:
                raise BeamsFileConversionError("Error occurred running conversion executable.") from e
            else:
                return MuonHistogramFile(out_file)

        raise BeamsFileConversionError("Binary file is in an unknown format. May need to update executables.")


class PSIMuonFile(ConvertibleFile):
    SOURCE = Source.PSI
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def __init__(self, file_path):
        super().__init__(file_path)
        self._combine_format = None

    def set_combine_format(self, is_exacts, starts_or_exacts, ends, names):
        # Check if the values provided are of a valid datatype. Doing this first prevents sneaky bugs.
        if len(is_exacts) != len(starts_or_exacts) or len(starts_or_exacts) != len(ends) or len(ends) != len(names):
            raise Exception("Need to provide all fields for each format")

        for ie, soe, e, n in zip(is_exacts, starts_or_exacts, ends, names):
            try:
                if ie:
                    [int(s) for s in soe]
                else:
                    int(soe)
                    int(e)
            except ValueError:
                raise Exception("Format for combining histograms contains values of invalid types.") from e

        distinct_starts = set([s for i, s in zip(is_exacts, starts_or_exacts) if not i])
        distinct_ends = set([s for i, s in zip(is_exacts, ends) if not i])
        distinct_names = set([s for i, s in zip(is_exacts, names) if not i])

        # Check if any values are repeated or if one set of values is larger then another
        if len(distinct_starts) != len(distinct_ends) or len(distinct_starts) != (len(distinct_names)):
            raise Exception("Invalid format for combining histograms.")

        self._combine_format = (is_exacts, starts_or_exacts, ends, names)

    def get_number_of_histograms(self):
        x = musr2py.MuSR_td_PSI_bin()
        x.read(self.file_path)
        return x.get_numberHisto_int()

    def convert(self, out_file):
        if not check_ext(out_file, Extensions.HISTOGRAM):
            raise Exception("Out file does not have a valid extension (.dat).")

        try:
            x = musr2py.MuSR_td_PSI_bin()
            x.read(self.file_path)

            # Get singular scalars
            num_hists = x.get_numberHisto_int()
            bin_width = x.get_binWidth_ns()
            run_number = x.get_runNumber_int()
            sample_name = x.get_sample().strip()
            temperature = x.get_temp().strip()
            orientation = x.get_orient().strip()
            field = x.get_field().strip()
            title = x.get_comment().strip()

            # Create full histogram array
            data = np.array([x.get_histo_vector(i, 1) for i in range(num_hists)])
            t0_data = x.get_t0_vector()
            first_good_data = x.get_firstGood_vector()
            last_good_data = x.get_lastGood_vector()

            histograms = []
            histograms_t0 = []
            histograms_first_good_bin = []
            histograms_last_good_bin = []
            if self._combine_format:
                is_exacts, starts_or_exacts, ends, hist_title_list = self._combine_format
                for is_exact, start_or_exact, end in zip(is_exacts, starts_or_exacts, ends):
                    if is_exact:
                        histograms_first_good_bin.append(str(max([first_good_data[h] for h in start_or_exact])))
                        histograms_last_good_bin.append(str(max([last_good_data[h] for h in start_or_exact])))
                        max_t0 = max([t0_data[h] for h in start_or_exact])
                        min_t0 = min([t0_data[h] for h in start_or_exact])
                        hist = np.array([])
                        for hi in start_or_exact:
                            hi_t0 = t0_data[hi]
                            hist_to_add = np.roll(data[hi], max_t0 - hi_t0)
                            hist_to_add[:max_t0-min_t0] = 0
                            if len(hist) == 0:
                                hist = hist_to_add
                            else:
                                hist += hist_to_add
                        histograms_t0.append(str(max_t0))
                        histograms.append(hist)
                    else:
                        if end < start_or_exact:
                            histograms_first_good_bin.append(str(max(first_good_data[0:end] + first_good_data[start_or_exact:])))
                            histograms_last_good_bin.append(str(max(last_good_data[0:end] + last_good_data[start_or_exact:])))
                            max_t0 = max(t0_data[0:end] + t0_data[start_or_exact:])
                            min_t0 = min(t0_data[0:end] + t0_data[start_or_exact:])
                            hist = np.array([])
                            for hi in range(0, end):
                                hi_t0 = t0_data[hi]
                                hist_to_add = np.roll(data[hi], max_t0 - hi_t0)
                                hist_to_add[:max_t0 - min_t0] = 0
                                if len(hist) == 0:
                                    hist = hist_to_add
                                else:
                                    hist += hist_to_add
                            for hi in range(start_or_exact, len(data)):
                                hi_t0 = t0_data[hi]
                                hist_to_add = np.roll(data[hi], max_t0 - hi_t0)
                                hist_to_add[:max_t0 - min_t0] = 0
                                if len(hist) == 0:
                                    hist = hist_to_add
                                else:
                                    hist += hist_to_add
                            histograms_t0.append(str(max_t0))
                            histograms.append(hist)
                        else:
                            histograms_first_good_bin.append(str(max(first_good_data[start_or_exact:end])))
                            histograms_last_good_bin.append(str(max(last_good_data[start_or_exact:end])))
                            max_t0 = max(t0_data[start_or_exact:end])
                            min_t0 = min(t0_data[start_or_exact:end])
                            hist = np.array([])
                            for hi in range(start_or_exact, end):
                                hi_t0 = t0_data[hi]
                                hist_to_add = np.roll(data[hi], max_t0 - hi_t0)
                                hist_to_add[:max_t0 - min_t0] = 0
                                if len(hist) == 0:
                                    hist = hist_to_add
                                else:
                                    hist += hist_to_add
                            histograms_t0.append(str(max_t0))
                            histograms.append(hist)
            else:
                hist_title_list = [str(i) if title.isspace() else title for i, title in enumerate(x.get_histoNames_vector())]
                histograms = data
                histograms_t0 = [str(t) for t in t0_data]
                histograms_first_good_bin = [str(f) for f in first_good_data]
                histograms_last_good_bin = [str(l) for l in last_good_data]

            first_background_list = []
            last_background_list = []
            for i, histogram in enumerate(histograms):
                for j, value in enumerate(histogram):
                    if value != 0:
                        to_t0 = int(histograms_t0[i])

                        bins_to_t0 = to_t0 - j
                        first_background = j + int(bins_to_t0 * 0.1)
                        last_background = to_t0 - int(bins_to_t0 * 0.4)

                        if last_background <= first_background:
                            last_background = first_background + 1

                        first_background_list.append(str(first_background))
                        last_background_list.append(str(last_background))

                        break

        except Exception as e:
            raise BeamsFileConversionError(f"An error occurred pulling data from the file. "
                                           f"Error occurred with {self.file_path}.") from e

        # Create our meta string for the top of the file
        meta_string = f"BEAMS\n" \
                      f"{BIN_SIZE_KEY}:{bin_width}," \
                      f"{TEMPERATURE_KEY}:{temperature}," \
                      f"{FIELD_KEY}:{field}," \
                      f"{SAMPLE_KEY}:{sample_name}," \
                      f"{ORIENTATION_KEY}:{orientation}," \
                      f"{RUN_NUMBER_KEY}:{run_number}," \
                      f"{TITLE_KEY}:{title}\n"

        meta_string += ','.join([title.strip() if not title.isspace() else str(i)
                                 for i, title in enumerate(hist_title_list)]) + "\n"
        meta_string += ','.join(first_background_list) + "\n"
        meta_string += ','.join(last_background_list) + "\n"
        meta_string += ','.join(histograms_first_good_bin) + "\n"
        meta_string += ','.join(histograms_last_good_bin) + "\n"
        meta_string += ','.join(histograms_t0)

        try:
            np.savetxt(out_file, np.rot90(histograms, 3), delimiter=',', header=meta_string, comments="", fmt="%-8i")
        except Exception as e:
            raise BeamsFileConversionError(f"An error occurred writing the converted data to the out file. "
                                           f"Error occurred with {self.file_path}.") from e

        return MuonHistogramFile(out_file)


class ISISMuonFile(ConvertibleFile):
    SOURCE = Source.ISIS
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    class DataPaths:
        TITLE = ['raw_data_1/title']
        RUN_NUMBER = ['raw_data_1/run_number']
        SAMPLE_NAME = ['raw_data_1/sample/name']
        AREA = ['raw_data_1/beamline']
        LAB = ['raw_data_1/instrument/source/name']
        RESOLUTION = ['raw_data_1/selog/pulse_width/value']
        TEMPERATURE = ['raw_data_1/sample/temperature', 'raw_data_1/selog/Temp_Sample/value']
        FIELD = ['raw_data_1/sample/magnetic_field', 'raw_data_1/selog/Field_ZF_Magnitude/value']
        HISTOGRAMS = ['raw_data_1/detector_1/counts']

    class Attributes:
        UNITS = ['units']
        FIRST_GOOD_BIN = ['first_good_bin']
        LAST_GOOD_BIN = ['last_good_bin']
        FIRST_BKGD_BIN = ['null']
        LAST_BKGD_BIN = ['null']
        T0_BIN = ['t0_bin']

    def __init__(self, file_path):
        super().__init__(file_path)
        self._combine_format = None

    def set_combine_format(self, is_exacts, starts_or_exacts, ends, names):
        # Check if the values provided are of a valid datatype. Doing this first prevents sneaky bugs.
        if len(is_exacts) != len(starts_or_exacts) or len(starts_or_exacts) != len(ends) or len(ends) != len(names):
            raise Exception("Need to provide all fields for each format")

        for ie, soe, e, n in zip(is_exacts, starts_or_exacts, ends, names):
            try:
                if ie:
                    [int(s) for s in soe]
                else:
                    int(soe)
                    int(e)
            except ValueError:
                raise Exception("Format for combining histograms contains values of invalid types.") from e

        distinct_starts = set([s for i, s in zip(is_exacts, starts_or_exacts) if not i])
        distinct_ends = set([s for i, s in zip(is_exacts, ends) if not i])
        distinct_names = set([s for i, s in zip(is_exacts, names) if not i])

        # Check if any values are repeated or if one set of values is larger then another
        if len(distinct_starts) != len(distinct_ends) or len(distinct_starts) != (len(distinct_names)):
            raise Exception("Invalid format for combining histograms.")

        self._combine_format = (is_exacts, starts_or_exacts, ends, names)

    @staticmethod
    def get_value(data_paths, hdf_file_object, full=None, string=False):
        for path in data_paths:
            if path in hdf_file_object:
                if full:
                    return hdf_file_object[path]
                if string:
                    return str(hdf_file_object[path][0]).strip('b').strip("'")
                return hdf_file_object[path][0]
            elif path == data_paths[-1]:
                raise KeyError("Path not found in HDF file.")

    @staticmethod
    def get_attribute(data_paths, attribute, hdf_file_object, string=False):
        dataset = ISISMuonFile.get_value(data_paths, hdf_file_object, True)

        for att in attribute:
            if att in dataset.attrs:
                if string:
                    return str(dataset.attrs[att]).strip('b').strip("'")
                return dataset.attrs[att]
            elif att == attribute[-1]:
                raise AttributeError("Attribute not found on dataset.")

    def get_number_of_histograms(self):
        f = h5py.File(self.file_path, 'r+')

        try:
            data = self.get_value(self.DataPaths.HISTOGRAMS, f, True)
            return data.shape[1]  # Expected shape is something like 1x64x2048
        except (AttributeError, KeyError) as e:
            raise BeamsFileConversionError("Binary file is in an unknown format.") from e

    def convert(self, out_file):
        if not check_ext(out_file, Extensions.HISTOGRAM):
            raise Exception("Out file does not have a valid extension (.dat).")

        try:
            f = h5py.File(self.file_path, 'r+')
        except OSError:
            raise BeamsFileConversionError("File signature not found. Unable to open this file.")

        try:
            title = self.get_value(self.DataPaths.TITLE, f, string=True)
            run_number = self.get_value(self.DataPaths.RUN_NUMBER, f)
            sample = self.get_value(self.DataPaths.SAMPLE_NAME, f, string=True)
            lab = self.get_value(self.DataPaths.LAB, f, string=True)
            area = self.get_value(self.DataPaths.AREA, f, string=True)
            resolution = self.get_value(self.DataPaths.RESOLUTION, f)

            try:
                resolution_units = str(self.get_attribute(self.DataPaths.RESOLUTION, self.Attributes.UNITS, f, string=True))
            except AttributeError:
                resolution_units = "ns"

            # We want the resolution (bin size) to be in nanoseconds.
            if 'p' in resolution_units:
                resolution *= 1000
            elif '\u00b5' in resolution_units or 'm' in resolution_units:
                resolution /= 1000

            temperature = self.get_value(self.DataPaths.TEMPERATURE, f)
            temperature_units = self.get_attribute(self.DataPaths.TEMPERATURE, self.Attributes.UNITS, f, string=True)
            field = self.get_value(self.DataPaths.FIELD, f)
            field_units = self.get_attribute(self.DataPaths.FIELD, self.Attributes.UNITS, f, string=True)
            t0_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.T0_BIN, f)

            first_good_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.FIRST_GOOD_BIN, f)
            last_good_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.LAST_GOOD_BIN, f)

            try:
                first_bkgd_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.FIRST_BKGD_BIN, f)
            except AttributeError:
                first_bkgd_bin = t0_bin // 4

            try:
                last_bkgd_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.FIRST_BKGD_BIN, f)
            except AttributeError:
                last_bkgd_bin = (t0_bin // 4) * 3
                last_bkgd_bin = last_bkgd_bin if last_bkgd_bin < t0_bin else t0_bin

            data = self.get_value(self.DataPaths.HISTOGRAMS, f, True)
        except (AttributeError, KeyError) as e:
            raise BeamsFileConversionError("Binary file is in an unknown format.") from e

        meta_string = ""
        meta_string += "BEAMS\n"
        meta_string += "{}:{},".format(BIN_SIZE_KEY, resolution)
        meta_string += "{}:{},".format(RUN_NUMBER_KEY, run_number)
        meta_string += "{}:{},".format(TITLE_KEY, title)
        meta_string += "{}:{},".format(LAB_KEY, lab)
        meta_string += "{}:{},".format(AREA_KEY, area)
        meta_string += "{}:{} {},".format(TEMPERATURE_KEY, temperature, temperature_units)
        meta_string += "{}:{} {},".format(FIELD_KEY, field, field_units)
        meta_string += "{}:{}\n".format("Sample", sample)

        if self._combine_format:
            is_exacts, starts_or_exacts, ends, names = self._combine_format
            histograms = []
            for is_exact, start_or_exact, end in zip(is_exacts, starts_or_exacts, ends):
                if is_exact:
                    histograms.append(sum([data[0][i] for i in start_or_exact]))
                else:
                    if end < start_or_exact:
                        histograms.append(sum(data[0][0:end]) + sum(data[0][start_or_exact:]))
                    else:
                        histograms.append(sum(data[0][start_or_exact:end]))
        else:
            names = [str(n) for n in range(self.get_number_of_histograms())]
            histograms = data[0]

        meta_string += '\n'.join([','.join([val if val else name for name in names]) for val in [None,
                                                                                                 str(first_bkgd_bin),
                                                                                                 str(last_bkgd_bin),
                                                                                                 str(first_good_bin),
                                                                                                 str(last_good_bin),
                                                                                                 str(t0_bin)]])
        try:
            with open(out_file, 'wt') as f:
                np.savetxt(f, np.rot90(histograms, 3), delimiter=',', header=meta_string, comments="", fmt="%-8i")
        except Exception as e:
            raise BeamsFileConversionError("An exception occurred writing ISIS data to {}".format(out_file)) from e

        return MuonHistogramFile(out_file)


class JPARCMuonFile(ConvertibleFile):
    SOURCE = Source.JPARC
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        raise NotImplementedError()


class MuonHistogramFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.HISTOGRAM
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 8

    def read_data(self):
        try:
            return read_columnated_data(file_path=self.file_path, data_row=self.HEADER_ROWS, d_type=int,
                                        titles=self.read_meta()[HIST_TITLES_KEY])
        except Exception as e:
            raise BeamsFileReadError("This histogram file is not supported by your current version of BEAMS") from e

    def read_meta(self):
        try:
            with open(self.file_path) as f:
                f.readline()
                metadata_line = f.readline()
                hist_titles = f.readline().strip().rsplit(',')
                background_one = f.readline().strip().rsplit(',')
                background_two = f.readline().strip().rsplit(',')
                good_bins_one = f.readline().strip().rsplit(',')
                good_bins_two = f.readline().strip().rsplit(',')
                initial_time = f.readline().strip().rsplit(',')

            metadata = read_meta_line(metadata_line)
            metadata[HIST_TITLES_KEY] = hist_titles
            metadata[BACKGROUND_ONE_KEY] = {k: v for k, v in zip(hist_titles, background_one)}
            metadata[BACKGROUND_TWO_KEY] = {k: v for k, v in zip(hist_titles, background_two)}
            metadata[GOOD_BIN_ONE_KEY] = {k: v for k, v in zip(hist_titles, good_bins_one)}
            metadata[GOOD_BIN_TWO_KEY] = {k: v for k, v in zip(hist_titles, good_bins_two)}
            metadata[T0_KEY] = {k: v for k, v in zip(hist_titles, initial_time)}

            return metadata
        except Exception as e:
            raise BeamsFileReadError("This histogram file is not supported by your current version of BEAMS") from e


class MuonAsymmetryFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.ASYMMETRY
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 3

    def read_data(self):
        try:
            return read_columnated_data(file_path=self.file_path, data_row=self.HEADER_ROWS, d_type=float,
                                        titles=["Time", "Asymmetry", "Uncertainty"])
        except Exception as e:
            raise BeamsFileReadError("This asymmetry file is not supported by your current version of BEAMS") from e

    def read_meta(self):
        try:
            with open(self.file_path) as f:
                f.readline()
                metadata_line = f.readline().strip().strip('#')

            metadata = read_meta_line(metadata_line)
            metadata[T0_KEY] = 0

            return metadata
        except Exception as e:
            raise BeamsFileReadError("This asymmetry file is not supported by your current version of BEAMS") from e


class FitDatasetExpressionFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.FIT_SET_VERBOSE
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 1

    def read_data(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            c_line = None
            s_lines = []
            e_line = None
            for i, l in enumerate(lines):
                if 'Specific' in l:
                    s_lines.append(i)
                elif 'Common' in l:
                    c_line = i
                elif 'Fitting equation' in l:
                    e_line = i

            try:
                common_parameters = []
                if c_line:
                    first_i = c_line + 2
                    last_i = e_line - 1 if len(s_lines) == 0 else s_lines[0] - 1
                    for i in range(first_i, last_i):
                        common_parameters.append(lines[i].split())

                specific_parameters = {}
                if s_lines:
                    for n, s in enumerate(s_lines):
                        first_i = s + 2
                        last_i = e_line - 1 if not len(s_lines) > n + 1 else s_lines[n + 1] - 2
                        file_i = s - 1
                        filename = lines[file_i][:-1]
                        parameters = []

                        for i in range(first_i, last_i):
                            parameters.append(lines[i].split())

                        line = lines[s]
                        title = line[line.find("(") + 1:-2]
                        specific_parameters[line.split()[5]] = (title, filename, parameters)

                if e_line:
                    e_line_split = lines[e_line + 2].split()
                    for i, e in enumerate(e_line_split):
                        if '=' in e:
                            expression = ''.join(e_line_split[i + 1:])
                            break
                    else:
                        raise Exception('Expression not formatted correctly in this fit file.')
                else:
                    raise Exception("Expression not found in this fit file.")

                return common_parameters, specific_parameters, expression
            except Exception as e:
                raise BeamsFileReadError("This fit file is not supported by your current version of BEAMS") from e

    def read_meta(self):
        return self.read_data()


class FitFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.FIT
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 3

    def read_data(self):
        try:
            return read_columnated_data(file_path=self.file_path, data_row=self.HEADER_ROWS, d_type=float,
                                        titles=['Time', 'Calculated', 'Observed', 'Uncertainty'])
        except Exception as e:
            raise BeamsFileReadError("This fit file is not supported by your current version of BEAMS") from e

    def read_meta(self):
        try:
            with open(self.file_path) as f:
                f.readline()
                metadata_line = f.readline().strip().strip('#')

            metadata = read_meta_line(metadata_line)
            metadata[T0_KEY] = 0

            return metadata
        except Exception as e:
            raise BeamsFileReadError("This fit file is not supported by your current version of BEAMS") from e


def file(file_path: str) -> File:
    """
    Returns a File object for a specified file path.

    :param file_path:
    :return File: a ReadableFile or ConvertibleFile object.
    """
    if not is_found(file_path):
        raise FileNotFoundError(file_path)

    elif check_ext(file_path, Extensions.HISTOGRAM) and is_beams(file_path):
        return MuonHistogramFile(file_path)

    elif check_ext(file_path, Extensions.ASYMMETRY) and is_beams(file_path):
        return MuonAsymmetryFile(file_path)

    elif check_ext(file_path, Extensions.TRIUMF):
        return TRIUMFMuonFile(file_path)

    elif check_ext(file_path, Extensions.PSI_BIN) or check_ext(file_path, Extensions.PSI_MDU):
        return PSIMuonFile(file_path)

    elif check_ext(file_path, Extensions.ISIS_NXS_V2):
        return ISISMuonFile(file_path)

    elif check_ext(file_path, Extensions.SESSION):
        return BeamsSessionFile(file_path)

    elif check_ext(file_path, Extensions.FIT) and is_beams(file_path):
        return FitFile(file_path)

    elif check_ext(file_path, Extensions.FIT_SUMMARY_VERBOSE) and is_beams(file_path):
        return FitDatasetExpressionFile(file_path)

    else:
        return UnknownFile(file_path)


def is_found(filename):
    """
    Checks that the file at the path given exists.

    :param filename:
    :return boolean:
    """
    try:
        with open(filename):
            return True
    except FileNotFoundError:
        return False
    except IOError:
        return False


def check_ext(filename, expected_ext):
    """
    Checks the extension of the given file path against the given extension

    :param filename:
    :param expected_ext:
    :return: boolean
    """
    expected_ext = expected_ext.lower()
    _, ext = os.path.splitext(filename.lower())
    return ext == expected_ext or expected_ext in ext


def is_beams(filename):
    """
    Checks if file is a BEAMS data file

    This check is purely based on the fact that BEAMS is in the first line, not really worth doing anything more
    specific.

    :param filename:
    :return boolean:
    """
    if is_found(filename):
        with open(filename) as f:
            return 'beams' in f.readline().rstrip('\n').lower()
    return False


def read_columnated_data(file_path, data_row, d_type, titles=None, title_row=None):
    """
    Reads in columnated data from a file

    If title row is provided and titles are not then it will attempt to retrieve the titles from that row. If titles
    is provided then it will not make an attempt to retrieve them.

    PARAMETERS
    ----------
        file_path: str
            Absolute or relative path to the file we are reading
        data_row: int
            The first line where the data begins (0 indexed)
        d_type: type
            The type of the data we are retrieving
        titles: list[str]
            List of titles for each column (in proper order)
        title_row: int
            The line where the column titles are in the file

    RETURNS
    -------
        data: np.ndarray

    """
    try:
        if not titles and title_row:
            with open(file_path, 'r') as f:
                for i in range(title_row):
                    f.readline()
                titles = [s.strip().strip('#') for s in f.readline().split(',')]

        if titles:
            return np.genfromtxt(file_path, dtype=d_type, delimiter=',', names=titles, skip_header=data_row)
        else:
            return np.genfromtxt(file_path, dtype=d_type, delimiter=',', skip_header=data_row)

    except Exception as e:
        raise BeamsFileReadError("Error occurred reading in data.") from e


def read_meta_line(line: str) -> dict:
    """
    Returns the meta data as a dictionary given a single line of metadata.

    Note: KeyNames must NOT include a comma. KeyNames must NOT include colons.
    All key value pairs MUST be separated by a comma. All keys and values will be strings and
    whitespace will be stripped from the left and right side of those strings. Test regex below if
    you are wondering if your meta string will survive.
    """
    key_regex = "(?<=^|,)[^,]*?(?=:)"
    value_regex = "(?<=:)([^:]|{.*})*(?=(,|$))"

    try:
        # We do it like this so that values can include colons (e.g. if we had a dictionary as a value). Turns out that
        # that is very hard to express simply with regex so we just iteratively remove key value pairs as we move down
        # the string, just finding the next match rather then finding all matches at once.
        meta_line = line
        meta = {}

        while len(meta_line) > 1:
            # Get the next key in the line
            key = regex.search(key_regex, meta_line).group()

            # Find the index the key substring starts at
            key_index = meta_line.find(key)

            # Set the line to be everything after the key
            meta_line = meta_line[key_index+len(key):]

            # Now find the next value in the line
            value = regex.search(value_regex, meta_line).group()

            # Find the index the value substring starts at
            value_index = meta_line.find(value)

            # Set the line to be everything after the value
            meta_line = meta_line[value_index + len(value):]

            # Strip the whitespace and add the key-value pair to the dict
            meta[key.strip()] = value.strip()

        return meta

    except Exception as e:
        raise BeamsFileReadError("Top line of metadata was in an unexpected format.") from e


class UnknownFileSource(Exception):
    """
    Raised when a user once a File object for an unknown file type, or type that the program is not
    currently equipped to handle.
    """

    def __init__(self):
        super(UnknownFileSource, self).__init__()


class BeamsFileReadError(Exception):
    """
    Raised when there is a problem reading data from a beams file.
    """

    def __init__(self, *args):
        super(BeamsFileReadError, self).__init__(*args)


class BeamsFileConversionError(Exception):
    """
    Raised when there is an error converting a convertible file (usually caused by a subprocess error)
    """

    def __init__(self, *args):
        super(BeamsFileConversionError, self).__init__(*args)

