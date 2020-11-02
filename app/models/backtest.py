from mongoengine import (
    DynamicDocument, DynamicEmbeddedDocument,
    StringField, EmbeddedDocumentListField, DateTimeField, FloatField,
    ReferenceField, DecimalField
)

from models.choices import MessageFillTypeChoices


class BacktestStatistics(DynamicEmbeddedDocument):
    pass


class BacktestReport(DynamicEmbeddedDocument):
    pass


class Backtest(DynamicDocument):
    description = StringField(max_length=256)
    fill_message_type = StringField(choices=MessageFillTypeChoices.choices)
    date_to = DateTimeField()
    date_from = DateTimeField()
    profit_result = FloatField()


class WalletHistory(DynamicEmbeddedDocument):
    date = DateTimeField()
    amount_free = DecimalField()
    amount_used = DecimalField()


class Wallet(DynamicDocument):
    backtest = ReferenceField(Backtest)
    history = EmbeddedDocumentListField(WalletHistory)

    @property
    def available_amount_free(self):
        return

    @property
    def available_amount_used(self):
        return