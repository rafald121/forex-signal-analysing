from datetime import datetime
from tqdm import tqdm
from collections import defaultdict

from telegram.db_conn import get_collection_for_database, RAW_MESSAGE
from app.pairs import pairs_without_slash

collection = get_collection_for_database(RAW_MESSAGE)

distinct_pairs = defaultdict(list)

date_from = datetime(2018, 1, 1)
date_to = datetime(2018, 12, 31)


def print_set_of_pairs():
    all_rows = collection.find({})
    for row in tqdm(all_rows):
        if not (row['date'] > date_from and row['date'] < date_to):
            continue
        row_message_text = row['text']
        if row_message_text:
            pair = [pair for pair in pairs_without_slash
                    if pair.lower() in row_message_text.lower()]
            if pair:
                distinct_pairs[pair[0]].append(row['date'])

    return distinct_pairs
