import datetime
import logging
import pandas as pd

from mongoengine.errors import NotUniqueError

from database import (
    connect_to_db,
    get_collection_for_database,
    COLLECTION_FILLED_PAIR,
    DB_BACKTEST
)
from app.models.historic import HistoricRow
from app.utils.utils_file import get_all_directories_of_directory

logger = logging.getLogger(__file__)

collection = get_collection_for_database(COLLECTION_FILLED_PAIR)


class HistDataDbFill:

    col_names = ['DATE', 'TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOL']

    def __init__(self):
        connect_to_db(alias=DB_BACKTEST)

    def add_all_data_to_db_from_path(self, path, exclude=()):

        directories = get_all_directories_of_directory(path, without_first=True)
        for nr, dir in enumerate(directories):
            pair = dir.rsplit('/', 1)[1]
            if pair in exclude:
                continue
            df = pd.read_csv(dir+'/merged.csv', names=self.col_names)
            self.add_df_to_db(pair, df)
        print('end of job')

    def add_df_to_db(self, pair, df):
        print("Zaczynam dodawac dla pary: {}".format(pair))
        for i, row in df.iterrows():
            try:
                obj = HistoricRow(
                    pair=pair,
                    date=self.get_datetime(row['DATE'], row['TIME']),
                    open=row['OPEN'],
                    high=row['HIGH'],
                    low=row['LOW'],
                    close=row['CLOSE'],
                    volume=row['VOL']
                )
                obj.save()
            except NotUniqueError:
                print(f"{pair} record already added to db")
            except Exception as e:
                print("Another error: {}".format(e))
        collection.insert_one({
            "pair": pair,
            "amount": int(df.size)
        })
        print(f'added {df.size} elements for pair={pair} at date: {datetime.datetime.now()}')

    @staticmethod
    def get_datetime(date, time):
        try:
            date = datetime.datetime(
                year=int(date.split('.')[0]),
                month=int(date.split('.')[1]),
                day=int(date.split('.')[2]),
                hour=int(time.split(':')[0]),
                minute=int(time.split(':')[1])
            )
        except IndexError:
            print("error while converting date: {}, time: {}".format(date, time))
        return date
