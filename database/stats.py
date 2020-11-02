from app.models.historic import HistoricRow
from database import connect_to_db


class DbStatistics:

    def __init__(self):
        connect_to_db()

    def get_distinct_pair_values(self):
        return HistoricRow.objects.distinct(field='pair')

    def get_disctinct_pair_with_size(self, more_than=0):
        pairs = self.get_distinct_pair_values()
        count = lambda pair :  HistoricRow.objects(pair=pair).count()
        dicttinct_pairs_count = {
            pair: count(pair) for pair in pairs
            if count(pair) > more_than
        }
        return dicttinct_pairs_count, len(dicttinct_pairs_count)
