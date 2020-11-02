import datetime
import logging

from mongoengine import (
    EmbeddedDocument, DecimalField, StringField,
    DynamicDocument, ReferenceField, EmbeddedDocumentField, DateTimeField, IntField,
    ListField, BooleanField, FloatField
)


from app.backtest.position_close_detector import PositionCloseDetector
from app.models.decisions import DecisionSignal
from app.models.choices import (
    TransactionStatusChoices,
    AmountInvestedCurrenciesChoices,
    TransactionClosedByChoices,
    ChannelNameChoices
)
from app.models.positions import TakeProfit
from app.pairs import pairs_without_slash

logger = logging.getLogger(__name__)


class AmountInvested(EmbeddedDocument):
    amount = DecimalField(min_value=0)
    currency = StringField(choices=AmountInvestedCurrenciesChoices.choices)


class Transaction(DynamicDocument):
    created_at = DateTimeField(default=datetime.datetime.now)
    tag = StringField()
    channel = StringField(choices=ChannelNameChoices.choices)

    decision = ReferenceField(DecisionSignal)
    pair = StringField(choices=pairs_without_slash, required=True)
    take_profits = ListField(EmbeddedDocumentField('TakeProfit'))
    stop_loss = EmbeddedDocumentField('StopLoss')

    initial_pair_price = DecimalField(precision=6)
    initial_pair_price_retries = IntField()

    amount_invested = IntField()
    result = DecimalField(precision=6)
    result_ratio = FloatField()

    date_open = DateTimeField()
    date_closed = DateTimeField()
    status = StringField(choices=TransactionStatusChoices.choices)
    closed_by = StringField(choices=TransactionClosedByChoices.choices)
    duration = FloatField(default=None)

    is_ratio_suspicious = BooleanField(default=None)
    strategy_label = StringField()

    @property
    def profit_result(self):
        result = 0
        return result

    @property
    def history(self):
        return

    def assign_take_profits_from_strategy(self, assigned_amount, strategy, tp_closed_dates):
        take_profits_length = len(self.decision.take_profits)
        distribution = strategy.get(take_profits_length)
        if distribution is None:
            logger.error("add some extra distribution")

        take_profits = []
        if len(self.decision.take_profits) != len(tp_closed_dates):
            raise Exception("Incompatiblity")

        for tp, closed_date in zip(self.decision.take_profits, tp_closed_dates.values()):
            if closed_date == PositionCloseDetector.NOT_FOUND:
                closed_date = None

            try:
                distribution_percentage = distribution[tp['order_number']]
            except KeyError:
                if len(self.decision.take_profits) == 1:
                    distribution_percentage = 1
                    tp['order_number'] = 1
                else:
                    distribution_percentage = 0

            if distribution_percentage != 0:

                if list(distribution.values()).count(1) == 1:
                    tp['is_last'] = True

                take_profit = TakeProfit(
                    **tp,
                    closed_date=closed_date,
                    amount_invested=assigned_amount*distribution_percentage
                )

                take_profits.append(take_profit)

        try:
            if take_profits[-1]['is_last'] == False:
                logger.error('incorrect situation')
                take_profits[-1]['is_last'] = True
        except Exception:
            logger.error('Jaki exception ląduje?')

        return take_profits

    def get_event_id_cancel(self):
        return "{transaction_id}_cancel".format(transaction_id=self.id)


    def get_stop_loss_result(self):
        """
        There can be situation that stop loss has been triggered after 1 from 3 realised take_profits
        so in this case we realise StopLoss with 66% of invested money
        If 2 of 3 take profits are realised then we return 1/3*stop_loss.amount_invested
        """
        not_realised_take_profits = [tp for tp in self.take_profits
                                     if tp.is_closed is False]
        result = sum([tp.amount_invested for tp in not_realised_take_profits])
        return result

    def get_last_occured_event(self):
        take_profits_dates = {
            tp['order_number']: tp['closed_date']
            for tp in self.take_profits
            if tp['closed_date'] is not None
        }
        if self.stop_loss['closed_date'] != None:
            stop_loss_date = {'sl': self.stop_loss['closed_date']}
        else:
            stop_loss_date = {}

        zbior = {
            **take_profits_dates,
            **stop_loss_date
        }
        zbior_sorted = sorted(zbior.items(), key=lambda d: d[1], reverse=True)
        last_event = zbior_sorted[0]
        if last_event[0] == 'sl':
            return 'sl'
        elif isinstance(last_event[0], int):
            return 'tp'
        else:
            logger.error(f'LastEvent value error: {last_event[0]}')

    def on_last_take_profit_or_stop_loss_reached(self, closed_by, date_closed=None, duration=None):
        self.status = TransactionStatusChoices.CLOSED
        self.date_closed = date_closed
        self.closed_by = closed_by
        self.result = self.get_result()
        self.result_ratio = self.result/self.amount_invested
        self.duration = duration

        if self.is_result_suspicious():
            self.is_ratio_suspicious = True
            self.result = self.amount_invested
        else:
            self.is_ratio_suspicious = False

        self.save()

    def on_initial_price_not_found(self):
        self.status = TransactionStatusChoices.INITIAL_PRICE_NOT_FOUND
        self.save()

    def get_closed_take_profits_result(self):
        result = 0
        for tp in self.take_profits:
            if tp.is_closed:
                if tp.result is not None:
                    result += tp.result
                else: # is closed without result ? some error....
                    result += tp.amount_invested
        return result

    def get_result(self):
        if self.closed_by == TransactionClosedByChoices.TAKE_PROFIT:
            try:
                return self.get_closed_take_profits_result()
            except TypeError:
                take_profit_result = 0
                pass
        elif self.closed_by == TransactionClosedByChoices.STOP_LOSS:
            closed_take_profits_result = self.get_closed_take_profits_result()
            return closed_take_profits_result+(self.amount_invested-closed_take_profits_result)*self.stop_loss.ratio
        else:
            return self.amount_invested

    def is_result_suspicious(self):
        return self.result_ratio < 0.9 or self.result_ratio > 1.1 or \
               (self.closed_by == 'take_profit' and self.result < self.amount_invested) or \
               (self.closed_by =='stop_loss' and self.result > self.amount_invested)

    def cancel_all(self):
        for take_profit in self.decision.take_profits:
            take_profit.cancel()

    def cancel_particular(self, take_profit):
        take_profit.cancel()
        pass

    def add_hold_days(self, days):
        self.duration += days

    def change_stop_loss(self):
        pass

    def change_take_profit(self, take_profit):
        pass

    def add_take_profit(self, take_profit):
        pass
