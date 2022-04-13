import pytest

from app.model import files
from app.resources import resources


class TestHelpers:
    @pytest.mark.parametrize("filename, is_found",
                             [
                                 (resources.resource_path(r"test/examples/histogram_data_0.dat"), True),
                                 ("this_file_does_not_exist.lol", False)
                             ])
    def test_is_found(self, filename, is_found):
        assert files.is_found(filename) == is_found

    @pytest.mark.parametrize("filename, check_ext, expected_result",
                             [
                                 ("a_file.dat", ".dat", True),
                                 ("a_file.fit", ".dat", False),
                                 ("a_file.dat", "dat", True)
                             ])
    def test_check_ext(self, filename, check_ext, expected_result):
        assert files.check_ext(filename, check_ext) == expected_result

    @pytest.mark.parametrize("filename, is_beams",
                             [
                                 (resources.resource_path(r"test/examples/is_beams_test_1.txt"), True),
                                 (resources.resource_path(r"test/examples/is_beams_test_2.txt"), True),
                                 (resources.resource_path(r"test/examples/is_beams_test_3.txt"), False)
                             ])
    def test_is_beams(self, filename, is_beams):
        assert files.is_beams(filename) == is_beams

    @pytest.mark.parametrize("filename, data_row, d_type, titles, title_row, expected_data",
                             [
                                 (resources.resource_path(r"test/examples/columnated_data_test_1.dat"),
                                  4, float, None, 3, {"title_a": [1, 3, 5, 7], "title_b": [2, 4, 6, 8]}),
                                 (resources.resource_path(r"test/examples/columnated_data_test_2.dat"),
                                  1, float, ['title_a', 'title_b'], None, {"title_a": [1, 3, 5, 7], "title_b": [2, 4, 6, 8]}),
                                 (resources.resource_path(r"test/examples/columnated_data_test_3.dat"),
                                  2, float, None, None, [[1, 2, 3, 4, 5], [4, 3, 2, 4, 5], [1, 2, 4, 5, 6]])
                             ])
    def test_read_columnated_data(self, filename, data_row, d_type, titles, title_row, expected_data):
        data = files.read_columnated_data(filename, data_row, d_type, titles, title_row)

        if isinstance(expected_data, dict):
            for expected_column_title, expected_column_data in expected_data.items():
                assert all(data[expected_column_title] == expected_column_data)
        else:
            for expected_row, read_row in zip(expected_data, data):
                assert all(expected_row == read_row)


class TestTriumfMuonFile:
    # I would encourage you strongly to add to this test as new .msr files come out and you find them failing to ensure
    # we maintain support across the board for these files.
    @pytest.mark.parametrize("filename, out_file, expected_out_file",
                             [
                                 (resources.resource_path(r"test/examples/triumf_convert_test_1.msr"),
                                  resources.resource_path(r"test/examples/_triumf_convert_test_1.dat"),
                                  resources.resource_path(r"test/examples/triumf_convert_test_1.dat"))
                             ])
    def test_convert_on_good_file(self, filename, out_file, expected_out_file):
        msr_file = files.file(filename)
        msr_file.convert(out_file)

        with open(out_file, 'rb') as of:
            with open(expected_out_file, 'rb') as expected_of:
                assert of.read() == expected_of.read()

    def test_convert_on_bad_file(self):
        msr_file = files.file(resources.resource_path(r"test/examples/triumf_convert_test_2.msr"))
        with pytest.raises(files.BeamsFileConversionError):
            msr_file.convert(resources.resource_path(r"test/examples/_triumf_convert_test_2.dat"))




