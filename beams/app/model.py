
class RunService:
    """
    Handles requests for data operations on runs sent by Presenter classes. Notifies observers based on data changes.
    """

    class __Observers:
        """
        Persistent object to store observers (rather then make the whole RunService object a singleton).
        """
        def __init__(self):
            self.currentObservers = {RunService.CURRENT_RUNS_CHANGED: []}

    __observers = None

    CURRENT_RUNS_CHANGED = 0

    def __init__(self):
        if not RunService.__observers:
            RunService.__observers = RunService.__Observers()

        self.dao = RunDAO()

    def register(self, observer, signal):
        """
        A class with a "update()" method may register itself as an observer of one of the RunService signals.
        :param observer: object to be stored as an observer
        :param signal: signal the observer is interested in
        """
        self.__observers.currentObservers[signal].append(observer)

    def _notify(self, signal):
        """
        Notifies all observers of the specified signal by calling their 'update()' methods.
        :param signal: signal that has been triggered
        """
        for observer in self.__observers.currentObservers[signal]:
            observer.update()


class RunDAO:
    """
    Handles simple data access operations for runs stored by the program.
    """
    def __init__(self):
        self._data_store = DataStore()

    def get_run_by_filename(self, filename):
        """
        Gets a Run object associated with the given filename.
        :param filename: full file path associated with a run
        :return run:
        """
        for run in self._data_store.runs:
            if run.file == filename:
                return run

    def remove_run_by_filename(self, filename):
        """
        Removes a Run object associated with the given filename.
        :param filename: full file path associated with a run
        """
        for run in self._data_store.runs:
            if run.file == filename:
                self._data_store.runs.remove(run)

    def get_run_by_id(self, run_id):
        """
        Gets a Run object with the specified ID.
        :param run_id: ID of a run
        :return run:
        """
        for run in self._data_store.runs:
            if run.file == run_id:
                return run

    def remove_run_by_id(self, run_id):
        """
        Removes a Run object with the specified ID
        :param run_id: ID of a run
        """
        for run in self._data_store.runs:
            if run.file == run_id:
                self._data_store.runs.remove(run)

    def add_run(self, run):
        """
        Adds a Run object to the data store.
        :param run:
        """
        self._data_store.runs.append(run)

    def clear_runs(self):
        """
        Clears all runs in the data store.
        """
        self._data_store.runs = []


class DataStore:
    """
    A model object that acts purely as data storage. All data access operations are pushed to DAO objects
    to make it a simple process to add different types of data in the future without complicating this class.
    This class is a singleton.
    """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.runs = []

    __instance = None

    def __init__(self):
        if not DataStore.__instance:
            DataStore.__instance = DataStore.__DataStore()

    def __getattr__(self, name):
        """
        Attribute requests are passed to the __DataStore instance.
        :param name: name of attribute
        :return value: value of attribute
        """
        return getattr(self.__instance, name)
