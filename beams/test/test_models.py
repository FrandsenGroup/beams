import pytest
import pickle
import numpy as np

from app.model import objects
from app.resources import resources


def close_enough(val_one, val_two, tolerance):
    return abs(val_one - val_two) <= tolerance


class TestHistograms:
    @pytest.mark.parametrize("input_array, t0, good_start, good_end, bkgd_start, bkgd_end, run_id, bin_size, title",
                             [([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                               8, 5, 19, 0, 4, "RANDOM_ID", 0.2, "Front")])
    def test_basic_construction(self, input_array, t0, good_start, good_end, bkgd_start,
                                bkgd_end, run_id, bin_size, title):
        objects.Histogram(input_array, t0, good_start, good_end, bkgd_start, bkgd_end, title, run_id, bin_size)

    @pytest.mark.parametrize("hist_one, hist_two, start_bin_one, start_bin_two, end_bin_one, end_bin_two, init_dif",
                             # Two histograms with identical meta values.
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2),
                               1030, 1030, 27648, 27648, 50),

                              # Histograms with different time zeroes.
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 979, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2),
                               1031, 1030, 27648, 27647, 51),

                              # Histograms with different good bin starts.
                              (objects.Histogram(range(27648),
                                                 980, 2000, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2),
                               2000, 2000, 27648, 27648, 1020),
                              ])
    def test_intersect(self, hist_one: objects.Histogram, hist_two: objects.Histogram,
                       start_bin_one, start_bin_two, end_bin_one, end_bin_two, init_dif):
        start_bin_one_c, start_bin_two_c, end_bin_one_c, end_bin_two_c, init_dif_c = hist_one.intersect(hist_two)

        assert start_bin_one_c == start_bin_one
        assert start_bin_two_c == start_bin_two
        assert end_bin_one_c == end_bin_one
        assert end_bin_two_c == end_bin_two
        assert init_dif_c == init_dif

    @pytest.mark.parametrize("hist_one, hist_two",
                             # Start bin is greater then the end bin
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 1000, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 979, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)),

                              # Start bin is below 0
                              (objects.Histogram(range(27648),
                                                 980, -5, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)),

                              # End bin is above length of histogram
                              (objects.Histogram(range(27648),
                                                 980, 2000, 70000, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2))
                              ])
    def test_intersect_raise_exception(self, hist_one: objects.Histogram, hist_two: objects.Histogram):
        with pytest.raises(ValueError):
            hist_one.intersect(hist_two)

        with pytest.raises(ValueError):
            hist_two.intersect(hist_one)

    @pytest.mark.parametrize("hist, radiation",
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               485.0),
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 0, 900, "Front", "RANDOM_ID", 0.2),
                               450.0),
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 700, 700, "Front", "RANDOM_ID", 0.2),
                               700),
                              ])
    def test_background_radiation(self, hist: objects.Histogram, radiation):
        radiation_c = hist.background_radiation()

        assert radiation_c == radiation

    @pytest.mark.parametrize("hist",
                             # Background start is below 0
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 27648, -5, 900, "Front", "RANDOM_ID", 0.2)),
                              # Background start is above background end
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 1200, 900, "Front", "RANDOM_ID", 0.2)),
                              # Background end is above length of histogram
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 700, 70000, "Front", "RANDOM_ID", 0.2)),
                              ])
    def test_background_radiation_raise_exception(self, hist: objects.Histogram):
        with pytest.raises(ValueError):
            hist.background_radiation()

    @pytest.mark.parametrize("hist",
                             [(objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2))])
    def test_pickling(self, hist):
        # This should fail if you have added an attribute to the histogram class and not added it to the
        #   __array_finalize__ method (this will make more sense if you look at the code).
        histogram_unpickled = pickle.loads(pickle.dumps(hist))
        assert hist == histogram_unpickled

    @pytest.mark.parametrize("hist",
                             [(objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2))])
    def test_persistent_object(self, hist):
        histogram_minimized = hist.get_persistent_data()
        histogram_maximized = hist.build_from_persistent_data(histogram_minimized)

        assert hist == histogram_maximized

    @pytest.mark.parametrize("hist",
                             [(objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2))])
    def test_persistent_with_pickling(self, hist):
        histogram_minimized = hist.get_persistent_data()
        histogram_minimized_unpickled = pickle.loads(pickle.dumps(histogram_minimized))
        histogram_maximized = hist.build_from_persistent_data(histogram_minimized_unpickled)

        assert hist == histogram_maximized

    @pytest.mark.parametrize("hists, correct_combined_hist",
                             [((objects.Histogram(range(27648),
                                                  980, 680, 25000, 600, 1000, "Front", "3412", 0.2),
                                objects.Histogram(range(27648),
                                                  980, 1030, 27648, 500, 900, "Front", "3413", 0.2)),
                               (objects.Histogram(range(0, 55296, 2),
                                                  980, 1030, 25000, 600, 900, "Front", "3412, 3413", 0.2))),
                              ((objects.Histogram(range(27648),
                                                  1000, 680, 25000, 600, 1000, "Front", "3412", 0.2),
                                objects.Histogram(range(27648),
                                                  980, 1030, 27648, 500, 900, "Front", "3413", 0.2)),
                               (objects.Histogram(range(20, 55276, 2),
                                                  980, 1030, 24980, 580, 900, "Front", "3412, 3413", 0.2))),
                              ((objects.Histogram(range(30000),
                                                  600, 1000, 23400, 120, 480, "Back", "1612", 0.2),
                                objects.Histogram(range(30000),
                                                  568, 1200, 26000, 122, 464, "Back", "1613", 0.2)),
                               (objects.Histogram(range(32, 59968, 2),
                                                  568, 1200, 23368, 122, 448, "Back", "1612, 1613", 0.2))),
                              ((objects.Histogram(range(21000),
                                                  500, 550, 20000, 65, 420, "Forw", "19232", 0.3),
                                objects.Histogram(range(21000),
                                                  600, 613, 20380, 50, 553, "Forw", "19233", 0.3),
                                objects.Histogram(range(21000),
                                                  300, 334, 19670, 66, 120, "Forw", "19234", 0.3)
                                ),
                               (objects.Histogram(range(500, 62600, 3),
                                                  300, 350, 19670, 66, 120, "Forw", "doesn't matter", 0.3)))

                              ])
    def test_combine(self, hists, correct_combined_hist):
        combined = objects.Histogram.combine(hists)
        assert combined == correct_combined_hist

    @pytest.mark.parametrize("hists",
                             [(objects.Histogram(range(27648),
                                                 980, 680, 25000, 600, 1000, "Front", "3412", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 500, 900, "Front", "3413", 0.3)),
                              (objects.Histogram(range(27648),
                                                 980, 680, 25000, 600, 1000, "Front", "3412", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 500, 900, "Back", "3413", 0.3)),
                              [objects.Histogram(range(27648),
                                                 980, 680, 25000, 600, 1000, "Front", "3412", 0.2)]
                              ])
    def test_combine_exception(self, hists):
        with pytest.raises(ValueError):
            objects.Histogram.combine(hists)


