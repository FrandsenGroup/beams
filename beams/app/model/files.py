# Standard Library Packages
import abc
import os
import pickle
import sys
import subprocess
import traceback
import enum

# Installed Packages
import pandas as pd
import numpy as np
import h5py


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
FILE_PATH_KEY = 'FilePath'
LAB_KEY = "Lab"
AREA_KEY = "Area"


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

    def __str__(self):
        return '[ReadableFile: file_path={}, source={}, format={}, type={}]'.format(self.file_path, self.SOURCE,
                                                                                    self.DATA_FORMAT, self.DATA_TYPE)


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

    def __str__(self):
        return '[ConvertibleFile: file_path={}, source={}, format={}, type={}]'.format(self.file_path, self.SOURCE,
                                                                                       self.DATA_FORMAT, self.DATA_TYPE)


class UnknownFile(File):
    DATA_TYPE = DataType.UNKNOWN
    DATA_FORMAT = Format.UNKNOWN
    SOURCE = Source.UNKNOWN

    def __str__(self):
        return '[UnknownFile: file_path={}]'.format(self.file_path)


class BeamsSessionFile(ReadableFile):
    HEADER_ROWS = 0
    DATA_FORMAT = Format.PICKLED

    def read_data(self):
        with open(self.file_path, 'rb') as session_file_object:
            try:
                return pickle.load(session_file_object)
            except Exception:
                raise BeamsFileReadError("This session file is not supported by your current version of BEAMS.")

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
            system_args = {'win32': ['beams\\app\\resources\\mud\\TRIUMF_WINDOWS', self.file_path, out_file],
                           # Windows Syntax
                           'linux': ['./beams/app/resources/mud/TRIUMF_LINUX', self.file_path, out_file],
                           # Linux Syntax
                           'darwin': ['./beams/app/resources/mud/TRIUMF_MAC', self.file_path, out_file]}  # Mac Syntax

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
                raise e
            else:
                return MuonHistogramFile(out_file)

        raise BeamsFileConversionError("Binary file is in an unknown format. May need to update executables.")


