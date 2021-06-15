
# Standard Library Packages
import abc
import os
import sys
import subprocess
import traceback
import enum
import json

# Installed Packages
import pandas as pd

# Custom Packages
from app.resources import resources


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
T0_KEY = 'T0'
CALC_HISTS_KEY = 'CalcHists'

#TODO Maybe we should have these files inherit from the actual File object
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


class TRIUMFMuonFile(ConvertibleFile):
    SOURCE = Source.TRIUMF
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        flags = ['-all']
        if is_found(self.file_path) and check_ext(self.file_path, '.msr') and check_ext(out_file, '.dat'):
            system_args = {'win32': ['beams\\app\\resources\\mud\\TRIUMF_WINDOWS', self.file_path, out_file],  # Windows Syntax
                           'linux': ['./beams/app/resources/mud/TRIUMF_LINUX', self.file_path, out_file],  # Linux Syntax
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
                return None  # Unrecognized system

            try:
                # print(" ".join(args))
                subprocess.check_call(args, shell=shell)
            except subprocess.CalledProcessError:
                track = traceback.format_exc()
                print(track)
                return None  # Error processing file
            else:
                return MuonHistogramFile(out_file)

        return None  # Unrecognized file format


class PSIMuonFile(ConvertibleFile):
    SOURCE = Source.PSI
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        if is_found(self.file_path) and (check_ext(self.file_path, '.bin') or check_ext(self.file_path, '.mdu')) \
                and check_ext(out_file, '.dat'):

            system_args = {'win32': ['beams\\app\\resources\\mud\\PSI_WINDOWS', self.file_path, out_file],  # Windows Syntax
                           'linux': ['./beams/app/resources/mud/PSI_LINUX', self.file_path, out_file],  # Linux Syntax
                           'darwin': ['./beams/app/resources/mud/PSI_MAC', self.file_path, out_file]}  # Mac Syntax

            if sys.platform in system_args.keys():
                args = system_args[sys.platform]

                if sys.platform == 'win32':
                    shell = True
                else:
                    shell = False
            else:
                return None  # Unrecognized system

            try:
                # print(" ".join(args))
                subprocess.check_call(args, shell=shell)
            except subprocess.CalledProcessError:
                track = traceback.format_exc()
                print(track)
                return None  # Error processing file
            else:
                return MuonHistogramFile(out_file)

        return None  # Unrecognized file format


class ISISMuonFile(ConvertibleFile):
    SOURCE = Source.ISIS
    DATA_FORMAT = Format.BINARY
    DATA_TYPE = DataType.MUON

    def convert(self, out_file):
        pass


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
        data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS - 1)
        data.columns = meta[HIST_TITLES_KEY]
        return data

    def read_meta(self):
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


class MuonAsymmetryFile(ReadableFile):
    SOURCE = Source.BEAMS
    DATA_FORMAT = Format.ASYMMETRY
    DATA_TYPE = DataType.MUON
    HEADER_ROWS = 3

    def read_data(self):
        data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS - 1)
        data.columns = ['Time', 'Asymmetry', 'Uncertainty']
        return data

    def read_meta(self):
        with open(self.file_path) as f:
            f.readline()
            metadata = f.readline().rstrip('\n').rsplit('# ')[1].rsplit(',')

        metadata = [pair.rsplit(':') for pair in metadata]
        for pair in metadata:
            if len(pair) < 2:
                pair.append('n/a')
        metadata = {pair[0]: pair[1] for pair in metadata}

        return metadata


def file(file_path):
    """
    Returns a File object (ReadableFile or ConvertibleFile) for a specified file path.

    :param file_path:
    :return File: a ReadableFile or ConvertibleFile object.
    """
    if not is_found(file_path):
        raise FileNotFoundError

    if check_ext(file_path, '.dat') and is_beams(file_path):
        return MuonHistogramFile(file_path)

    elif check_ext(file_path, '.asy') and is_beams(file_path):
        return MuonAsymmetryFile(file_path)

    elif check_ext(file_path, '.msr'):
        return TRIUMFMuonFile(file_path)

    elif check_ext(file_path, '.bin') or check_ext(file_path, '.mdu'):
        return PSIMuonFile(file_path)

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


class ConversionError(Exception):
    """
    Raised when there is an error converting a convertible file (usually caused by a subprocess error)
    """
    def __init__(self):
        super(ConversionError, self).__init__()


def set_last_used_directory(path):

    if len(path) == 0:
        path = "."

    if os.path.exists(path) and os.path.isdir(path):
        resources.SAVED_USER_DATA["dir"] = path
        with open(resources.CONFIGURATION_FILE, 'w+') as f:
            json.dump(resources.SAVED_USER_DATA, f)


def load_last_used_directory():
    if "dir" in resources.SAVED_USER_DATA.keys():
        path = resources.SAVED_USER_DATA["dir"]
        if os.path.exists(r'{}'.format(path)) and os.path.isdir(r'{}'.format(path)):
            return path
    else:
        set_last_used_directory(os.getcwd())
        return os.getcwd()
