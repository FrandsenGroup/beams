import pytest
import pickle

from app.model import data_access, objects, files
from app.resources import resources


@pytest.fixture
def database_with_styles():
    s1, s2, s3 = {}, {}, {}
    db = data_access.Database()
    db.style_table = {"1": s1, "2": s2, "3": s3}
    return db


@pytest.fixture
def database_with_runs():
    r1, r2, r3 = objects.RunDataset(), objects.RunDataset(), objects.RunDataset()
    r1.id = "1"
    r2.id = "2"
    r3.id = "3"
    r1.meta = {files.RUN_NUMBER_KEY: "run1"}
    r2.meta = {files.RUN_NUMBER_KEY: "run2"}
    r3.meta = {files.RUN_NUMBER_KEY: "run3"}
    db = data_access.Database()
    db.run_table = {r1.id: r1, r2.id: r2, r3.id: r3}
    return db


@pytest.fixture
def database_with_files(database_with_runs):
    f1, f2, f3 = (objects.FileDataset(files.file(resources.resource_path(rf"test/examples/histogram_data_{i}.dat")))
                  for i in range(3))
    f1.id = "1"
    f1.dataset = database_with_runs.run_table["1"]
    f2.id = "2"
    f2.dataset = database_with_runs.run_table["2"]
    f3.id = "3"
    f3.dataset = database_with_runs.run_table["3"]
    database_with_runs.file_table = {f1.id: f1, f2.id: f2, f3.id: f3}
    return database_with_runs


@pytest.fixture
def database_with_fits():
    f1, f2, f3 = objects.FitDataset(), objects.FitDataset(), objects.FitDataset()
    f1.id = "1"
    f2.id = "2"
    f3.id = "3"
    db = data_access.Database()
    db.fit_table = {f1.id: f1, f2.id: f2, f3.id: f3}
    return db


class TestRunDao:
    def test_get_runs(self, database_with_runs):
        dao = data_access.RunDAO()

        runs = dao.get_runs()
        assert len(runs) == 3

    def test_get_runs_by_ids(self, database_with_runs):
        dao = data_access.RunDAO()

        runs = dao.get_runs_by_ids(["1", "2"])
        assert len(runs) == 2
        assert runs[0].id in ["1", "2"]
        assert runs[1].id in ["1", "2"]

    def test_get_runs_by_numbers(self, database_with_runs):
        dao = data_access.RunDAO()

        runs = list(dao.get_runs_by_numbers(["run2", "run3"]).values())
        assert len(runs) == 2
        assert runs[0].meta[files.RUN_NUMBER_KEY] in ["run2", "run3"]
        assert runs[1].meta[files.RUN_NUMBER_KEY] in ["run2", "run3"]

    def test_add_runs(self, database_with_runs):
        dao = data_access.RunDAO()

        dao.add_runs([objects.RunDataset()])
        assert len(database_with_runs.run_table) == 4

    def test_remove_runs_by_ids(self, database_with_runs):
        dao = data_access.RunDAO()

        dao.remove_runs_by_ids(["1", "2"])
        assert len(database_with_runs.run_table) == 1
        assert "3" in database_with_runs.run_table

    def test_update_runs_by_id(self, database_with_runs):
        dao = data_access.RunDAO()

        new_run = objects.RunDataset()
        dao.update_runs_by_id(["1"], [new_run])
        assert len(database_with_runs.run_table) == 3
        assert database_with_runs.run_table["1"] == new_run

    def test_clear(self, database_with_runs):
        dao = data_access.RunDAO()

        dao.clear()
        assert len(database_with_runs.run_table) == 0

    def test_persist(self, database_with_runs):
        original_run_table = database_with_runs.run_table.copy()
        dao = data_access.RunDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_runs.run_table) == 0

        dao.maximize(minimal)
        assert database_with_runs.run_table == original_run_table

    def test_persist_with_pickle(self, database_with_runs):
        original_run_table = database_with_runs.run_table.copy()
        dao = data_access.RunDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_runs.run_table) == 0

        minimal_pickled = pickle.dumps(minimal)
        minimal_unpickled = pickle.loads(minimal_pickled)
        assert minimal == minimal_unpickled

        dao.maximize(minimal_unpickled)
        assert database_with_runs.run_table == original_run_table


