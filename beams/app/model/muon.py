
# Standard Library Packages
import uuid

# Installed Packages
import numpy as np

# BEAMS Modules
from app.model import files, mufyt


class MuonRun:
    def __init__(self, data, meta: dict, file):
        self.data = data
        self.meta = meta
        self.file = file
        self.id = str(uuid.uuid4())

        self.asymmetry = None
        self.uncertainty = None
        self.time = None
        self.fit = mufyt.Fit()

        self.alpha = 1
        self.beta = 1
        self.t0 = None

    def __str__(self):
        return '[MuonRun: ID={}, meta={}]'.format(self.id, self.meta)


def build_muon_run_from_histogram_file(file, meta=None) -> MuonRun:
    """
    Builds a MuonRun object (Asymmetry, Uncertainty, Time, etc) based on the given data and meta.

    :param data: A pandas dataframe containing the histograms with their titles as column heads.
    :param meta: A dictionary containing the meta data for the run
    :param file: The file path of the file associated with this run
    :return run: a MuonRun object
    """
    reader = files.file(file)
    data = reader.read_data()
    meta = meta if meta else reader.read_meta()

    run = MuonRun(data, meta, file)

    calculate_muon_asymmetry(run)
    calculate_muon_uncertainty(run)
    calculate_muon_time(run)

    print(run.time)

    return run


def build_muon_run_from_asymmetry_file(file, meta=None) -> MuonRun:
    reader = files.file(file)
    data = reader.read_data()
    meta = meta if meta else reader.read_meta()

    run = MuonRun(None, meta, file)
    run.asymmetry = data.loc[:, 'Asymmetry'].values
    run.uncertainty = data.loc[:, 'Uncertainty'].values
    run.time = data.loc[:, 'Time'].values
    run.t0 = run.meta[files.T0_KEY]

    return run


def correct_muon_asymmetry(run: MuonRun, alpha=None, beta=None):
    """
    Recalculates the asymmetry with the alpha value given in the MuonRun object or the one specified.
    By default it is set to 1 in the MuonRun object.

    :param run: The MuonRun with updated alpha value
    :param alpha: Optional alpha to be used, will replace the one in the MuonRun.
    :param beta: Optional beta to be used, will replace the one in the MuonRun
    """

    if alpha:
        run.alpha = alpha

    if beta:
        run.beta = beta

    reader = files.file(run.file)
    if reader.DATA_FORMAT == files.Format.HISTOGRAM:
        calculate_muon_asymmetry(run)
    elif reader.DATA_FORMAT == files.Format.ASYMMETRY:
        data = reader.read_data()
        run.asymmetry = data.loc[:, 'Asymmetry'].values

    run.asymmetry = ((run.alpha - 1) + (run.alpha + 1) * run.asymmetry) / \
                    ((run.alpha * run.beta + 1) + (run.alpha * run.beta - 1) * 2)


def bin_muon_asymmetry(run: MuonRun, new_bin):
    """
    Bins the asymmetry according to the provided bin size.

    :param run: The run containing the asymmetry to bin
    :param new_bin: The bin size of the new asymmetry in nano-seconds
    :return asymmetry: The binned asymmetry
    """
    bin_full = float(run.meta[files.BIN_SIZE_KEY]) / 1000
    bin_binned = float(new_bin) / 1000
    num_bins = len(run.asymmetry)

    if bin_binned <= bin_full:
        return run.asymmetry

    binned_indices_per_bin = int(np.round(bin_binned / bin_full))
    binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
    leftover_bins = int(num_bins % binned_indices_per_bin)

    if leftover_bins:
        reshaped_asymmetry = np.reshape(run.asymmetry[:-leftover_bins],
                                        (binned_indices_total, binned_indices_per_bin))
    else:
        reshaped_asymmetry = np.reshape(run.asymmetry, (binned_indices_total, binned_indices_per_bin))

    binned_asymmetry = np.apply_along_axis(np.mean, 1, reshaped_asymmetry)

    return binned_asymmetry


def bin_muon_uncertainty(run: MuonRun, new_bin):
    """
    Bins the uncertainty according to the provided bin size.

    :param run: The run containing the uncertainty to bin
    :param new_bin: The bin size of the new uncertainty in nano-seconds
    :return uncertainty: The binned uncertainty
    """

    bin_full = float(run.meta[files.BIN_SIZE_KEY]) / 1000
    bin_binned = float(new_bin) / 1000
    num_bins = len(run.asymmetry)

    if bin_binned <= bin_full:
        return run.uncertainty

    binned_indices_per_bin = int(np.round(bin_binned / bin_full))
    binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
    leftover_bins = int(num_bins % binned_indices_per_bin)

    if leftover_bins:
        reshaped_uncertainty = np.reshape(run.uncertainty[:-leftover_bins],
                                          (binned_indices_total, binned_indices_per_bin))
    else:
        reshaped_uncertainty = np.reshape(run.uncertainty, (binned_indices_total, binned_indices_per_bin))

    binned_uncertainty = 1 / binned_indices_per_bin * np.sqrt(np.apply_along_axis(np.sum, 1,
                                                                                  reshaped_uncertainty ** 2))

    return binned_uncertainty


def bin_muon_time(run: MuonRun, new_bin):
    """
    Calculates the binned time array.

    :param run:
    :param new_bin:
    :return time:
    """

    bin_full = float(run.meta[files.BIN_SIZE_KEY]) / 1000
    bin_binned = float(new_bin) / 1000
    num_bins = len(run.asymmetry)
    t0 = float(run.t0)

    if bin_binned <= bin_full:
        return run.time

    binned_indices_per_bin = int(np.round(bin_binned / bin_full))
    binned_indices_total = int(np.floor(num_bins / binned_indices_per_bin))
    time_per_binned = binned_indices_per_bin * bin_full

    return (np.arange(binned_indices_total) * time_per_binned) + (t0 * bin_full) + (time_per_binned / 2)


