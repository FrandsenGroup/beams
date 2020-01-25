
import pandas as pd
import os
import subprocess
import sys


class InvalidFileFormat(Exception):
    def __init__(self, ):
        super(InvalidFileFormat, self).__init__()


class InvalidData(Exception):
    pass


def convert_msr(in_file, out_file, flags=None):
    """ Takes an 'in_file' with a .msr extension and then converts and writes the data to
        an 'out_file' with a .dat extension. Tested on Ubuntu and Windows 10 successfully.
        To convert it calls the MUD.exe/MUDC executable which is compiled from the source code
        in the mud/src folder. """

    if is_found(in_file) and check_ext(in_file, '.msr') and check_ext(out_file, '.dat'):
        system_args = {'win32': ['mud\MUD', in_file, out_file],  # Windows Syntax
                       'linux': ['./mud/MUDC', in_file, out_file],  # Linux Syntax
                       'darwin': ['./mud/MUDM', in_file, out_file]}  # Mac Syntax

        if sys.platform in system_args.keys():
            args = system_args[sys.platform]

            if flags:
                args.extend(flags)  # -v (verbose) -all (all metadata) See BEAMS_MUD.c to see other flags.

            if sys.platform == 'win32':
                shell = True
            else:
                shell = False
        else:
            return False  # Unrecognized system

        try:
            subprocess.check_call(args, shell=shell)
        except subprocess.CalledProcessError:
            return False  # Error processing file
        else:
            return True

    return False  # Unrecognized file format


def create_file_key(filename):
    file = FileReader(filename)
    if file.get_type() == FileReader.BINARY_FILE:
        return os.path.split(filename)[1]

    header = FileReader(filename).get_meta()
    file_root = os.path.split(filename)[1]
    file_key = file_root
    if header is not None:
        file_key = file_key + " - " + header['Title']
    return file_key


def check_ext(filename, expected_ext):
    """ Checks the extension of file against the user specified extension. """
    _, ext = os.path.splitext(filename)
    if ext == expected_ext:
        return True
    return False


def is_beams(filename):
    """ Checks if the .dat file is BEAMS formatted (first line should read 'BEAMS'). No other checks."""
    if is_found(filename):
        with open(filename) as file:
            if 'BEAMS' in file.readline().rstrip('\n'):
                return True
    return False


def is_found(filename):
    """ Checks that the file path can be successfully found and opened. """
    try:
        with open(filename):
            pass
    except FileNotFoundError:
        return False
    except IOError:
        return False
    else:
        return True


def parse_func(s):
    """ Takes in an expression as a string and returns a set of the free variables. """

    # Add to these sets any keywords you want to be recognized as not variables.
    # Keep keywords lowercase, user input will be cast to lowercase for comparison.
    oper_set = ('+', '-', '/', '*', '(', ')', '[', ']', '{', '}', '^', '!')
    key_1_char_set = ('e', 'i')
    key_2_char_set = ('pi')
    key_3_char_set = ('sin', 'cos', 'tan')
    key_4_char_set = ('sinh', 'cosh', 'tanh')

    free_set = set()
    free_variable = []
    skip_chars = 0

    for i, character in enumerate(s):
        if skip_chars > 0:
            skip_chars -= 1
            continue

        if character.isspace() or character in oper_set:
            free_variable_joined = "".join(free_variable)
            free_set.add(free_variable_joined)
            free_variable = []

        elif character.isalpha():
            if s[i:i + 4].lower() in key_4_char_set:
                skip_chars = 3
                continue
            elif s[i:i + 3].lower() in key_3_char_set:
                skip_chars = 2
                continue
            elif s[i:i + 2].lower() in key_2_char_set:
                skip_chars = 1
                continue
            elif s[i].lower() in key_1_char_set and (s[i + 1] in oper_set or s[i + 1].isspace()):
                continue
            else:
                free_variable.append(character)

        elif character.isdigit():
            if free_variable:
                free_variable.append(character)

    free_variable_joined = "".join(free_variable)
    free_set.add(free_variable_joined)
    free_set.remove('')

    return free_set


def get_separator():
    if sys.platform == 'win32':
        return "\\"
    else:
        return "/"