class TestAsymmetries:
    @pytest.mark.parametrize("input_array, t0, bin_size, uncertainty, time",
                             [(range(27648), 980, 0.2, range(27648), range(27648))])
    def test_first_constructor_combination(self, input_array, t0, bin_size, uncertainty, time):
        # Test construction without histograms
        objects.Asymmetry(input_array=input_array, time_zero=t0, bin_size=bin_size, uncertainty=uncertainty, time=time)

    @pytest.mark.parametrize("hist_one, hist_two",
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2))])
    def test_second_constructor_combination(self, hist_one, hist_two):
        asymmetry = objects.Asymmetry(histogram_one=hist_one, histogram_two=hist_two)
        assert asymmetry.bin_size == 0.2
        assert asymmetry.time_zero == 50
        assert asymmetry.alpha == 1
        assert asymmetry.uncertainty is not None
        assert asymmetry.time is not None

    @pytest.mark.parametrize("asymmetry",
                             [(objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                                 uncertainty=range(27648), time=range(27648))),
                              (objects.Asymmetry(histogram_one=objects.Histogram(range(27648),
                                                                                 980, 1030, 27648, 70, 900, "Front",
                                                                                 "RANDOM_ID", 0.2),
                                                 histogram_two=objects.Histogram(range(27648),
                                                                                 980, 1030, 27648, 70, 900, "Back",
                                                                                 "RANDOM_ID", 0.2)))])
    def test_pickling(self, asymmetry):
        # This should fail if you have added an attribute to the asymmetry class and not added it to the
        #   __array_finalize__ method (this will make more sense if you look at the code).
        asymmetry_unpickled = pickle.loads(pickle.dumps(asymmetry))
        assert asymmetry == asymmetry_unpickled

    @pytest.mark.parametrize("asymmetry",
                             [(objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                                 uncertainty=range(27648), time=range(27648))),
                              (objects.Asymmetry(histogram_one=objects.Histogram(range(27648),
                                                                                 980, 1030, 27648, 70, 900, "Front",
                                                                                 "RANDOM_ID", 0.2),
                                                 histogram_two=objects.Histogram(range(27648),
                                                                                 980, 1030, 27648, 70, 900, "Back",
                                                                                 "RANDOM_ID", 0.2)))])
    def test_persistent_object(self, asymmetry: objects.Asymmetry):
        asymmetry_minimized = asymmetry.get_persistent_data()
        asymmetry_maximized = asymmetry.build_from_persistent_data(asymmetry_minimized)

        assert asymmetry == asymmetry_maximized

    @pytest.mark.parametrize("asymmetry",
                             [(objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                                 uncertainty=range(27648), time=range(27648))),
                              (objects.Asymmetry(histogram_one=objects.Histogram(range(27648),
                                                                                 980, 1030, 27648, 70, 900, "Front",
                                                                                 "RANDOM_ID", 0.2),
                                                 histogram_two=objects.Histogram(range(27648),
                                                                                 980, 1030, 27648, 70, 900, "Back",
                                                                                 "RANDOM_ID", 0.2)))])
    def test_persistent_with_pickling(self, asymmetry: objects.Asymmetry):
        asymmetry_minimized = asymmetry.get_persistent_data()
        asymmetry_minimized_unpickled = pickle.loads(pickle.dumps(asymmetry_minimized))
        asymmetry_maximized = asymmetry.build_from_persistent_data(asymmetry_minimized_unpickled)

        assert asymmetry == asymmetry_maximized

    @pytest.mark.parametrize("asymmetry, expected_binned_asymmetry, bin_size",
                             [(objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                                 uncertainty=range(27648), time=range(27648)),
                               objects.Asymmetry(input_array=range(36), time_zero=980, bin_size=0.2,
                                                 uncertainty=range(36), time=range(36)),
                               150),
                              # Bin size is reasonable, even cut of bins
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(10), time_zero=8, bin_size=1,
                                                 uncertainty=range(10), time=range(10)),
                               10),
                              # Bin size is reasonable, throws away leftover bins so we have 2 instead of 3.
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(2), time_zero=8, bin_size=1,
                                                 uncertainty=range(2), time=range(2)),
                               40),
                              # Bin size is equal to current bin size
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               1),
                              # Bin size == 0
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               0),
                              # Bin size that should result in a binned asymmetry of size == 1
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(1), time_zero=8, bin_size=1,
                                                 uncertainty=range(1), time=range(1)),
                               100)
                              ])
    def test_bin_lengths(self, asymmetry, expected_binned_asymmetry, bin_size):
        given_binned_asymmetry = asymmetry.bin(bin_size)
        assert len(given_binned_asymmetry) == len(expected_binned_asymmetry)
        assert len(given_binned_asymmetry.time) == len(expected_binned_asymmetry.time)
        assert len(given_binned_asymmetry.uncertainty) == len(expected_binned_asymmetry.uncertainty)

        if given_binned_asymmetry.calculated is not None or expected_binned_asymmetry.calculated is not None:
            assert len(given_binned_asymmetry.calculated) == len(expected_binned_asymmetry.calculated)

    @pytest.mark.parametrize("asymmetry, expected_binned_asymmetry, bin_size",
                             [(objects.Asymmetry(input_array=[1 for _ in range(15)], uncertainty=[1 for _ in range(15)],
                                                 time=range(15), time_zero=2, bin_size=1),
                               objects.Asymmetry(input_array=[1, 1, 1], uncertainty=[0.447, 0.447, 0.447],
                                                 time=range(3), time_zero=2, bin_size=1),
                               5),
                              (objects.Asymmetry(input_array=[1 for _ in range(15)], uncertainty=[1 for _ in range(15)],
                                                 time=range(15), time_zero=2, bin_size=1),
                               objects.Asymmetry(input_array=[1, 1], uncertainty=[0.408, 0.408],
                                                 time=range(2), time_zero=2, bin_size=1),
                               6),
                              (objects.Asymmetry(input_array=[3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9, 8, 0],
                                                 uncertainty=[3, 2, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9, 8, 0],
                                                 time=range(15), time_zero=2, bin_size=1),
                               objects.Asymmetry(input_array=[3.5, 6.5], uncertainty=[1.481, 2.682],
                                                 time=range(2), time_zero=2, bin_size=1),
                               6),
                              ])
    def test_bin_values(self, asymmetry, expected_binned_asymmetry, bin_size):
        given_binned_asymmetry = asymmetry.bin(bin_size)

        assert np.allclose(given_binned_asymmetry, expected_binned_asymmetry, 0.005)
        assert np.allclose(given_binned_asymmetry.uncertainty, expected_binned_asymmetry.uncertainty, 0.005)

        if given_binned_asymmetry.calculated is not None or expected_binned_asymmetry.calculated is not None:
            np.allclose(given_binned_asymmetry.calculated, expected_binned_asymmetry.calculated, 0.005)

    @pytest.mark.parametrize("asymmetry, bin_size",
                             # Bin size would produce an asymmetry with no elements.
                             [(objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)), 101),
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=.1,
                                                 uncertainty=range(100), time=range(100)), 1001),
                              # Bin size is negative
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)), -1)
                              ])
    def test_bin_raise_exception(self, asymmetry, bin_size):
        with pytest.raises(ValueError):
            asymmetry.bin(bin_size)

    @pytest.mark.parametrize("asymmetry, min_time, max_time, expected_integration, expected_uncertainty",
                             [
                                 (objects.Asymmetry(input_array=np.zeros(10), time_zero=8, bin_size=1,
                                                    uncertainty=np.zeros(10), time=np.array(range(10))),
                                  None, None, 0, 0),
                                 (objects.Asymmetry(input_array=np.ones(10), time_zero=8, bin_size=1,
                                                    uncertainty=np.ones(10), time=np.array(range(10))),
                                  None, None, 9, 0.003),
                                 (objects.Asymmetry(input_array=np.array(range(10)), time_zero=8, bin_size=1,
                                                    uncertainty=np.ones(10), time=np.array(range(10))),
                                  None, None, 40.5, 0.003),
                                 (objects.Asymmetry(input_array=np.array(range(10)), time_zero=8, bin_size=1,
                                                    uncertainty=np.array(range(10)), time=np.array(range(10))),
                                  None, None, 40.5, 0.017),
                                 (objects.Asymmetry(input_array=np.array(range(10)), time_zero=8, bin_size=1,
                                                    uncertainty=np.ones(10), time=np.array(range(10))),
                                  0, 1, 0, 0),
                                 (objects.Asymmetry(input_array=np.array(range(10)), time_zero=8, bin_size=1,
                                                    uncertainty=np.ones(10), time=np.array(range(10))),
                                  7, 9, 7.5, 0.001)
                             ])
    def test_integrate(self, asymmetry, min_time, max_time, expected_integration, expected_uncertainty):
        calculated_integration, calculated_uncertainty = asymmetry.integrate(min_time, max_time)
        assert close_enough(calculated_integration, expected_integration, 0.001)
        assert close_enough(calculated_uncertainty, expected_uncertainty, 0.001)

    @pytest.mark.parametrize("asymmetry, min_time, max_time",
                             [
                                 (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                    uncertainty=range(100), time=range(100)), 9, 4),
                                 (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                    uncertainty=range(100), time=range(100)), '1', None)
                             ])
    def test_integrate_raises_exception(self, asymmetry, min_time, max_time):
        with pytest.raises(Exception):
            asymmetry.integrate(min_time, max_time)

    @pytest.mark.parametrize("asymmetry, expected_corrected_asymmetry, alpha",
                             # Correcting to value of 1.0 with a raw asymmetry.
                             [(objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               1),
                              # Correcting to a value of 2.0 when the alpha of an asymmetry is already 2.0.
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100), alpha=2),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100), alpha=2),
                               2),
                              # Correcting an array of 1's with any alpha should result in array of 1's
                              (objects.Asymmetry(input_array=[1, 1, 1], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 1, 1], time=range(3), alpha=1),
                               objects.Asymmetry(input_array=[1, 1, 1], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 1, 1], time=range(3), alpha=2.458),
                               2.458),
                              # Correcting an array of values with a different alpha
                              (objects.Asymmetry(input_array=[1, 2, 3], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 2, 3], time=range(3), alpha=1),
                               objects.Asymmetry(input_array=[1.000, 1.313, 1.510], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 2, 3], time=range(3), alpha=2.458),
                               2.458)
                              ])
    def test_correct(self, asymmetry, expected_corrected_asymmetry, alpha):
        given_corrected_asymmetry = asymmetry.correct(alpha)

        assert given_corrected_asymmetry.alpha == expected_corrected_asymmetry.alpha
        assert np.allclose(given_corrected_asymmetry, expected_corrected_asymmetry, 0.005)
        assert np.allclose(given_corrected_asymmetry.uncertainty, expected_corrected_asymmetry.uncertainty, 0.005)

        if given_corrected_asymmetry.calculated is not None or expected_corrected_asymmetry.calculated is not None:
            assert np.allclose(given_corrected_asymmetry.calculated, expected_corrected_asymmetry.calculated, 0.005)

    @pytest.mark.parametrize("asymmetry, expected_corrected_asymmetry",
                             # Calling raw on a raw asymmetry
                             [(objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100))),
                              # Calling raw on an array of 1's with a non-one alpha (should be the same)
                              (objects.Asymmetry(input_array=[1, 1, 1], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 1, 1], time=range(3), alpha=2.458),
                               objects.Asymmetry(input_array=[1, 1, 1], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 1, 1], time=range(3))),
                              # Calling raw on a corrected asymmetry. (Inverse is in test_correct).
                              (objects.Asymmetry(input_array=[1.000, 1.313, 1.510], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 2, 3], time=range(3), alpha=2.458),
                               objects.Asymmetry(input_array=[1, 2, 3], time_zero=8, bin_size=1,
                                                 uncertainty=[1, 2, 3], time=range(3)))
                              ])
    def test_raw(self, asymmetry, expected_corrected_asymmetry):
        given_corrected_asymmetry = asymmetry.raw()

        assert given_corrected_asymmetry.alpha == 1.0
        assert np.allclose(given_corrected_asymmetry, expected_corrected_asymmetry, 0.005)
        assert np.allclose(given_corrected_asymmetry.uncertainty, expected_corrected_asymmetry.uncertainty, 0.005)

        if given_corrected_asymmetry.calculated is not None or expected_corrected_asymmetry.calculated is not None:
            assert np.allclose(given_corrected_asymmetry.calculated, expected_corrected_asymmetry.calculated, 0.005)

    @pytest.mark.parametrize("asymmetry, expected_cut_asymmetry, min_time, max_time",
                             # Using bounds of array as range to cut
                             [(objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               0, 100),
                              # Create a range of 1
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=[0], time_zero=8, bin_size=1,
                                                 uncertainty=[0], time=[0]),
                               0, 1),
                              # Create a range of of more then one to the end
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(50), time_zero=8, bin_size=1,
                                                 uncertainty=range(50), time=range(50)),
                               0, 50),
                              # Use a negative value as minimum time
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(50), time_zero=8, bin_size=1,
                                                 uncertainty=range(50), time=range(50)),
                               -5, 50),
                              # Using a very large value as maximum time
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               0, 500),
                              # Get a middle range of the asymmetry
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(50, 70), time_zero=8, bin_size=1,
                                                 uncertainty=range(50, 70), time=range(50, 70)),
                               50, 70),
                              # Use bounds above end of asymmetry
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=[], time_zero=8, bin_size=1,
                                                 uncertainty=[], time=[]),
                               500, 700),
                              # Use bounds below beginning of asymmetry
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=[], time_zero=8, bin_size=1,
                                                 uncertainty=[], time=[]),
                               -10, -1),
                              # Use None as an upper bound (end is the boundary)
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(5, 100), time_zero=8, bin_size=1,
                                                 uncertainty=range(5, 100), time=range(5, 100)),
                               5, None),
                              # Use None as a lower bound (beginning is boundary)
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=range(70), time_zero=8, bin_size=1,
                                                 uncertainty=range(70), time=range(70)),
                               None, 70),
                              # Use None as upper boundary when lower is above end of asymmetry
                              (objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               objects.Asymmetry(input_array=[], time_zero=8, bin_size=1,
                                                 uncertainty=[], time=[]),
                               500, None)
                              ])
    def test_cut(self, asymmetry, expected_cut_asymmetry, min_time, max_time):
        given_cut_asymmetry = asymmetry.cut(min_time, max_time)

        assert np.allclose(given_cut_asymmetry, expected_cut_asymmetry, 0.005)
        assert np.allclose(given_cut_asymmetry.uncertainty, expected_cut_asymmetry.uncertainty, 0.005)
        assert np.allclose(given_cut_asymmetry.time, expected_cut_asymmetry.time, 0.005)

        if given_cut_asymmetry.calculated is not None or expected_cut_asymmetry.calculated is not None:
            assert np.allclose(given_cut_asymmetry.calculated, expected_cut_asymmetry.calculated, 0.005)

    @pytest.mark.parametrize("asymmetry, min_time, max_time",
                             # Provide a min time and max time which create an invalid range
                             [(objects.Asymmetry(input_array=range(100), time_zero=8, bin_size=1,
                                                 uncertainty=range(100), time=range(100)),
                               55, 50)
                              ])
    def test_cut_raise_exception(self, asymmetry, min_time, max_time):
        with pytest.raises(ValueError):
            asymmetry.cut(min_time, max_time)


