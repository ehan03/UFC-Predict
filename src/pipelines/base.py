# standard library imports

# third party imports

# local imports
from src.databases.supabase_facade import SupabaseFacade


class Pipeline:
    """
    Base class for all pipelines
    """

    def __init__(self):
        """
        Initialize Pipeline class
        """

        self.supabase_facade = SupabaseFacade()