class TestFileDao:
    def test_get_files(self, database_with_files):
        dao = data_access.FileDAO()

        file_datasets = dao.get_files()
        assert len(file_datasets) == 3

    def test_get_files_by_ids(self, database_with_files):
        dao = data_access.FileDAO()

        file_datasets = dao.get_files_by_ids(["1", "3"])
        assert len(file_datasets) == 2
        assert file_datasets[0].id in ["1", "3"]
        assert file_datasets[1].id in ["1", "3"]
        assert file_datasets[0].id != file_datasets[1].id

    def test_get_files_by_path(self, database_with_files):
        dao = data_access.FileDAO()

        file_dataset = dao.get_files_by_path(resources.resource_path(r"test/examples/histogram_data_1.dat"))
        assert file_dataset is not None
        assert file_dataset.id == "2"

    def test_add_files(self, database_with_files):
        dao = data_access.FileDAO()

        dao.add_files([(objects.FileDataset(files.UnknownFile(file_path="test.txt")))])
        assert len(database_with_files.file_table) == 4

    def test_remove_files_by_paths(self, database_with_files):
        dao = data_access.FileDAO()

        files_removed = dao.remove_files_by_paths([resources.resource_path(r"test/examples/histogram_data_1.dat"),
                                                   resources.resource_path(r"test/examples/histogram_data_0.dat")])
        assert files_removed == 2
        assert len(database_with_files.file_table) == 1
        assert "3" in database_with_files.file_table

    def test_remove_files_by_id(self, database_with_files):
        dao = data_access.FileDAO()

        dao.remove_files_by_id(["1", "3"])
        assert len(database_with_files.file_table) == 1
        assert "2" in database_with_files.file_table

        dao.remove_files_by_id("2")
        assert len(database_with_files.file_table) == 0

    def test_clear(self, database_with_files):
        dao = data_access.FileDAO()

        dao.clear()
        assert len(database_with_files.file_table) == 0

    def test_persist(self, database_with_files):
        original_file_table = database_with_files.file_table.copy()
        dao = data_access.FileDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_files.file_table) == 0

        dao.maximize(minimal)
        assert database_with_files.file_table == original_file_table

    def test_persist_with_pickle(self, database_with_files):
        original_file_table = database_with_files.file_table.copy()
        dao = data_access.FileDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_files.file_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.maximize(minimal)
        assert database_with_files.file_table == original_file_table


class TestFitDao:
    def test_get_fits(self, database_with_fits):
        dao = data_access.FitDAO()

        fits = dao.get_fits()
        assert len(fits) == 3

    def test_get_fits_by_ids(self, database_with_fits):
        dao = data_access.FitDAO()

        get_ids = ["1", "3"]
        fits = dao.get_fits_by_ids(get_ids)
        assert len(fits) == 2
        assert fits[0].id in get_ids
        assert fits[1].id in get_ids

    def test_add_fits(self, database_with_fits):
        dao = data_access.FitDAO()

        dao.add_fits([objects.FitDataset()])
        assert len(database_with_fits.fit_table) == 4

    def test_remove_fits_by_ids(self, database_with_fits):
        dao = data_access.FitDAO()

        dao.remove_fits_by_ids(["1", "3"])
        assert len(database_with_fits.fit_table) == 1

        dao.remove_fits_by_ids("2")
        assert len(database_with_fits.fit_table) == 0

    def test_clear(self, database_with_fits):
        dao = data_access.FitDAO()

        dao.clear()
        assert len(database_with_fits.fit_table) == 0

    def test_minimize(self, database_with_fits):
        original_fit_table = database_with_fits.fit_table.copy()
        dao = data_access.FitDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_fits.fit_table) == 0

        dao.maximize(minimal)
        assert database_with_fits.fit_table == original_fit_table

    def test_maximize(self, database_with_fits):
        original_fit_table = database_with_fits.fit_table.copy()
        dao = data_access.FitDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_fits.fit_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.maximize(minimal_unpickled)
        assert database_with_fits.fit_table == original_fit_table