class TestUncertainties:
    @pytest.mark.parametrize("input_array, bin_size",
                             [([1, 2, 3, 4, 5, 6], 0.2)])
    def test_first_constructor_combination(self, input_array, bin_size):
        uncertainty = objects.Uncertainty(input_array, bin_size)
        assert uncertainty.bin_size == 0.2

    @pytest.mark.parametrize("hist_one, hist_two",
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2))])
    def test_second_constructor_combination(self, hist_one, hist_two):
        uncertainty = objects.Uncertainty(histogram_one=hist_one, histogram_two=hist_two)
        assert uncertainty.bin_size == 0.2

    @pytest.mark.parametrize("uncertainty",
                             [(objects.Uncertainty([1, 2, 3, 4, 5, 6, 7], 0.2))])
    def test_pickling(self, uncertainty):
        uncertainty_unpickled = pickle.loads(pickle.dumps(uncertainty))
        assert uncertainty_unpickled == uncertainty

    @pytest.mark.parametrize("uncertainty",
                             [(objects.Uncertainty([1, 2, 3, 4, 5, 6, 7], 0.2))])
    def test_persistent_object(self, uncertainty: objects.Uncertainty):
        uncertainty_minimized = uncertainty.get_persistent_data()
        uncertainty_maximized = uncertainty.build_from_persistent_data(uncertainty_minimized)

        assert uncertainty_maximized == uncertainty

    @pytest.mark.parametrize("uncertainty",
                             [(objects.Uncertainty([1, 2, 3, 4, 5, 6, 7], 0.2))])
    def test_persistent_with_pickling(self, uncertainty: objects.Uncertainty):
        uncertainty_minimized = uncertainty.get_persistent_data()
        uncertainty_minimized_unpickled = pickle.loads(pickle.dumps(uncertainty_minimized))
        uncertainty_maximized = uncertainty.build_from_persistent_data(uncertainty_minimized_unpickled)

        assert uncertainty_maximized == uncertainty

    @pytest.mark.parametrize("uncertainty, expected_uncertainty, packing",
                             [
                                 (objects.Uncertainty(range(100), 1),
                                  objects.Uncertainty(range(100), 1),
                                  1),
                                 (objects.Uncertainty(range(10), 1),
                                  objects.Uncertainty([0.500, 1.802, 3.201, 4.609, 6.020], 2),
                                  2),
                                 (objects.Uncertainty(range(10), 1),
                                  objects.Uncertainty(range(10), 1),
                                  0.5)
                             ])
    def test_binning(self, uncertainty, expected_uncertainty, packing):
        given_uncertainty = uncertainty.bin(packing)

        assert np.allclose(given_uncertainty, expected_uncertainty, 0.005)
        assert given_uncertainty.bin_size == expected_uncertainty.bin_size

    @pytest.mark.parametrize("uncertainty, packing",
                             [
                                 (objects.Uncertainty(range(1), 1), 2)
                             ])
    def test_binning_raise_exception(self, uncertainty, packing):
        with pytest.raises(ValueError):
            uncertainty.bin(packing)


