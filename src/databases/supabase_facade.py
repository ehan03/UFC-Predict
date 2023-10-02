# standard library imports
import os

# third party imports
import pandas as pd
from supabase.client import Client, create_client

# local imports


class SupabaseFacade:
    """
    Facade for interacting with the Supabase database
    """

    MAXIMUM_ROWS = 1000

    def __init__(self):
        """
        Initializes the Supabase facade
        """

        self.supabase_url = os.environ.get("SUPABASE_URL", "")
        self.supabase_key = os.environ.get("SUPABASE_KEY", "")
        assert self.supabase_url and self.supabase_key

        self.client: Client = create_client(
            self.supabase_url,
            self.supabase_key,
        )

    def fetch_all(self, table_name):
        """
        Fetches all records from a table, paginating the results if necessary, and
        returns as a pandas dataframe
        """

        results = []
        offset = 0
        while True:
            response = (
                self.client.table(table_name)
                .select("*")
                .range(offset, offset + self.MAXIMUM_ROWS)
                .execute()
            )

            if len(response.data) == 0:
                break

            results.extend(response.data)
            offset += self.MAXIMUM_ROWS

        df = pd.DataFrame(results)

        return df

    def bulk_insert(self, table_name, df):
        """
        Inserts a dataframe into a table
        """

        df = df.convert_dtypes()
        df = df.astype(object).where(pd.notnull(df), None)
        for i in range(0, len(df), self.MAXIMUM_ROWS):
            self.client.table(table_name).insert(
                df[i : i + self.MAXIMUM_ROWS].to_dict("records")
            ).execute()

    def bulk_upsert(self, table_name, df, on_conflict):
        """
        Upserts a dataframe into a table
        """

        df = df.convert_dtypes()
        df = df.astype(object).where(pd.notnull(df), None)
        for i in range(0, len(df), self.MAXIMUM_ROWS):
            self.client.table(table_name).upsert(
                df[i : i + self.MAXIMUM_ROWS].to_dict("records"),
                on_conflict=on_conflict,
            ).execute()
