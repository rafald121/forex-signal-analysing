import pandas as pd

from datetime import datetime
from telegram.db_conn import get_collection_for_database, RAW_MESSAGE

collection = get_collection_for_database(RAW_MESSAGE)


def check_min_date():
    min_date = datetime.now()

    all_rows = collection.find({})

    for row in all_rows:
        if row['date'] < min_date:
            min_date = row['date']
    print(min_date)


def get_dataframe_from_collection(collection):
    dates = [item['date'] for item in list(collection.find({}, {'date': 1, '_id': 0}))]
    data = {'dates': dates}

    return pd.DataFrame(data=data)