class TestTimes:
    @pytest.mark.parametrize("input_array, bin_size, time_zero",
                             [([1, 2, 3, 4, 5, 6], 0.2, 1.0)])
    def test_first_constructor_combination(self, input_array, bin_size, time_zero):
        time = objects.Time(input_array, bin_size_ns=bin_size, time_zero_bin=time_zero)
        assert time.bin_size == 0.2
        assert time.time_zero == 1.0

    @pytest.mark.parametrize("length, bin_size, time_zero_ns",
                             [(1000, 1, 10)])
    def test_second_constructor_combination(self, length, bin_size, time_zero_ns):
        time = objects.Time(length=length, bin_size_ns=bin_size, time_zero_ns=time_zero_ns)
        assert len(time) == length
        assert close_enough(time[1] - time[0], bin_size / 1000, 0.001)
        assert time.time_zero == 0

    @pytest.mark.parametrize("length, bin_size, time_zero_bin",
                             [(1000, 1, 10)])
    def test_third_constructor_combination(self, length, bin_size, time_zero_bin):
        time = objects.Time(length=length, bin_size_ns=bin_size, time_zero_bin=time_zero_bin)
        assert len(time) == length
        assert close_enough(time[1] - time[0], bin_size / 1000, 0.001)
        assert time.time_zero == time_zero_bin
        assert close_enough(time[0], time_zero_bin * bin_size / 1000, 0.001)

    @pytest.mark.parametrize("time",
                             [(objects.Time([1, 2, 3, 4, 5, 6, 7], 0.2))])
    def test_pickling(self, time):
        time_unpickled = pickle.loads(pickle.dumps(time))
        assert time_unpickled == time

    @pytest.mark.parametrize("time",
                             [(objects.Time([1, 2, 3, 4, 5, 6, 7], 0.2))])
    def test_persistent_object(self, time: objects.Time):
        time_minimized = time.get_persistent_data()
        time_maximized = time.build_from_persistent_data(time_minimized)

        assert time_maximized == time

    @pytest.mark.parametrize("time",
                             [(objects.Time([1, 2, 3, 4, 5, 6, 7], 0.2))])
    def test_persistent_with_pickling(self, time: objects.Time):
        time_minimized = time.get_persistent_data()
        time_minimized_unpickled = pickle.loads(pickle.dumps(time_minimized))
        time_maximized = time.build_from_persistent_data(time_minimized_unpickled)

        assert time_maximized == time

    @pytest.mark.parametrize("time, expected_time, packing",
                             [
                                 (objects.Time(range(100), 1),
                                  objects.Time(range(100), 1),
                                  1),
                                 (objects.Time(range(10), 1),
                                  objects.Time([0.001, 0.003, 0.005, 0.007, 0.009], 2),
                                  2),
                                 (objects.Time(range(10), 1),
                                  objects.Time(range(10), 1),
                                  0.5)
                             ])
    def test_binning(self, time, expected_time, packing):
        given_time = time.bin(packing)

        assert np.allclose(given_time, given_time, 0.005)
        assert given_time.bin_size == given_time.bin_size
        assert given_time.time_zero == given_time.time_zero


