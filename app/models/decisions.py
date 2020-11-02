import datetime

from mongoengine import (
    Document,
    StringField, DateTimeField,
    ReferenceField, DecimalField,
    IntField, ListField, DictField
)

from app.models.choices import (
    ChannelNameChoices,
    DecisionSignalTypeChoices,
    DecisionCorrectionTypeChoices,
    MessageTypeChoices
)
from app.models.exceptions import (
    IncorrectDecisionSignalPair,
    IncorrectDecisionSignalMessageType,
    IncorrectDecisionCorrectionMessage,
)
from app.models.messages import Message
from app.pairs import pairs_without_slash


# DECISIONS
class DecisionSignal(Document):
    created_at = DateTimeField(default=datetime.datetime.now)
    date = DateTimeField(default=datetime.datetime.now)
    processor_used = StringField(choices=ChannelNameChoices.choices)
    message = ReferenceField(Message)
    initial_price = DecimalField(precision=6)
    pair = StringField(choices=pairs_without_slash, required=True)
    take_profits = ListField()
    stop_loss = DictField()
    type = StringField(choices=DecisionSignalTypeChoices.choices)

    def clean(self):
        if self.pair is not None:
            self.pair = self.pair.replace('/', '').upper()
        return super(DecisionSignal, self).clean()

    def validate(self, clean=True):

        self.clean()

        if self.pair not in pairs_without_slash:
            raise IncorrectDecisionSignalPair(**{"pair":self.pair})
        if self.message.type not in [MessageTypeChoices.SIGNAL, MessageTypeChoices.SIGNAL_EXTRA]:
            raise IncorrectDecisionSignalMessageType
        return super(DecisionSignal, self).validate(clean)

    def save(self, *args, **kwargs):
        return super(DecisionSignal, self).save(*args, **kwargs)


class DecisionCorrection(Document):
    processor_used = StringField(choices=ChannelNameChoices.choices)
    message = ReferenceField(Message)
    transaction_to_correct = ReferenceField('Transaction', required=True)
    type = StringField(choices=DecisionCorrectionTypeChoices.choices)
    date = DateTimeField(default=datetime.datetime.now)

    meta = {
        'allow_inheritance': True
    }

    def validate(self, clean=True):
        if self.message.type != MessageTypeChoices.CORRECTION:
            raise IncorrectDecisionCorrectionMessage

        return super(DecisionCorrection, self).validate(clean)


class CorrectionActionCancelAll(DecisionCorrection):
    pass


class CorrectionActionHold(DecisionCorrection):
    add_days_amount = IntField()
