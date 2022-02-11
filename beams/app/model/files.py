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


def create_meta_string(meta: dict) -> str:
    hist_keys = [T0_KEY, BACKGROUND_TWO_KEY, BACKGROUND_ONE_KEY, GOOD_BIN_ONE_KEY, GOOD_BIN_TWO_KEY, HIST_TITLES_KEY]

    final_string = 'BEAMS\n'
    for i, (key, value) in enumerate(meta.items()):
        if key not in hist_keys:
            final_string += f"{key}:{str(value)}" + "," if i < len(meta) - 1 else ""
    final_string += "\n"

    final_string += '\n'.join([','.join([title if meta_list is None else str(meta_list[title])
                                         for title in meta[HIST_TITLES_KEY]])
                               for meta_list in [None,
                                                 meta[BACKGROUND_ONE_KEY],
                                                 meta[BACKGROUND_TWO_KEY],
                                                 meta[GOOD_BIN_ONE_KEY],
                                                 meta[GOOD_BIN_TWO_KEY],
                                                 meta[T0_KEY]]])
    return final_string


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
