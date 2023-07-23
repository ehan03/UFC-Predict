# standard library imports
import sqlite3

# third party imports
import pandas as pd

# local imports
from .items import BoutItem, FighterItem
from .utils import map_bout_columns, map_fighter_columns


class FightersSQLitePipeline:
    def open_spider(self, spider):
        self.rows = []
        self.conn = sqlite3.connect("../../data/ufc.db")

    def process_item(self, item, spider):
        if isinstance(item, FighterItem):
            self.rows.append(dict(item))
        return item

    def close_spider(self, spider):
        if self.rows:
            fighters_df = pd.DataFrame(self.rows).rename(
                columns={
                    col: map_fighter_columns(col) for col in FighterItem.fields.keys()
                }
            )

            # Sort by name
            fighters_df["first name"] = fighters_df["FIGHTER_NAME"].apply(
                lambda x: x.split()[0]
            )
            fighters_df["last name"] = fighters_df["FIGHTER_NAME"].apply(
                lambda x: x.split()[-1]
            )
            fighters_df = fighters_df.sort_values(by=["last name", "first name"])
            fighters_df = fighters_df.drop(columns=["first name", "last name"])

            # Insert into database
            fighters_df.to_sql("FIGHTERS", self.conn, if_exists="replace", index=False)

        self.conn.commit()
        self.conn.close()


class BoutsSQLitePipeline:
    def open_spider(self, spider):
        self.rows = []
        self.conn = sqlite3.connect("../../data/ufc.db")
        self.c = self.conn.cursor()

    def process_item(self, item, spider):
        if isinstance(item, BoutItem):
            self.rows.append(dict(item))
        return item

    def close_spider(self, spider):
        if self.rows:
            bouts_df = pd.DataFrame(self.rows)

            # Sort by date and bout ordinal within each event

            bouts_df = bouts_df.drop(columns=["bout_ordinal"])
            bouts_df = bouts_df.rename(
                columns={col: map_bout_columns(col) for col in BoutItem.fields.keys()}
            )

            # Insert into database
            bouts_df.to_sql("BOUTS", self.conn, if_exists="replace", index=False)

        self.conn.commit()
        self.conn.close()
