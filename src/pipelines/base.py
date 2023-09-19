# standard library imports

# third party imports

# local imports
from src.databases.sqlite_facade import SQLiteFacade


class Pipeline:
    """
    Base class for all pipelines
    """

    def __init__(self):
        """
        Initialize Pipeline class
        """

        self.sqlite_facade = SQLiteFacade()
