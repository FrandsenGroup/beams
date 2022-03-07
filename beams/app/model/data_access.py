"""
Acts as the main data storage for the application and abstracts away data-access operations.
"""


class Database:
    """
    Our database as currently constituted is just a singleton with a bunch of dictionaries acting as tables. Any data
    we want to persist when a session is saved and reloaded is stored here.
    """
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
    """
    Handles all data access operations related to RunDatasets.
    """
    __database = Database()

    def get_runs(self):
        return self.__database.run_table.values()

    def get_runs_by_ids(self, ids):
        return [self.__database.run_table[rid] for rid in ids]

    def get_runs_by_numbers(self, numbers):
        return {run.meta['RunNumber']: run for run in self.__database.run_table.values() if run.meta['RunNumber'] in numbers}

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

    def minimize(self):
        return {run_id: run.get_persistent_data() for run_id, run in self.__database.run_table.items()}

    def maximize(self, data):
        from app.model import objects
        self.__database.run_table = {
            run_id: objects.RunDataset.build_from_persistent_data(run) for run_id, run in data.items()
        }


class FitDAO:
    """
    Handles all data access operations related to FitDatasets.
    """
    __database = Database()

    def get_fits(self):
        return self.__database.fit_table.values()

    def get_fits_by_ids(self, ids):
        return [self.__database.fit_table[fid] for fid in ids]

    def add_fits(self, fits):
        for fit in fits:
            self.__database.fit_table[fit.id] = fit

    def remove_fits_by_ids(self, ids):
        for fid in ids:
            self.__database.fit_table.pop(fid)

    def clear(self):
        self.__database.fit_table = {}

    def minimize(self):
        return {fit_id: fit.get_persistent_data() for fit_id, fit in self.__database.fit_table.items()}

    def maximize(self, data):
        self.__database.fit_table = {fit_id: fit.build_from_persistent_data() for fit_id, fit in data}


class FileDAO:
    """
    Handles all data access operations related to File objects.
    """
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
    """
    Handles all data access operations related to Styles. Since we want common styles to be used between the panels
    and persist if a session is saved and reloaded, it is easiest to store them here.
    """
    __database = Database()

    def add_style(self, identifier, style):
        self.__database.style_table[identifier] = style

    def get_styles(self, identifiers=None):
        if identifiers is not None:
            return [self.__database.style_table[i] for i in identifiers]
        else:
            return self.__database.style_table

    def update_style(self, identifier, key, value):
        self.__database.style_table[identifier][key] = value


class SystemDAO:
    """
    Handles all data access operations related to the application configuration. These are loaded in from
    resources.CONFIG_FILE.
    """
    __database = Database()

    def set_configuration(self, key, value):
        self.__database.system_table[key] = value

    def get_configuration(self, key=None):
        if key:
            value = self._recursive_search(self.__database.system_table, key)

            if value is not None:
                return value
            else:
                raise BeamsRequestedDataNotInDatabaseError("Config value not in the configuration.")
        else:
            return self.__database.system_table

    def set_database(self, database: Database):
        self.__database._instance = database

    def get_database(self):
        return self.__database

    def _recursive_search(self, dictionary, key):
        for k, v in dictionary.items():
            if k == key:
                return dictionary[k]

            elif isinstance(v, dict):
                value = self._recursive_search(v, key)

                if value:
                    return value

        return None


class BeamsRequestedDataNotInDatabaseError(Exception):
    def __init__(self, *args, **kwargs):
        super(BeamsRequestedDataNotInDatabaseError, self).__init__(args, kwargs)