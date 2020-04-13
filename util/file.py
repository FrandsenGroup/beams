
# Standard Library Packages
import abc
import os
import sys
import subprocess
import traceback

# Installed Packages
import pandas as pd


# File Sources
TRIUMF = 0
PSI = 1
ISIS = 2
JPARC = 3
BEAMS = 4

# File Formats
HISTOGRAM = 0
ASYMMETRY = 1
BINARY = 2

# File Data
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


class File(abc.ABC):
    DATA_TYPE = None
    DATA_FORMAT = None
    source = None

    def __init__(self, file_path):
        self.file_path = file_path


class ConvertibleFile(File, abc.ABC):
    @abc.abstractmethod
    def convert(self, out_file):
        pass


class ReadableFile(File, abc.ABC):
    HEADER_ROWS = None

    @abc.abstractmethod
    def read_data(self):
        pass

    @abc.abstractmethod
    def read_meta(self):
        pass


class TRIUMFMuonFile(ConvertibleFile):
    SOURCE = TRIUMF
    DATA_FORMAT = BINARY
    DATA_TYPE = MUON

    def convert(self, out_file):
        flags = ['-all']
        if is_found(self.file_path) and check_ext(self.file_path, '.msr') and check_ext(out_file, '.dat'):
            system_args = {'win32': ['mud\\TRIUMF_WINDOWS', self.file_path, out_file],  # Windows Syntax
                           'linux': ['./mud/TRIUMF_LINUX', self.file_path, out_file],  # Linux Syntax
                           'darwin': ['./mud/TRIUMF_MAC', self.file_path, out_file]}  # Mac Syntax

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
                print(" ".join(args))
                subprocess.check_call(args, shell=shell)
            except subprocess.CalledProcessError:
                track = traceback.format_exc()
                print(track)
                return None  # Error processing file
            else:
                return MuonHistogramFile(out_file)

        return None  # Unrecognized file format


class PSIMuonFile(ConvertibleFile):
    SOURCE = PSI
    DATA_FORMAT = BINARY
    DATA_TYPE = MUON

    def convert(self, out_file):
        if is_found(self.file_path) and (check_ext(self.file_path, '.bin') or check_ext(self.file_path, '.mdu')) \
                and check_ext(out_file, '.dat'):

            system_args = {'win32': ['mud\\PSI_WINDOWS', self.file_path, out_file],  # Windows Syntax
                           'linux': ['./mud/PSI_LINUX', self.file_path, out_file],  # Linux Syntax
                           'darwin': ['./mud/PSI_MAC', self.file_path, out_file]}  # Mac Syntax

            if sys.platform in system_args.keys():
                args = system_args[sys.platform]

                if sys.platform == 'win32':
                    shell = True
                else:
                    shell = False
            else:
                return None  # Unrecognized system

            try:
                print(" ".join(args))
                subprocess.check_call(args, shell=shell)
            except subprocess.CalledProcessError:
                track = traceback.format_exc()
                print(track)
                return None  # Error processing file
            else:
                return MuonHistogramFile(out_file)

        return None  # Unrecognized file format


class ISISMuonFile(ConvertibleFile):
    SOURCE = ISIS
    DATA_FORMAT = BINARY
    DATA_TYPE = MUON

    def convert(self, out_file):
        pass


class JPARCMuonFile(ConvertibleFile):
    SOURCE = JPARC
    DATA_FORMAT = BINARY
    DATA_TYPE = MUON

    def convert(self, out_file):
        pass


class MuonHistogramFile(ReadableFile):
    SOURCE = BEAMS
    DATA_FORMAT = HISTOGRAM
    DATA_TYPE = MUON
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
    SOURCE = BEAMS
    DATA_FORMAT = ASYMMETRY
    DATA_TYPE = MUON
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
    """ Creates the appropriate File object based on the given file path. """
    if not is_found(file_path):
        raise FileNotFoundError

    if check_ext(file_path, '.dat') and is_beams(file_path):
        return MuonHistogramFile(file_path)

    elif check_ext(file_path, '.asy') and is_beams(file_path):
        return MuonAsymmetryFile(file_path)

    elif check_ext(file_path, 'msr'):
        return TRIUMFMuonFile(file_path)

    elif check_ext(file_path, '.bin') or check_ext(file_path, '.mdu'):
        return PSIMuonFile(file_path)

    else:
        raise InvalidFileFormat()


def is_found(filename):
    """ Checks that the file path can be successfully found and opened. """
    try:
        with open(filename):
            return True
    except FileNotFoundError:
        return False
    except IOError:
        return False


def check_ext(filename, expected_ext):
    """ Checks the extension of file against the user specified extension. """
    _, ext = os.path.splitext(filename)
    return ext == expected_ext


def is_beams(filename):
    """ Checks if the .dat file is BEAMS formatted (first line should read 'BEAMS'). No other checks."""
    if is_found(filename):
        with open(filename) as f:
            return 'BEAMS' in f.readline().rstrip('\n')


class InvalidFileFormat(Exception):
    def __init__(self, ):
        super(InvalidFileFormat, self).__init__()