class TestFits:  # Just the object
    @pytest.mark.parametrize("fit",
                             [(objects.Fit({}, "x", "a title", "a run id", None, None))])
    def test_pickling(self, fit):
        fit_unpickled = pickle.loads(pickle.dumps(fit))
        assert fit_unpickled == fit

    @pytest.mark.parametrize("fit",
                             [(objects.Fit({}, "x", "a title", "a run id", None,
                                           objects.Asymmetry(input_array=range(27648),
                                                             time_zero=980, bin_size=0.2,
                                                             uncertainty=range(27648), time=range(27648))))])
    def test_persistent_object(self, fit: objects.Fit):
        fit_minimized = fit.get_persistent_data()
        fit_maximized = fit.build_from_persistent_data(fit_minimized)

        assert fit_maximized == fit
        assert fit_maximized.asymmetry == fit.asymmetry

    @pytest.mark.parametrize("fit",
                             [(objects.Fit({}, "x", "a title", "a run id", None,
                                           objects.Asymmetry(input_array=range(27648),
                                                             time_zero=980, bin_size=0.2,
                                                             uncertainty=range(27648), time=range(27648))))])
    def test_persistent_with_pickling(self, fit: objects.Fit):
        fit_minimized = fit.get_persistent_data()
        fit_minimized_unpickled = pickle.loads(pickle.dumps(fit_minimized))
        fit_maximized = fit.build_from_persistent_data(fit_minimized_unpickled)

        assert fit_maximized == fit
        assert fit_maximized.asymmetry == fit.asymmetry