class PSIMuonFile(ConvertibleFile):
    SOURCE = Source.PSI
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        if is_found(self.file_path) and (
                check_ext(self.file_path, Extensions.PSI_BIN) or check_ext(self.file_path, Extensions.PSI_MDU)) \
                and check_ext(out_file, Extensions.HISTOGRAM):

            system_args = {'win32': ['beams\\app\\resources\\mud\\PSI_WINDOWS', self.file_path, out_file],
                           # Windows Syntax
                           'linux': ['./beams/app/resources/mud/PSI_LINUX', self.file_path, out_file],  # Linux Syntax
                           'darwin': ['./beams/app/resources/mud/PSI_MAC', self.file_path, out_file]}  # Mac Syntax

            if sys.platform in system_args.keys():
                args = system_args[sys.platform]

                if sys.platform == 'win32':
                    shell = True
                else:
                    shell = False
            else:
                raise EnvironmentError("Not on a recognized system.")

            try:
                subprocess.check_call(args, shell=shell)
            except subprocess.CalledProcessError:
                track = traceback.format_exc()
                raise BeamsFileConversionError(str(track))
            else:
                return MuonHistogramFile(out_file)

        raise BeamsFileConversionError("Binary file is in an unknown format. May need to update executables.")


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

    def set_combine_format(self, starts, ends, names):
        # Check if the values provided are of a valid datatype. Doing this first prevents sneaky bugs.
        try:
            starts = [int(s) for s in starts]
            ends = [int(e) for e in ends]
            names = [str(n) for n in names]
        except ValueError:
            raise Exception("Format for combining histograms contains values of invalid types.")

        distinct_starts = set(starts)
        distinct_ends = set(ends)
        distinct_names = set(names)

        # Check if any values are repeated or if one set of values is larger then another
        if len(distinct_starts) != len(distinct_ends) or len(distinct_starts) != (len(distinct_names)) \
                or len(starts) != len(distinct_starts) or len(ends) != len(distinct_ends) \
                or len(names) != len(distinct_names) or len(distinct_starts) == 0:
            raise Exception("Invalid format for combining histograms.")

        # Check the start and end make sense.
        for i, (start, end, name) in enumerate(zip(starts, ends, names)):
            if start in ends or end in starts or start > end:
                raise Exception("Invalid range of histograms to combine.")

        if max(ends) > self.get_number_of_histograms():
            raise Exception("Invalid range of histograms to combine.")

        self._combine_format = (starts, ends, names)

    @staticmethod
    def get_value(data_paths, hdf_file_object, full=None):
        for path in data_paths:
            if path in hdf_file_object:
                if full:
                    return hdf_file_object[path]
                return hdf_file_object[path][0]
            elif path == data_paths[-1]:
                raise KeyError("Path not found in HDF file.")

    @staticmethod
    def get_attribute(data_paths, attribute, hdf_file_object):
        dataset = ISISMuonFile.get_value(data_paths, hdf_file_object, True)

        for att in attribute:
            if att in dataset.attrs:
                return dataset.attrs[att]
            elif att == attribute[-1]:
                raise AttributeError("Attribute not found on dataset.")

    def get_number_of_histograms(self):
        f = h5py.File(self.file_path, 'r+')

        try:
            data = self.get_value(self.DataPaths.HISTOGRAMS, f, True)
            return data.shape[1]  # Expected shape is something like 1x64x2048
        except (AttributeError, KeyError):
            raise BeamsFileConversionError("Binary file is in an unknown format. May need to update executables.")

    def convert(self, out_file):
        if not check_ext(out_file, Extensions.HISTOGRAM):
            raise Exception("Out file does not have a valid extension (.dat).")

        f = h5py.File(self.file_path, 'r+')

        try:
            title = self.get_value(self.DataPaths.TITLE, f)
            run_number = self.get_value(self.DataPaths.RUN_NUMBER, f)
            sample = self.get_value(self.DataPaths.SAMPLE_NAME, f)
            lab = self.get_value(self.DataPaths.LAB, f)
            area = self.get_value(self.DataPaths.AREA, f)
            resolution = self.get_value(self.DataPaths.RESOLUTION, f)
            resolution_units = str(self.get_attribute(self.DataPaths.RESOLUTION, self.Attributes.UNITS, f))

            # We want the resolution (bin size) to be in nanoseconds.
            if 'p' in resolution_units:
                resolution *= 1000
            elif '\u00b5' in resolution_units or 'm' in resolution_units:
                resolution /= 1000

            temperature = self.get_value(self.DataPaths.TEMPERATURE, f)
            temperature_units = self.get_attribute(self.DataPaths.TEMPERATURE, self.Attributes.UNITS, f)
            field = self.get_value(self.DataPaths.FIELD, f)
            field_units = self.get_attribute(self.DataPaths.FIELD, self.Attributes.UNITS, f)

            first_good_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.FIRST_GOOD_BIN, f)
            last_good_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.LAST_GOOD_BIN, f)
            t0_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.T0_BIN, f)

            try:
                first_bkgd_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.FIRST_BKGD_BIN, f)
            except AttributeError:
                first_bkgd_bin = 0

            try:
                last_bkgd_bin = self.get_attribute(self.DataPaths.HISTOGRAMS, self.Attributes.FIRST_BKGD_BIN, f)
            except AttributeError:
                last_bkgd_bin = t0_bin

            data = self.get_value(self.DataPaths.HISTOGRAMS, f, True)
        except (AttributeError, KeyError):
            raise BeamsFileConversionError("Binary file is in an unknown format. May need to update executables.")

        meta_string = ""
        meta_string += "BEAMS\n"
        meta_string += "{}:{}, ".format(BIN_SIZE_KEY, resolution)
        meta_string += "{}:{}, ".format(RUN_NUMBER_KEY, run_number)
        meta_string += "{}:{}, ".format(TITLE_KEY, title)
        meta_string += "{}:{}, ".format(LAB_KEY, lab)
        meta_string += "{}:{}, ".format(AREA_KEY, area)
        meta_string += "{}:{} {}, ".format(TEMPERATURE_KEY, temperature, temperature_units)
        meta_string += "{}:{} {}, ".format(FIELD_KEY, field, field_units)
        meta_string += "{}:{}\n".format("Sample", sample)

        if self._combine_format:
            starts, ends, names = self._combine_format
            histograms = [sum(data[0][start:end]) for start, end in zip(starts, ends)]

        else:
            names = [str(n) for n in range(self.get_number_of_histograms())]
            histograms = data[0]

        meta_string += '\n'.join([','.join([val if val else name for name in names]) for val in [None,
                                                                                                 str(first_bkgd_bin),
                                                                                                 str(last_bkgd_bin),
                                                                                                 str(t0_bin),
                                                                                                 str(first_good_bin),
                                                                                                 str(last_good_bin)]])
        try:
            np.savetxt(out_file, np.rot90(histograms), delimiter=',', header=meta_string, comments="", fmt="%-8i")
        except Exception:
            raise BeamsFileConversionError("An exception occurred writing ISIS data to {}".format(out_file))


class JPARCMuonFile(ConvertibleFile):
    SOURCE = Source.JPARC
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        pass


class MuonHistogramFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.HISTOGRAM
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 8

    def read_data(self):
        meta = self.read_meta()

        try:
            data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS - 1)
            data.columns = meta[HIST_TITLES_KEY]
            return data
        except Exception:
            raise BeamsFileReadError("This histogram file is not supported by your current version of BEAMS")

    def read_meta(self):
        try:
            with open(self.file_path) as f:
                f.readline()
                metadata = f.readline().rstrip('\n').rsplit(',')
                hist_titles = f.readline().rstrip('\n').rsplit(',')
                background_one = f.readline().rstrip('\n').rsplit(',')
                background_two = f.readline().rstrip('\n').rsplit(',')
                good_bins_one = f.readline().rstrip('\n').rsplit(',')
                good_bins_two = f.readline().rstrip('\n').rsplit(',')
                initial_time = f.readline().rstrip('\n').rsplit(',')

            metadata = [pair.rsplit(':') for pair in metadata]
            for pair in metadata:
                if len(pair) < 2:
                    pair.append('n/a')

            metadata = {pair[0]: pair[1] for pair in metadata}
            metadata[HIST_TITLES_KEY] = hist_titles
            metadata[BACKGROUND_ONE_KEY] = {k: v for k, v in zip(hist_titles, background_one)}
            metadata[BACKGROUND_TWO_KEY] = {k: v for k, v in zip(hist_titles, background_two)}
            metadata[GOOD_BIN_ONE_KEY] = {k: v for k, v in zip(hist_titles, good_bins_one)}
            metadata[GOOD_BIN_TWO_KEY] = {k: v for k, v in zip(hist_titles, good_bins_two)}
            metadata[T0_KEY] = {k: v for k, v in zip(hist_titles, initial_time)}

            return metadata
        except Exception:
            raise BeamsFileReadError("This histogram file is not supported by your current version of BEAMS")


class MuonAsymmetryFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.ASYMMETRY
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 3

    def read_data(self):
        try:
            data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS - 1)
            data.columns = ['Time', 'Asymmetry', 'Uncertainty']
            return data
        except Exception:
            raise BeamsFileReadError("This asymmetry file is not supported by your current version of BEAMS")

    def read_meta(self):
        try:
            with open(self.file_path) as f:
                f.readline()
                metadata_line = f.readline().rstrip('\n').rsplit('# ')[1].rsplit(',')

            metadata = [pair.rsplit(':') for pair in metadata_line]
            for pair in metadata:
                if len(pair) < 2:
                    pair.append('n/a')
            metadata = {pair[0]: pair[1] for pair in metadata}
            metadata[T0_KEY] = 0

            return metadata
        except Exception:
            raise BeamsFileReadError("This asymmetry file is not supported by your current version of BEAMS")


class FitDatasetExpressionFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.FIT_SET_VERBOSE
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 1

    def read_data(self):
        with open(self.file_path, 'r') as f:
            lines = f.readlines()
            c_line = None
            s_lines = []
            e_line = None
            for i, l in enumerate(lines):
                if 'Specific' in l:
                    s_lines.append(i)
                elif 'Common' in l:
                    c_line = i
                elif 'Expression' in l:
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
            except Exception:
                raise BeamsFileReadError("This fit file is not supported by your current version of BEAMS")

    def read_meta(self):
        return self.read_data()


class FitFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.FIT
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 3

    def read_data(self):
        try:
            data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS - 1)
            data.columns = ['Time', 'Asymmetry', 'Calculated', 'Uncertainty']
            return data
        except Exception:
            raise BeamsFileReadError("This fit file is not supported by your current version of BEAMS")

    def read_meta(self):
        try:
            with open(self.file_path) as f:
                f.readline()
                metadata_line = f.readline().rstrip('\n').rsplit('# ')[1].rsplit(',')

            metadata = [pair.rsplit(':') for pair in metadata_line]
            for pair in metadata:
                if len(pair) < 2:
                    pair.append('n/a')
            metadata = {pair[0]: pair[1] for pair in metadata}
            metadata[T0_KEY] = 0
            return metadata
        except Exception:
            raise BeamsFileReadError("This fit file is not supported by your current version of BEAMS")


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
    _, ext = os.path.splitext(filename)
    return ext == expected_ext


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
            return 'BEAMS' in f.readline().rstrip('\n')


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

filepath = r"D:\Research_Frandsen\BEAMS_venv\MUD_Files\ISIS\MUSR00083585.nxs_v2"
file_object = file(filepath)
file_object.set_combine_format([0, 33],[32, 64],['forw', 'back'])
file_object.convert("out.dat")

