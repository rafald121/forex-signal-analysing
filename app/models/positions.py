from mongoengine import (
    Document,
    DynamicEmbeddedDocument,
    StringField,
    EmbeddedDocumentListField,
    DateTimeField,
    ReferenceField,
    DecimalField,
    BooleanField,
    EmbeddedDocumentField,
    IntField,
    FloatField)

from app.models.choices import DecisionSignalTypeChoices, PositionTypeChoices


def get_ratio_for_realized_position(position_type, position_price, transaction_initial_price):

    try:
        if position_type == DecisionSignalTypeChoices.LONG:
            return float(position_price)/float(transaction_initial_price)

        if position_type == DecisionSignalTypeChoices.SHORT:
            return float(transaction_initial_price)/float(position_price)

    except (TypeError, ValueError, Exception):
        return 1


class StopLoss(DynamicEmbeddedDocument):
    transaction_id = StringField()

    amount_invested = DecimalField(precision=6)
    price = DecimalField(precision=6)
    result = DecimalField(precision=6)
    ratio = FloatField()

    is_closed = BooleanField(default=False)  # is closed naturally
    has_reached_level_before_days_limit = BooleanField()
    closed_date = DateTimeField(default=None)
    duration = FloatField(default=None)
    retries_founding_price_when_days_exceed = IntField()
    is_transaction_already_closed = BooleanField(default=None)
    ratio_default = FloatField(default=None)

    def generate_stop_loss_id(self):
        return f"{self.transaction_id}_sl"

    def on_reach(self, closed_date=None):
        pass

    def cancel(self):
        self.is_closed = True

    def save(self, *args, **kwargs):
        return super(StopLoss, self).save(*args, **kwargs)

    def __str__(self):
        return f"SL: {self.price}"


class TakeProfit(DynamicEmbeddedDocument):
    order_number = IntField(min_value=1)
    transaction_id = StringField()

    amount_invested = DecimalField(precision=6)
    price = DecimalField(precision=6)
    result = DecimalField(precision=6)
    ratio = FloatField()
    ratio_default = FloatField(default=None)

    is_closed = BooleanField(default=False)
    is_last = BooleanField(default=False)
    has_reached_level_before_days_limit = BooleanField()
    closed_date = DateTimeField(default=None)
    duration = FloatField(default=None)
    retries_founding_price_when_days_exceed = IntField()
    is_transaction_already_closed = BooleanField(default=None)

    def generate_take_profit_id(self):
        return f"{self.transaction_id}_tp#{self.order_number}"

    def on_reach(self, closed_date=None):
        pass

    def cancel(self):
        self.is_closed = True

    def on_last_finish(self):
        pass

    def __str__(self):
        return f"TP#{self.order_number}: {self.price}"