class TestFitDatasets:
    @pytest.mark.parametrize("dataset",
                             [(objects.FitDataset())])
    def test_pickling(self, dataset):
        dataset_unpickled = pickle.loads(pickle.dumps(dataset))
        assert dataset_unpickled == dataset

    @pytest.mark.parametrize("dataset",
                             [(objects.FitDataset(fits={
                                 "fit1": objects.Fit({}, "x", "a title", "a run id", None,
                                                     objects.Asymmetry(input_array=range(27648),
                                                                       time_zero=980, bin_size=0.2,
                                                                       uncertainty=range(27648), time=range(27648)))
                             }))])
    def test_persistent_object(self, dataset: objects.FitDataset):
        dataset_minimized = dataset.get_persistent_data()
        dataset_maximized = dataset.build_from_persistent_data(dataset_minimized)

        assert dataset_maximized == dataset

    @pytest.mark.parametrize("dataset",
                             [(objects.FitDataset(fits={
                                 "fit1": objects.Fit({}, "x", "a title", "a run id", None,
                                                     objects.Asymmetry(input_array=range(27648),
                                                                       time_zero=980, bin_size=0.2,
                                                                       uncertainty=range(27648), time=range(27648)))
                             }))])
    def test_persistent_with_pickling(self, dataset: objects.FitDataset):
        dataset_minimized = dataset.get_persistent_data()
        dataset_minimized_unpickled = pickle.loads(pickle.dumps(dataset_minimized))
        dataset_maximized = dataset.build_from_persistent_data(dataset_minimized_unpickled)

        assert dataset_maximized == dataset