def calculate_muon_uncertainty(run: MuonRun):
    """
    Calculates the uncertainty based on the two histograms specified as 'CalcHists' in the MuonRun meta.

    :param run:
    :return None: The uncertainty attribute in the run is set to the calculated uncertainty
    """
    start_bin_one, start_bin_two, end_bin_one, end_bin_two, t0 = calculate_muon_good_histogram_limits(run)
    run.t0 = t0

    hist_one = run.data.loc[start_bin_one - 1: end_bin_one, run.meta[files.CALC_HISTS_KEY][0]].values
    hist_two = run.data.loc[start_bin_two - 1: end_bin_two, run.meta[files.CALC_HISTS_KEY][1]].values

    d_one = np.sqrt(hist_one)
    d_two = np.sqrt(hist_two)

    np.nan_to_num(hist_one, copy=False)
    np.nan_to_num(hist_two, copy=False)

    np.seterr(divide='ignore', invalid='ignore')
    uncertainty = np.array(np.sqrt(np.power((2 * hist_one * d_two / np.power(hist_two + hist_one, 2)), 2) +
                                   np.power((2 * hist_two * d_one / np.power(hist_two + hist_one, 2)), 2)))
    np.seterr(divide='warn', invalid='warn')

    np.nan_to_num(uncertainty, copy=False)

    run.uncertainty = uncertainty


def calculate_muon_asymmetry(run: MuonRun):
    """
    Calculates the asymmetry based on the two histograms specified as 'CalcHists' in the MuonRun meta.

    :param run:
    :return None: The asymmetry attribute in the run is set to the calculated asymmetry
    """
    start_bin_one, start_bin_two, end_bin_one, end_bin_two, t0 = calculate_muon_good_histogram_limits(run)
    run.t0 = t0

    hist_one = run.data.loc[start_bin_one - 1: end_bin_one, run.meta[files.CALC_HISTS_KEY][0]].values
    hist_two = run.data.loc[start_bin_two - 1: end_bin_two, run.meta[files.CALC_HISTS_KEY][1]].values

    bkgd_one, bkgd_two = calculate_muon_background_radiation(run)

    run.asymmetry = ((hist_one - bkgd_one) - (hist_two - bkgd_two)) / \
                    ((hist_two - bkgd_two) + (hist_one - bkgd_one))


def calculate_muon_time(run: MuonRun):
    """
    Creates and sets the time array for a given run. Asymmetry should be set before so we know how long to make it.

    :param run:
    :return:
    """
    print(run.t0)
    run.time = (np.arange(len(run.asymmetry)) * float(run.meta[files.BIN_SIZE_KEY]) / 1000) + \
               (run.t0 * float(run.meta[files.BIN_SIZE_KEY]) / 1000)


def calculate_muon_background_radiation(run: MuonRun):
    """
    Calculates the background radiation of the two histograms specified as 'CalcHists' in the MuonRun meta.

    :param run:
    :return (bkgd_one, bkgd_two): The background of the first and second histogram, respectively
    """

    hist_one_title = run.meta[files.CALC_HISTS_KEY][0]
    bkgd_one_start = run.meta[files.BACKGROUND_ONE_KEY][hist_one_title]
    bkgd_one_end = run.meta[files.BACKGROUND_TWO_KEY][hist_one_title]
    background_one = run.data[hist_one_title][int(bkgd_one_start):int(bkgd_one_end) - 1]
    bkgd_one = np.mean(background_one)

    hist_two_title = run.meta[files.CALC_HISTS_KEY][1]
    bkgd_two_start = run.meta[files.BACKGROUND_ONE_KEY][hist_two_title]
    bkgd_two_end = run.meta[files.BACKGROUND_TWO_KEY][hist_two_title]
    background_two = run.data[hist_two_title][int(bkgd_two_start):int(bkgd_two_end) - 1]
    bkgd_two = np.mean(background_two)

    return bkgd_one, bkgd_two


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

    t_one = int(run.meta[files.T0_KEY][run.meta[files.CALC_HISTS_KEY][0]])
    t_two = int(run.meta[files.T0_KEY][run.meta[files.CALC_HISTS_KEY][1]])
    start_one = int(run.meta[files.GOOD_BIN_ONE_KEY][run.meta[files.CALC_HISTS_KEY][0]])
    start_two = int(run.meta[files.GOOD_BIN_ONE_KEY][run.meta[files.CALC_HISTS_KEY][1]])
    end_one = int(run.meta[files.GOOD_BIN_TWO_KEY][run.meta[files.CALC_HISTS_KEY][0]])
    end_two = int(run.meta[files.GOOD_BIN_TWO_KEY][run.meta[files.CALC_HISTS_KEY][1]])

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


def calculate_muon_fft(asymmetry, time):
    """
    Calculates the fft of the given asymmetry (Thanks Ben)

    :param asymmetry:
    :param time:
    :return z, fft: An array of frequencies in MHz and an array for the fft
    """

    f_min = 0
    f_max = 1
    f_step = (f_max - f_min)/100
    z_min = 2 * np.pi * f_min
    z_max = 2 * np.pi * f_max
    z_step = 2 * np.pi * f_step

    low_step = int(np.ceil((z_min - 1e-8) / z_step))
    high_step = int(np.floor((z_max + 1e-8) / z_step)) + 1
    z = np.arange(low_step, high_step) * z_step

    try:
        x_step = time[1] - time[0]
    except IndexError:
        return [0], [0]

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

    return z, fft


def calculate_muon_integration(run: MuonRun):
    return np.trapz(run.asymmetry, run.time)
