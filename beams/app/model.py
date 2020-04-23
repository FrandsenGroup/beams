
from util import muon, files


class MuonDataContext:
    """
    A model object that acts purely as data storage and access object.
    """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.notifier = Notifier()
            self.runs = []

    __instance = None

    def __init__(self):
        if not MuonDataContext.__instance:
            MuonDataContext.__instance = MuonDataContext.__DataStore()

    def get_run_by_filename(self, filename):
        """
        Gets a Run object associated with the given filename.
        :param filename: full file path associated with a run
        :return run:
        """
        for run in self.__instance.runs:
            if run.file == filename:
                return run

    def remove_runs_by_filename(self, filenames, stop_signal=None):
        """
        Removes a Run object associated with the given filename.
        :param filenames: array of full file paths associated with a run
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        for filename in filenames:
            for run in self.__instance.runs:
                if run.file == filename:
                    self.__instance.runs.remove(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_run_by_id(self, run_id):
        """
        Gets a Run object with the specified ID.
        :param run_id: ID of a run
        :return run:
        """
        for run in self.__instance.runs:
            if run.file == run_id:
                return run

    def remove_runs_by_id(self, run_ids, stop_signal=None):
        """
        Removes a Run object with the specified ID
        :param run_ids: array of IDs of runs
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        for run_id in run_ids:
            for run in self.__instance.runs:
                if run.file == run_id:
                    self.__instance.runs.remove(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_run(self, run, stop_signal=None):
        """
        Adds a Run object to the data store.
        :param run:
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        self.__instance.runs.append(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_runs(self, runs, stop_signal=None):
        """
        Adds an array of run objects to the data store.
        :param runs: array of runs
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        self.__instance.runs.extend(runs)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_run_from_histogram_file(self, histogram_file, histograms, stop_signal=None):

        # for param in run_params:
        #     run = muon.build_muon_run_from_histogram_file(param[0], param[1], param[2])
        #     self.__instance.runs.append(run)

        if not stop_signal:
            self.__instance.notifier.notify()

    def add_run_from_asymmetry_file(self, asymmetry_file, stop_signal=None):

        if not stop_signal:
            self.__instance.notifier.notify()

    def clear_runs(self, stop_signal=None):
        """
        Clears all runs in the data store.
        :param stop_signal: optional parameter to prevent sending update signal to presenters
        """
        self.__instance.runs = []

        if not stop_signal:
            self.__instance.notifier.notify()

    @staticmethod
    def subscribe(observer):
        MuonDataContext.__instance.notifier.subscribe(observer)


class FileContext:
    """
        A model object that acts purely as data storage and access object.
        """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.notifier = Notifier()
            self.files = set()

    __instance = None

    def __init__(self):
        if FileContext.__instance is None:
            FileContext.__instance = FileContext.__DataStore()

    def add_files(self, files, stop_signal=None):
        self.__instance.files.update(files)

        if not stop_signal:
            self.__instance.notifier.notify()

    def remove_files(self, files, stop_signal=None):
        self.__instance.files.difference_update(files)

        if not stop_signal:
            self.__instance.notifier.notify()

    def get_files(self):
        return self.__instance.files

    @staticmethod
    def subscribe(observer):
        FileContext.__instance.notifier.subscribe(observer)


class Notifier:
    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def notify(self):
        for observer in self.observers:
            observer.update()
