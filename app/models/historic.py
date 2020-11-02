from mongoengine import Document, fields, DEFAULT_CONNECTION_NAME

from app import pairs
from database import DB_BACKTEST


class HistoricRow(Document):
    pair = fields.StringField(
        choices=pairs.pairs_without_slash,
        unique_with='date'
    )
    date = fields.DateTimeField()
    open = fields.FloatField()
    high = fields.FloatField()
    low = fields.FloatField()
    close = fields.FloatField()
    volume = fields.FloatField()

    meta = {
        "db_alias": DB_BACKTEST
    }

    def __str__(self):
        return "{pair} | {date}".format(
            pair = self.pair,
            date = self.date
        )