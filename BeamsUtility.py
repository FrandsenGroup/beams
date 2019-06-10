
import pandas as pd
import os
import subprocess
import sys


class InvalidFileFormat(Exception):
    pass


class InvalidData(Exception):
    pass


def convert_msr(in_file=None, out_file=None, flags=None):
    """ Takes an 'in_file' with a .msr extension and then converts and writes the data to
        an 'out_file' with a .dat extension. Tested on Ubuntu and Windows 10 successfully.
        To convert it calls the MUD.exe executable which is compiled from the source code
        in the mud/src folder. """

    if is_found(in_file) and check_ext(in_file, '.msr') and check_ext(out_file, '.dat'):
        system_args = {'win32': ['MUD', in_file, out_file],  # Windows Syntax
                       'linux': ['./MUD.exe', in_file, out_file],  # Linux Syntax
                       'darwin': ['./MUD.exe', in_file, out_file]}  # Mac Syntax

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


def read_dat(filename=None, skiprows=3):
    """ Reads and returns the histogram and header, does not check retrieved data. """
    if check_ext(filename, '.dat'):
        header = get_header(filename)
        histograms = get_histograms(filename, skiprows)

        return [header, histograms]

    return None


def get_header(filename=None, header_rows=None):
    """ Gets the header from a .dat file. If BEAMS formatted, it creates a dictionary with
        the header data, otherwise it stores the first user-specified number of lines in a
        list of strings. """
    if is_beams(filename):  # We are basically praying if it is BEAMS, it has the proper format. #fixthis, call errors
        with open(filename) as file:
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
        metadata['HistTitles'] = hist_titles
        metadata['BkgdOne'] = {k: v for k, v in zip(hist_titles, background_one)}
        metadata['BkgdTwo'] = {k: v for k, v in zip(hist_titles, background_two)}
        metadata['GoodBinOne'] = {k: v for k, v in zip(hist_titles, good_bins_one)}
        metadata['GoodBinTwo'] = {k: v for k, v in zip(hist_titles, good_bins_two)}
        metadata['T0'] = {k: v for k, v in zip(hist_titles, initial_time)}

    elif check_ext(filename, '.dat'):
        metadata = []
        with open(filename) as file:
            for _ in range(header_rows):
                metadata.append(file.readline())

    else:
        return None

    return metadata


def get_histograms(filename=None, skiprows=None, histogram=None):
    """ Gets the histogram(s) from a specified .dat file, does not check retrieved data.
        User can specify a particular histogram to retrieve or None to retrieve all. """
    if histogram:
        try:
            histograms = pd.read_csv(filename, skiprows=skiprows, usecols=[histogram])
        except ValueError:
            raise InvalidFileFormat
    else:
        histograms = pd.read_csv(filename, skiprows=skiprows-1)
    return histograms


def check_ext(filename=None, expected_ext=None):
    """ Checks the extension of file against the user specified extension. """
    _, ext = os.path.splitext(filename)
    if ext == expected_ext:
        return True
    return False


def check_input(user_input=None, expected=None, low_limit=None, up_limit=None, equal_to=None):
    """ Checks the user_input against the conditions specified by function caller. """
    try:
        altered = expected(user_input)  # 'expected' consists of functions like int, float or str
    except ValueError:
        return False
    except NameError:
        return False

    if low_limit and altered < low_limit:
        return False
    if up_limit and altered > up_limit:
        return False
    if equal_to and not altered == equal_to:
        return False

    return True


def check_files(filenames=None):
    """ Checks given filenames for BEAM format, .dat or .msr extensions. """
    dat_beams_files = []  # .dat files in BEAMS format, no specification necessary
    dat_other_files = []  # .dat files in non-BEAMS format, user specification necessary
    msr_files = []  # .msr files (MUD format)
    bad_files = []  # Unsupported file types

    for file in filenames:
        if is_found(file):
            if is_beams(file):
                dat_beams_files.append(file)
            elif check_ext(file, '.dat'):
                dat_other_files.append(file)
            elif check_ext(file, '.msr'):
                msr_files.append(file)
            else:
                bad_files.append(file)
        else:
            bad_files.append(file)

    return [dat_beams_files, dat_other_files, msr_files, bad_files]


def is_beams(filename=None):
    """ Checks if the .dat file is BEAMS formatted (first line should read 'BEAMS'). No other checks."""
    if is_found(filename) and check_ext(filename, '.dat'):
        with open(filename) as file:
            if file.readline().rstrip('\n') == 'BEAMS':
                return True
    return False


def is_found(filename=None):
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


def is_valid_format(sections=None, t0=None, header_rows=None, file_names=None):
    def check_file_names():
        for filename in file_names:
            if is_found(filename) and check_ext(filename, '.dat'):
                return True
        return False

    def check_header():
        """Checks to ensure header rows was given correctly"""
        for filename in file_names:
            with open(filename) as fp:
                for i, line in enumerate(fp):
                    if i == int(header_rows):
                        line = line.rstrip()
                        first_values = line.split(',')
                        try:
                            for value in first_values:
                                if value != 'nan':
                                    float(value)
                        except ValueError:
                            return False
                        break
        return True

    def check_binning():
        """Ensures the initial bin is not larger then the number of lines or less then zero"""
        try:
            int(t0)
        except ValueError:
            return False
        for filename in file_names:
            n = sum(1 for _ in open(filename, 'rb'))
            if int(t0) > n or int(t0) < 0:
                return False
        return True

    def check_column_values():
        for k1, v1 in sections.items():
            for k2, v2 in sections.items():
                if v1 == v2 and k1 != k2:
                    return False
        return True

    def check_columns_setup():
        """Checks specified sections to ensure needed attributes can be calculated and none have the same column"""
        if sections:
            if 'Front' in sections and 'Back' in sections:
                if 'Time' in sections:
                    if (sections['Front'] == sections['Back']) or (sections['Front'] == sections['Time']) \
                            or (sections['Back'] == sections['Time']):
                        return False
                    return "fbt"
                else:
                    if sections['Front'] == sections['Back']:
                        return False
                    return "fb"
            elif 'Left' in sections and 'Right' in sections:
                if 'Time' in sections:
                    if (sections['Left'] == sections['Right']) or (sections['Left'] == sections['Time']) \
                            or (sections['Right'] == sections['Time']):
                        return False
                    return "lrt"
                else:
                    if sections['Left'] == sections['Right']:
                        return False
                    return "lr"
            elif 'Asymmetry' in sections:
                if 'Time' in sections:
                    if 'Uncertainty' in sections:
                        if (sections['Asymmetry'] == sections['Time']) or (
                                sections['Asymmetry'] == sections['Uncertainty']) \
                                or (sections['Uncertainty'] == sections['Time']):
                            return False
                        return 'atu'
                    else:
                        if sections['Asymmetry'] == sections['Time']:
                            return False
                        return 'at'
                else:
                    return False
            else:
                return False
        else:
            return False

    if not check_file_names():
        return 'EF'
    if not check_header():
        return 'EH'
    if not check_column_values():
        return 'EC'

    f_format = check_columns_setup()
    if not f_format:
        return 'EC'
    elif f_format == 'fbt' or f_format == 'fb' or f_format == 'lrt' or f_format == 'lr':
        if not check_binning():
            return 'EB'

    return f_format