class TestRunDatasets:
    def test_pickling(self):
        dataset = objects.RunDataset()
        dataset.histograms = {
            "h1": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
            "h2": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)
        }
        dataset.asymmetries = {
            "a1": objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                    uncertainty=range(27648), time=range(27648))
        }
        dataset.meta = {
            "m1": "someting",
            "m2": 2
        }
        dataset.histograms_used = ["h1", "h2"]

        dataset_unpickled = pickle.loads(pickle.dumps(dataset))
        assert dataset_unpickled.equals(dataset)

    def test_persistent_object(self):
        dataset = objects.RunDataset()
        dataset.histograms = {
            "h1": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
            "h2": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)
        }
        dataset.asymmetries = {
            "a1": objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                    uncertainty=range(27648), time=range(27648))
        }
        dataset.meta = {
            "m1": "someting",
            "m2": 2
        }
        dataset.histograms_used = ["h1", "h2"]

        dataset_minimized = dataset.get_persistent_data()
        dataset_maximized = dataset.build_from_persistent_data(dataset_minimized)

        assert dataset_maximized.equals(dataset)

    def test_persistent_with_pickling(self):
        dataset = objects.RunDataset()
        dataset.histograms = {
            "h1": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
            "h2": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)
        }
        dataset.asymmetries = {
            "a1": objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                    uncertainty=range(27648), time=range(27648))
        }
        dataset.meta = {
            "m1": "someting",
            "m2": 2
        }
        dataset.histograms_used = ["h1", "h2"]

        dataset_minimized = dataset.get_persistent_data()
        dataset_minimized_unpickled = pickle.loads(pickle.dumps(dataset_minimized))
        dataset_maximized = dataset.build_from_persistent_data(dataset_minimized_unpickled)

        assert dataset_maximized.equals(dataset)
        
        