class TestStyleDao:
    def test_add_style(self, database_with_styles):
        dao = data_access.StyleDAO()

        dao.add_style("4", {})
        assert len(database_with_styles.style_table) == 4

    def test_get_styles(self, database_with_styles):
        dao = data_access.StyleDAO()

        styles = dao.get_styles()
        assert styles == database_with_styles.style_table

        styles = dao.get_styles(["1", "2"])
        assert len(styles) == 2

        styles = dao.get_styles("1")
        assert len(styles) == 1

    def test_update_style(self, database_with_styles):
        dao = data_access.StyleDAO()

        dao.update_style("1", "akey", "avalue")
        assert database_with_styles.style_table["1"]["akey"] == "avalue"

        dao.update_style("1", "akey", "bvalue")
        assert database_with_styles.style_table["1"]["akey"] == "bvalue"

    def test_clear(self, database_with_styles):
        dao = data_access.StyleDAO()

        dao.clear()
        assert len(database_with_styles.style_table) == 0

    def test_minimize(self, database_with_styles):
        original_style_table = database_with_styles.style_table.copy()
        dao = data_access.StyleDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_styles.style_table) == 0

        dao.maximize(minimal)
        assert database_with_styles.style_table == original_style_table

    def test_maximize(self, database_with_styles):
        original_style_table = database_with_styles.style_table.copy()
        dao = data_access.StyleDAO()

        minimal = dao.minimize()
        dao.clear()
        assert len(database_with_styles.style_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.maximize(minimal_unpickled)
        assert database_with_styles.style_table == original_style_table


class TestSystemDao:
    def test_set_configuration(self):
        db = data_access.Database()
        dao = data_access.SystemDAO()

        dao.set_configuration("config1", "setting1")
        assert db.system_table["config1"] == "setting1"

        dao.set_configuration("config1", "setting2")
        assert db.system_table["config1"] == "setting2"

        dao.set_configuration("config2", "setting1")
        assert len(db.system_table) == 2

    def test_get_configuration(self):
        db = data_access.Database()
        db.system_table = {
            "config1": "setting1",
            "config2": {
                "config3": "setting3"
            }
        }
        dao = data_access.SystemDAO()

        setting = dao.get_configuration("config1")
        assert setting == "setting1"

        setting = dao.get_configuration("config3")
        assert setting == "setting3"

        # Haven't handled duplicate config names nested under different configs. Honestly not going to be used.

    def test_minimize(self, database_with_styles, database_with_runs, database_with_fits, database_with_files):
        db = data_access.Database()
        original_run_table = db.run_table.copy()
        original_file_table = db.file_table.copy()
        original_fit_table = db.fit_table.copy()
        original_style_table = db.style_table.copy()
        dao = data_access.SystemDAO()

        minimal = dao.get_database()
        data_access.RunDAO().clear()
        data_access.FileDAO().clear()
        data_access.FitDAO().clear()
        data_access.StyleDAO().clear()
        assert len(db.run_table) == 0
        assert len(db.file_table) == 0
        assert len(db.fit_table) == 0
        assert len(db.style_table) == 0

        dao.set_database(minimal)
        assert db.run_table == original_run_table
        assert db.style_table == original_style_table
        assert db.file_table == original_file_table
        assert db.fit_table == original_fit_table

    def test_minimize_with_pickle(self, database_with_styles, database_with_runs, database_with_fits, database_with_files):
        db = data_access.Database()
        original_run_table = db.run_table.copy()
        original_file_table = db.file_table.copy()
        original_fit_table = db.fit_table.copy()
        original_style_table = db.style_table.copy()
        dao = data_access.SystemDAO()

        minimal = dao.get_database()
        data_access.RunDAO().clear()
        data_access.FileDAO().clear()
        data_access.FitDAO().clear()
        data_access.StyleDAO().clear()
        assert len(db.run_table) == 0
        assert len(db.file_table) == 0
        assert len(db.fit_table) == 0
        assert len(db.style_table) == 0

        minimal_unpickled = pickle.loads(pickle.dumps(minimal))
        assert minimal_unpickled == minimal

        dao.set_database(minimal_unpickled)
        assert db.run_table == original_run_table
        assert db.style_table == original_style_table
        assert db.file_table == original_file_table
        assert db.fit_table == original_fit_table

