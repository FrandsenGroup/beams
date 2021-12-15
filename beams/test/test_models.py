import pytest
import pickle
import numpy as np

from app.model import objects


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

    @pytest.mark.skip
    def test_combine(self):
        pass


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


class UncertaintyTests:
    pass
