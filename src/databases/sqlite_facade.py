"""
This module contains the SQLiteFacade class, which is a wrapper for the sqlite3
and contains helper methods for interacting with the database.
"""

# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd

# local imports
from src.databases.create_statements import get_create_statement


class SQLiteFacade:
    """
    Facade for interacting with the SQLite database
    """

    def __init__(self) -> None:
        """
        Initialize the facade class
        """

        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()

    def create_table(self, table_name: str) -> None:
        """
        Create the specified table

        Parameters:
            table_name (str): The name of the table to create
        """

        self.cur.execute(get_create_statement(table_name))
        self.conn.commit()

    def truncate_table(self, table_name: str) -> None:
        """
        Truncate the specified table

        Parameters:
            table_name (str): The name of the table to truncate
        """

        self.cur.execute(f"DELETE FROM {table_name}")
        self.conn.commit()

    def insert_into_table(self, data: pd.DataFrame, table_name: str) -> None:
        """
        Insert the specified data into the specified table

        Parameters:
            data (pd.DataFrame): The data to insert
            table_name (str): The name of the table to insert into
            insert_type (str): The type of insert to perform
        """

        data.to_sql(table_name, self.conn, if_exists="append", index=False)
        self.conn.commit()

    def close_connection(self):
        """
        Close the connection to the database
        """

        self.conn.close()
