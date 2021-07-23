
class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.run_table = {}
            cls._instance.fit_table = {}
            cls._instance.file_table = {}
            cls._instance.style_table = {}
            cls._instance.system_table = {}
        return cls._instance


class RunDAO:
    __database = Database()

    def get_runs(self):
        return self.__database.run_table.values()

    def get_runs_by_ids(self, ids):
        return [self.__database.run_table[rid] for rid in ids]

    def add_runs(self, runs):
        for run in runs:
            self.__database.run_table[run.id] = run

    def remove_runs_by_ids(self, ids):
        for rid in ids:
            self.__database.run_table.pop(rid)

    def update_runs_by_id(self, ids, runs):
        for rid, run in zip(ids, runs):
            self.__database.run_table[rid] = run

    def clear(self):
        self.__database.run_table = {}


class FitDAO:
    __database = Database()

    def get_fits(self):
        return self.__database.fit_table.values()

    def get_fits_by_ids(self, ids):
        return [self.__database.fit_table[fid] for fid in ids]

    def add_fits(self, fits):
        for fit in fits:
            self.__database.fit_table[fit.id] = fit

    def remove_runs_by_ids(self, ids):
        for fid in ids:
            self.__database.fit_table.pop(fid)

    def clear(self):
        self.__database.fit_table = {}


class FileDAO:
    __database = Database()

    def get_files(self):
        return self.__database.file_table.values()

    def get_files_by_ids(self, ids):
        return [self.__database.file_table[file_id] for file_id in ids]

    def get_files_by_path(self, path):
        for file in self.__database.file_table.values():
            if file.file_path == path:
                return file

    def add_files(self, file_datasets):
        for dataset in file_datasets:
            self.__database.file_table[dataset.id] = dataset

    def remove_files_by_paths(self, paths):
        for path in paths:
            self.__database.file_table.pop(path)

    def remove_files_by_id(self, fid):
        self.__database.file_table.pop(fid)

    def clear(self):
        self.__database.file_table = {}


class StyleDAO:
    __database = Database()


class SystemDAO:
    __database = Database()

