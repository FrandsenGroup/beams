import pytest

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
                             # Histograms with different time zeroes.
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 1000, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 979, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)),

                              # Histograms with different good bin starts.
                              (objects.Histogram(range(27648),
                                                 980, -5, 27648, 70, 900, "Front", "RANDOM_ID", 0.2),
                               objects.Histogram(range(27648),
                                                 980, 1030, 27648, 70, 900, "Back", "RANDOM_ID", 0.2)),

                              # Histograms with different good bin starts.
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
                             [(objects.Histogram(range(27648),
                                                 980, 1030, 27648, -5, 900, "Front", "RANDOM_ID", 0.2)),
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 1200, 900, "Front", "RANDOM_ID", 0.2)),
                              (objects.Histogram(range(27648),
                                                 980, 1030, 27648, 700, 70000, "Front", "RANDOM_ID", 0.2)),
                              ])
    def test_background_radiation_raise_exception(self, hist: objects.Histogram):
        with pytest.raises(ValueError):
            hist.background_radiation()

    @pytest.mark.skip
    def test_combine(self):
        pass


class AsymmetryTests:
    pass


class UncertaintyTests:
    pass
