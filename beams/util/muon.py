
import pandas as pd

from util import files


class MuonRun:
    def __init__(self, data, meta):
        self.data = data
        self.meta = meta

        self.asymmetry = None
        self.uncertainty = None
        self.time = None

    def update_bin(self):
        pass


def build_muon_run(data, meta) -> MuonRun:
    """
    Builds a MuonRun object (Asymmetry, Uncertainty, Time, etc) based on the given data and meta.

    :param data: A pandas dataframe containing the histograms with their titles as column heads.
    :param meta: A dictionary containing the meta data for the run
    :return run: a MuonRun object
    """

    run = MuonRun(data, meta)

    return run


def correct_muon_asymmetry(run: MuonRun, alpha=None):
    """
    Recalculates the asymmetry with the alpha value given in the MuonRun object or the one specified.
    By default it is set to 1 in the MuonRun object.

    :param run: The MuonRun with updated alpha value
    :param alpha: Optional alpha to be used, will replace the one in the MuonRun.
    :return asymmetry: A numpy array
    """

    pass


def bin_muon_asymmetry(run: MuonRun, bin):
    """
    Bins the asymmetry according to the provided bin size.

    :param run: The run containing the asymmetry to bin
    :param bin: The bin size of the new asymmetry in nano-seconds
    :return asymmetry: The binned asymmetry
    """

    pass


def bin_muon_uncertainty(run: MuonRun, bin):
    """
    Bins the uncertainty according to the provided bin size.

    :param run: The run containing the uncertainty to bin
    :param bin: The bin size of the new uncertainty in nano-seconds
    :return uncertainty: The binned uncertainty
    """

    pass


def calculate_muon_uncertainty(run: MuonRun):
    """
    Calculates the uncertainty based on the two histograms specified as 'CalcHists' in the MuonRun meta.

    :param run:
    :return None: The uncertainty attribute in the run is set to the calculated uncertainty
    """

    pass


def calculate_muon_asymmetry(run: MuonRun):
    """
    Calculates the asymmetry based on the two histograms specified as 'CalcHists' in the MuonRun meta.

    :param run:
    :return None: The asymmetry attribute in the run is set to the calculated asymmetry
    """

    pass


def calculate_muon_background_radiation(run: MuonRun):
    """
    Calculates the background radiation of the two histograms specified as 'CalcHists' in the MuonRun meta.

    :param run:
    :return (bkgd_one, bkgd_two): The background of the first and second histogram, respectively
    """

    pass


def calculate_muon_good_histogram_limits(run: MuonRun):
    """
    Calculates the limits for which an asymmetry can be calculated from this histograms specified as
    'CalcHists' in the MuonRun meta.

    :param run:
    :return
        start_one: First bin to use in the first histogram
        start_two: First bin to use in the second histogram
        end_one: Last bin to use in the first histogram
        end_two: Last bin to use in the second histogram
        t0: The initial time
    """

    pass


def calculate_muon_fft(asymmetry):
    """
    Calculates the fft of the given asymmetry.

    :param asymmetry:
    :return f, fft: An array of frequencies in MHz and an array for the fft
    """

    pass