# fixme just make this object a function, then the convert functionality make more intuitive sense.
class FileReader:
    # File Source
    BEAMS = 0
    TRIUMF = 1

    # File Type
    BINARY_FILE = 0
    HISTOGRAM_FILE = 1
    ASYMMETRY_FILE = 2
    FFT_FILE = 3

    def __init__(self, file_path):
        self.file_path = file_path
        self.found = is_found(file_path)
        if not self.found:
            return

        if check_ext(file_path, '.dat') and is_beams(file_path):
            self.__file = BeamsDatFile(file_path)
            self.type = self.HISTOGRAM_FILE
            self.__source = self.BEAMS
        elif check_ext(file_path, '.asy') and is_beams(file_path):
            self.__file = BeamsAsyFile(file_path)
            self.type = self.ASYMMETRY_FILE
            self.__source = self.BEAMS
        elif check_ext(file_path, '.msr'):
            self.__file = TriumfMsrFile(file_path)
            self.type = self.BINARY_FILE
            self.__source = self.TRIUMF
        else:
            raise InvalidFileFormat()

    def __str__(self):
        return str(self.__file)

    def get_data(self):
        return self.__file.get_data()

    def get_meta(self):
        return self.__file.get_meta()

    def convert(self):
        return self.__file.convert()

    def get_type(self):
        return self.type

    def get_file_path(self):
        return self.file_path

    def is_found(self):
        return self.found


class File:
    def get_type(self):
        raise InvalidFileFormat()

    def get_file_path(self):
        raise InvalidFileFormat()

    def get_data(self):
        raise InvalidFileFormat()

    def get_meta(self):
        raise InvalidFileFormat()

    def convert(self):
        raise InvalidFileFormat()


class BeamsAsyFile(File):
    HEADER_ROWS = 3

    def __init__(self, file_path):
        self.file_path = file_path
        self.__meta = None

    def __str__(self):
        return "Beams Asymmetry File: meta=" + str(self.get_meta())

    def get_data(self):
        data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS-1)
        data.columns = ['Time', 'Asymmetry', 'Uncertainty']
        return data

    def get_meta(self):
        if self.__meta is None:
            with open(self.file_path) as file:
                file.readline()
                metadata = file.readline().rstrip('\n').rsplit('# ')[1].rsplit(',')

            metadata = [pair.rsplit(':') for pair in metadata]
            for pair in metadata:
                if len(pair) < 2:
                    pair.append('n/a')
            metadata = {pair[0]: pair[1] for pair in metadata}

            # need binsize, field, temperature, t0, title. Otherwise we have no idea what this data is
            self.__meta = metadata
            return metadata
        else:
            return self.__meta

    def convert(self):
        raise InvalidFileFormat()


class BeamsDatFile(File):
    HEADER_ROWS = 8

    def __init__(self, file_path):
        self.file_path = file_path
        self.__meta = None

    def __str__(self):
        return "Beams Data File: meta=" + str(self.get_meta())

    def get_data(self):
        meta = self.get_meta()
        data = pd.read_csv(self.file_path, skiprows=self.HEADER_ROWS-1)
        data.columns = meta[HIST_TITLES_KEY]
        return data

    def get_meta(self):
        if self.__meta is None:
            with open(self.file_path) as file:
                file.readline()
                metadata = file.readline().rstrip('\n').rsplit(',')
                hist_titles = file.readline().rstrip('\n').rsplit(',')
                background_one = file.readline().rstrip('\n').rsplit(',')
                background_two = file.readline().rstrip('\n').rsplit(',')
                good_bins_one = file.readline().rstrip('\n').rsplit(',')
                good_bins_two = file.readline().rstrip('\n').rsplit(',')
                initial_time = file.readline().rstrip('\n').rsplit(',')

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
            self.__meta = metadata
            return metadata
        else:
            return self.__meta

    def convert(self):
        raise InvalidFileFormat()


# fixme have the convert functions for musr files return a new BeamsDatFile object?
class TriumfMsrFile(File):
    def __init__(self, file_path):
        self.file_path = file_path

    def get_data(self):
        raise InvalidFileFormat()

    def get_meta(self):
        # fixme, it could be useful to make a executable to get the header of an msr file
        raise InvalidFileFormat()

    def convert(self):
        pass


class PSIMsrFile(File):
    def __int__(self, file_path):
        self.file_path = file_path

    def get_data(self):
        raise InvalidFileFormat()

    def get_meta(self):
        # fixme, it could be useful to make a executable to get the header of an msr file
        raise InvalidFileFormat()

    def convert(self):
        pass


class ISISMsrFile(File):
    def __init__(self, file_path):
        self.file_path = file_path

    def get_data(self):
        raise InvalidFileFormat()

    def get_meta(self):
        # fixme, it could be useful to make a executable to get the header of an msr file
        raise InvalidFileFormat()

    def convert(self):
        pass


class JParcMsrFile(File):
    def __int__(self, file_path):
        self.file_path = file_path

    def get_data(self):
        raise InvalidFileFormat()

    def get_meta(self):
        # fixme, it could be useful to make a executable to get the header of an msr file
        raise InvalidFileFormat()

    def convert(self):
        pass


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
