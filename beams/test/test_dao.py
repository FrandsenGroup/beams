import pytest
import pickle

from app.model import data_access, objects, files
from resources import resources


@pytest.mark.RunDao
class TestRunDao:
    def test_get_runs(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        runs = dao.get_runs()

        assert r1 in runs and r2 in runs and r3 in runs
        assert len(runs) == 3

    def test_get_runs_by_ids(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        runs = dao.get_runs_by_ids([r1.id, r2.id])

        assert r1 in runs and r2 in runs
        assert r3 not in runs
        assert len(runs) == 2

    def test_get_runs_by_numbers(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        r1.meta = {files.RUN_NUMBER_KEY: "1"}
        r2.meta = {files.RUN_NUMBER_KEY: "2"}
        r3.meta = {files.RUN_NUMBER_KEY: "3"}
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        runs = dao.get_runs_by_numbers(["2", "3"]).values()

        assert r2 in runs and r3 in runs
        assert r1 not in runs
        assert len(runs) == 2

    def test_add_runs(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        dao.add_runs([objects.RunDataset()])

        assert len(db.run_table) == 4

    def test_remove_runs_by_ids(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        dao.remove_runs_by_ids([r2.id, r3.id])

        assert len(db.run_table) == 1
        assert r1.id in db.run_table

    def test_update_runs_by_id(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        dao.update_runs_by_id([r1.id], [r2])

        assert len(db.run_table) == 3
        assert db.run_table[r1.id] == r2

    def test_clear(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        dao.clear()

        assert len(db.run_table) == 0

    def test_persist(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        original_run_table = {r1.id: r1, r2.id: r2, r3.id: r3}
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.run_table) == 0

        dao.maximize(minimal)
        assert db.run_table == original_run_table

    def test_persist_with_pickle(self):
        r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
        db = data_access.Database()
        original_run_table = {r1.id: r1, r2.id: r2, r3.id: r3}
        db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}

        dao = data_access.RunDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.run_table) == 0

        minimal_pickled = pickle.dumps(minimal)
        minimal_unpickled = pickle.loads(minimal_pickled)
        assert minimal == minimal_unpickled

        dao.maximize(minimal_unpickled)
        assert db.run_table == original_run_table


@pytest.mark.FileDao
class TestFileDao:
    def test_get_files(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FileDAO()

        file_datasets = dao.get_files()

        assert f1 in file_datasets and f2 in file_datasets and f3 in file_datasets
        assert len(file_datasets) == 3

    def test_get_files_by_ids(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FileDAO()

        file_datasets = dao.get_files_by_ids([f1.id, f3.id])

        assert f1 in file_datasets and f3 in file_datasets
        assert f2 not in file_datasets
        assert len(file_datasets) == 2

    def test_get_files_by_path(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FileDAO()

        file_datasets = dao.get_files_by_path(resources.resource_path(r"test/examples/histogram_data_1.dat"))

        assert f2 == file_datasets

    def test_add_files(self):
        f1, f2 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(2))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2}

        dao = data_access.FileDAO()

        dao.add_files([(objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_2.dat"))))])

        assert len(db.file_table) == 3

    def test_remove_files_by_paths(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FileDAO()

        files_removed = dao.remove_files_by_paths([resources.resource_path(r"test/examples/histogram_data_1.dat"),
                                   resources.resource_path(r"test/examples/histogram_data_0.dat")])

        assert files_removed == 2
        assert len(db.file_table) == 1
        assert f3.id in db.file_table

    def test_remove_files_by_id(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FileDAO()

        dao.remove_files_by_id([f1.id, f3.id])

        assert len(db.file_table) == 1
        assert f2.id in db.file_table

        dao.remove_files_by_id(f2.id)

        assert len(db.file_table) == 0

    def test_clear(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        db.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FileDAO()

        dao.clear()

        assert len(db.file_table) == 0

    def test_persist(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        original_file_table = {f1.id: f1, f2.id: f2, f3.id: f3}
        db.file_table = original_file_table

        dao = data_access.FileDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.file_table) == 0

        dao.maximize(minimal)
        assert db.file_table == original_file_table

    def test_persist_with_pickle(self):
        f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                      for i in range(3))
        db = data_access.Database()
        original_file_table = {f1.id: f1, f2.id: f2, f3.id: f3}
        db.file_table = original_file_table

        dao = data_access.FileDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.file_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.maximize(minimal)
        assert db.file_table == original_file_table


@pytest.mark.FitDao
class TestFitDao:
    def test_get_fits(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        db.fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FitDAO()

        fits = dao.get_fits()
        assert f1 in fits and f2 in fits and f3 in fits
        assert len(fits) == 3

    def test_get_fits_by_ids(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        db.fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FitDAO()

        fits = dao.get_fits_by_ids([f1.id, f2.id])
        assert f1 in fits and f2 in fits
        assert f3 not in fits
        assert len(fits) == 2

    def test_add_fits(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        db.fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FitDAO()

        dao.add_fits([objects.FitDataset()])
        assert len(db.fit_table) == 4

    def test_remove_fits_by_ids(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        db.fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FitDAO()

        dao.remove_fits_by_ids([f1.id, f3.id])
        assert len(db.fit_table) == 1

        dao.remove_fits_by_ids(f2.id)
        assert len(db.fit_table) == 0

    def test_clear(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        db.fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}

        dao = data_access.FitDAO()

        dao.clear()
        assert len(db.fit_table) == 0

    def test_minimize(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        original_fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}
        db.fit_table = original_fit_table

        dao = data_access.FitDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.fit_table) == 0

        dao.maximize(minimal)
        assert db.fit_table == original_fit_table

    def test_maximize(self):
        f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
        db = data_access.Database()
        original_fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}
        db.fit_table = original_fit_table

        dao = data_access.FitDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.fit_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.maximize(minimal_unpickled)
        assert db.fit_table == original_fit_table


@pytest.mark.StyleDao
class TestStyleDao:
    def test_add_style(self):
        s1, s2, s3 = {}, {}, {}
        db = data_access.Database()
        db.style_table = {"1": s1, "2": s2, "3": s3}

        dao = data_access.StyleDAO()

        dao.add_style("4", {})
        assert len(db.style_table) == 4

    def test_get_styles(self):
        s1, s2, s3 = {}, {}, {}
        db = data_access.Database()
        db.style_table = {"1": s1, "2": s2, "3": s3}

        dao = data_access.StyleDAO()

        styles = dao.get_styles()
        assert styles == db.style_table

        styles = dao.get_styles(["1", "2"])
        assert len(styles) == 2

        styles = dao.get_styles("1")
        assert len(styles) == 1

    def test_update_style(self):
        s1, s2, s3 = {}, {}, {}
        db = data_access.Database()
        db.style_table = {"1": s1, "2": s2, "3": s3}

        dao = data_access.StyleDAO()

        dao.update_style("1", "akey", "avalue")
        assert db.style_table["1"]["akey"] == "avalue"

        dao.update_style("1", "akey", "bvalue")
        assert db.style_table["1"]["akey"] == "bvalue"

    def test_clear(self):
        s1, s2, s3 = {}, {}, {}
        db = data_access.Database()
        db.style_table = {"1": s1, "2": s2, "3": s3}

        dao = data_access.StyleDAO()

        dao.clear()
        assert len(db.style_table) == 0

    def test_minimize(self):
        s1, s2, s3 = {}, {}, {}
        db = data_access.Database()
        original_style_table = {"1": s1, "2": s2, "3": s3}
        db.style_table = original_style_table

        dao = data_access.StyleDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.style_table) == 0

        dao.maximize(minimal)
        assert db.style_table == original_style_table

    def test_maximize(self):
        s1, s2, s3 = {}, {}, {}
        db = data_access.Database()
        original_style_table = {"1": s1, "2": s2, "3": s3}
        db.style_table = original_style_table

        dao = data_access.StyleDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(db.style_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.maximize(minimal_unpickled)
        assert db.style_table == original_style_table
