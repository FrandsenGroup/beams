import pytest
import pickle

from app.model import data_access, objects, files


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
        pass

    def test_get_files_by_ids(self):
        pass

    def test_get_files_by_path(self):
        pass

    def test_add_files(self):
        pass

    def test_remove_files_by_paths(self):
        pass

    def test_remove_files_by_id(self):
        pass

    def test_clear(self):
        pass

    def test_persist(self):
        pass

    def test_persist_with_pickle(self):
        pass
