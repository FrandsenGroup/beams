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
            if key in self.__database.system_table.keys():
                return self.__database.system_table[key]
            else:
                return None
        else:
            return self.__database.system_table

    def set_database(self, database: Database):
        # TODO we are going to want to update the file table, not all file datasets will be loaded now...
        #   maybe we do want to just replace the whole session actually.
        # file_table = self.__database.file_table
        self.__database._instance = database
        # self.__database.file_table = file_table
