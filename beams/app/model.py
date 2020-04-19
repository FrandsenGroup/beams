
class RunService:
    """
    Handles requests for data operations on runs sent by Presenter classes. Emits signals.
    """

    class __Observers:
        """
        Persistent object to store observers.
        """

        def __init__(self):
            self.observers = {}

    __observers = None

    def __init__(self):
        if not RunService.__observers:
            RunService.__observers = RunService.__Observers()

        self.dao = RunDAO()


class RunDAO:
    """
    Handles simple data access operations for runs stored by the program.
    """
    def __init__(self):
        self.model = RunDataStore()


class RunDataStore:
    """
    A model object that acts purely as data storage. All data access operations are pushed to DAO objects
    to make it a simple process to add different types of data in the future. This class is a singleton.
    """

    class __DataStore:
        """
        Singleton instance object to hold data.
        """

        def __init__(self):
            self.runs = None

    __instance = None

    def __init__(self):
        if not RunDataStore.__instance:
            RunDataStore.__instance = RunDataStore.__DataStore()

    def __getattr__(self, name):
        """
        Attribute requests are passed to the __DataStore instance.

        :param name: name of attribute
        :return value: value of attribute
        """
        return getattr(self.__instance, name)