class TestFileDatasets:
    def test_pickling(self):
        dataset = objects.RunDataset()
        dataset.histograms = {
            "h1": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
            "h2": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)
        }
        dataset.asymmetries = {
            "a1": objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                    uncertainty=range(27648), time=range(27648))
        }
        dataset.meta = {
            "m1": "someting",
            "m2": 2
        }
        dataset.histograms_used = ["h1", "h2"]

        from app.model import files
        file_dataset = objects.FileDataset(files.file(resources.resource_path(r"test/examples/histogram_data_1.dat")))
        file_dataset.dataset = dataset

        file_dataset_unpickled = pickle.loads(pickle.dumps(file_dataset))
        assert file_dataset_unpickled.equals(file_dataset)
    
    def test_persistent_object(self):
        dataset = objects.RunDataset()
        dataset.histograms = {
            "h1": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
            "h2": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)
        }
        dataset.asymmetries = {
            "a1": objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                    uncertainty=range(27648), time=range(27648))
        }
        dataset.meta = {
            "m1": "someting",
            "m2": 2
        }
        dataset.histograms_used = ["h1", "h2"]

        from app.model import files
        file_dataset = objects.FileDataset(files.file(resources.resource_path(r"test/examples/histogram_data_1.dat")))
        file_dataset.dataset = dataset

        file_dataset_minimized = file_dataset.get_persistent_data()
        file_dataset_maximized = file_dataset.build_from_persistent_data(file_dataset_minimized)

        file_dataset_maximized.dataset = dataset  # cheating a little
        assert file_dataset_maximized.equals(file_dataset)

    def test_persistent_with_pickling(self):
        dataset = objects.RunDataset()
        dataset.histograms = {
            "h1": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
            "h2": objects.Histogram(range(27648), 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)
        }
        dataset.asymmetries = {
            "a1": objects.Asymmetry(input_array=range(27648), time_zero=980, bin_size=0.2,
                                    uncertainty=range(27648), time=range(27648))
        }
        dataset.meta = {
            "m1": "someting",
            "m2": 2
        }
        dataset.histograms_used = ["h1", "h2"]

        from app.model import files
        file_dataset = objects.FileDataset(files.file(resources.resource_path(r"test/examples/histogram_data_1.dat")))
        file_dataset.dataset = dataset

        file_dataset_minimized = file_dataset.get_persistent_data()
        file_dataset_minimized_unpickled = pickle.loads(pickle.dumps(file_dataset_minimized))
        file_dataset_maximized = file_dataset.build_from_persistent_data(file_dataset_minimized_unpickled)

        file_dataset_maximized.dataset = dataset  # cheating a little
        assert file_dataset_maximized.equals(file_dataset)
