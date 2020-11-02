import logging
from datetime import timedelta

from app.exceptions.backtest import InsufficientFundsException
from app.models import choices
from app.models.choices import (
    MessageTypeChoices,
    TransactionClosedByChoices,
    TransactionStatusChoices,
    PositionTypeChoices
)
from app.models.positions import StopLoss, get_ratio_for_realized_position
from app.models.transactions import Transaction
from app.processing.process_signal import ProcessSignalManager
from app.backtest.position_close_detector import (
    PositionCloseDetector,
    get_initial_price_of_nearest_historic_row_date_for_pair
)


logger = logging.getLogger(__file__)


class Event(object):

    def __init__(self, execution_date, event_id):
        self.execution_date = execution_date
        self.event_id = event_id

    def execute(self):
        raise NotImplementedError

    def get_event_duration(self, transaction_date):
        return (self.execution_date - transaction_date).total_seconds()/60/60/24


class EventCancel(Event):

    def __init__(self, execution_date, backtest, transaction):
        self.execution_date = execution_date
        self.backtest = backtest
        self.transaction = transaction
        super().__init__(
            execution_date=execution_date, event_id=transaction.get_event_id_cancel()
        )

    def execute(self):
        # cancel stop loss.
        stop_loss = self.transaction.stop_loss
        stop_loss.has_reached_level_before_days_limit = False
        self.backtest.queue.remove_event_by_id(stop_loss.generate_stop_loss_id())

        # cancel take_profits
        take_profits_open = [tp for tp in self.transaction.take_profits
                             if tp.is_closed is False]  # is_closed = False == otwarta
        for tp in take_profits_open:
            tp.result = tp.amount_invested
            tp.has_reached_level_before_days_limit = False
            self.backtest.wallet.on_transaction_refund_back(tp.result)
            self.backtest.queue.remove_event_by_id(tp.generate_take_profit_id)

        self.transaction.save()


# TRANSACTION
class EventTakeProfit(Event):

    def __init__(self, backtest, execution_date, take_profit, event_id):
        self.backtest = backtest
        self.take_profit = take_profit
        self.event_id = event_id
        super(EventTakeProfit, self).__init__(
            execution_date=execution_date, event_id=event_id
        )

    def execute(self):
        self.backtest.statistics.on_position_event_realised(PositionTypeChoices.TAKE_PROFIT)
        transaction = Transaction.objects.get(pk=self.take_profit.transaction_id)
        take_profit = transaction.take_profits[self.take_profit.order_number-1]
        take_profit.closed_date = self.execution_date

        duration = self.get_event_duration(transaction.date_open)
        take_profit.duration = duration

        if transaction.status in TransactionStatusChoices.choices_closed:
            logger.info(f'Transaction(pk={transaction.pk} has been already closed. '
                        f'Stop loss will not be executed.')
            take_profit.has_reached_level_before_days_limit = True
            take_profit.is_transaction_already_closed = True
            transaction.save()
            return

        logging.info('Take profit realised :) !')
        take_profit.is_closed = True
        take_profit.has_reached_level_before_days_limit = True
        take_profit.ratio = get_ratio_for_realized_position(
            transaction.decision.type, take_profit.price, transaction.initial_pair_price
        )

        take_profit.result = float(take_profit.amount_invested) * take_profit.ratio
        if not take_profit.result:  # it means that it can be take_profit that strategy didn't assigned
            logger.error('tp result should not be 0')
            take_profit.result = 0

        self.backtest.wallet.on_transaction_position_realised(take_profit.result)

        if take_profit.is_last:
            self.backtest.statistics.on_transaction_closed(TransactionClosedByChoices.TAKE_PROFIT)
            transaction.on_last_take_profit_or_stop_loss_reached(
                TransactionClosedByChoices.TAKE_PROFIT,
                date_closed=self.execution_date,
                duration=duration
            )
            self.backtest.queue.remove_event_by_id(transaction.get_event_id_cancel())

        self.backtest.statistics.on_event_realised(self, self.backtest.wallet)
        transaction.save()
        return

    def __repr__(self):
        return f"EventTakeProfit #{self.take_profit.order_number}. " \
               f"transaction.id={self.take_profit.transaction_id}"


class EventStopLoss(Event):

    def __init__(self, backtest, execution_date, stop_loss, event_id):
        self.backtest = backtest
        self.stop_loss = stop_loss
        self.event_id = event_id
        super(EventStopLoss, self).__init__(
            execution_date=execution_date, event_id=event_id
        )

    def execute(self):
        self.backtest.statistics.on_position_event_realised(PositionTypeChoices.STOP_LOSS)
        transaction = Transaction.objects.get(pk=self.stop_loss.transaction_id)
        stop_loss = transaction.stop_loss
        stop_loss.closed_date = self.execution_date
        stop_loss.has_reached_level_before_days_limit = True

        duration = self.get_event_duration(transaction.date_open)
        stop_loss.duration = duration

        if transaction.status in TransactionStatusChoices.choices_closed:
            logger.info(f'Transaction(pk={transaction.pk} has been already closed. '
                        f'Stop loss will not be executed.')
            stop_loss.is_transaction_already_closed = True
            transaction.save()
            return

        logging.info('Stop loss realised :( !')
        stop_loss.is_closed = True

        # STOP LOSS CLOSED ON TIME - before days limit
        stop_loss.ratio = get_ratio_for_realized_position(
            transaction.decision.type, stop_loss.price, transaction.initial_pair_price
        )

        stop_loss_result = transaction.get_stop_loss_result()
        stop_loss.result = float(stop_loss_result) * stop_loss.ratio
        if not stop_loss.result:
            logger.error('SL Should not be 0')

        # we add amount but ratio is <1 so we will have less money than before investing
        self.backtest.wallet.on_transaction_position_realised(stop_loss.result)
        self.backtest.statistics.on_transaction_closed(TransactionClosedByChoices.STOP_LOSS)
        transaction.on_last_take_profit_or_stop_loss_reached(
            TransactionClosedByChoices.STOP_LOSS,
            date_closed=self.execution_date,
            duration=duration
        )
        self.backtest.queue.remove_event_by_id(transaction.get_event_id_cancel())

        self.backtest.statistics.on_event_realised(self, self.backtest.wallet)
        transaction.save()

    def __repr__(self):
        return f"EventStopLoss of transaction.id={self.stop_loss.transaction_id}"


# MESSAGE
class EventMessageReceived(object):

    def __init__(self, message, backtest, tag=None):
        event = None
        if message.type == MessageTypeChoices.SKIP:
            event = EventSkip(message)
        elif message.type == MessageTypeChoices.SIGNAL:
            event = EventSignal(message, backtest, tag)
        elif message.type == MessageTypeChoices.CORRECTION:
            event = EventCorrection(message, backtest)
        self.event = event


class EventSkip(Event):

    def __init__(self, message):
        execution_date = message.date
        super(EventSkip, self).__init__(execution_date, 'event_skip')

    def execute(self):
        """event skip haven't got logic"""
        logger.info('Event skipped')


class EventSignal(Event):

    def __init__(self, message, backtest, tag=None):
        self.message = message
        self.backtest = backtest
        self.tag = tag
        execution_date = message.date
        event_id = f"{tag}_{message.id_universal}"
        super(EventSignal, self).__init__(execution_date, event_id=event_id)

    def execute(self):
        logger.info(f'Executing EventSignal for message(id_universal={self.message.id_universal}')
        decision_signal = ProcessSignalManager.get_decision_signal(self.message)

        position_close_date_take_profits, position_close_date_stop_loss = \
            PositionCloseDetector.detect(decision_signal)

        transaction = Transaction(
            tag=self.tag,
            channel=self.message.channel.name,
            decision=decision_signal,
            status=choices.TransactionStatusChoices.OPEN,
            pair=decision_signal.pair,
            date_open=decision_signal.date,
            strategy_label=self.backtest.config.strategy_label
        ).save()

        try:
            assigned_amount = self.backtest.wallet.on_transaction_open()
            transaction.amount_invested = assigned_amount
        except InsufficientFundsException:
            logger.error('Insufficient funds')
            transaction.status = TransactionStatusChoices.INSUFFICIENT_FUNDS
            transaction.save()
            return

        if decision_signal.initial_price is not None:
            initial_price = decision_signal.initial_price
            retries = None
        else:
            initial_price, retries = get_initial_price_of_nearest_historic_row_date_for_pair(
                pair=decision_signal.pair, date=decision_signal.date
            )

        if initial_price is None:
            transaction.on_initial_price_not_found()
            self.backtest.wallet.on_transaction_refund_back(transaction.amount_invested)
            self.backtest.statistics.increment_transaction_initial_pair_not_found()
            return

        transaction.initial_pair_price = initial_price
        transaction.initial_pair_price_retries = retries

        transaction.take_profits = transaction.assign_take_profits_from_strategy(
            assigned_amount, self.backtest.config.strategy, position_close_date_take_profits
        )
        transaction.stop_loss = StopLoss(
            **decision_signal.stop_loss,
            closed_date=position_close_date_stop_loss if position_close_date_stop_loss != PositionCloseDetector.NOT_FOUND else None,
            amount_invested=assigned_amount
        )

        for take_profit in transaction.take_profits:
            if not take_profit.amount_invested:  # it means that strategy assigned 0 to amount_invested
                continue

            execution_date_tp = position_close_date_take_profits[take_profit.order_number]
            has_reached_tp = execution_date_tp not in [PositionCloseDetector.NOT_FOUND, None]
            take_profit.has_reached_tp = has_reached_tp
            take_profit.transaction_id = str(transaction.pk)

            if has_reached_tp:
                take_profit.closed_date = execution_date_tp
                tp_event = EventTakeProfit(
                    event_id=take_profit.generate_take_profit_id(),
                    backtest=self.backtest,
                    execution_date=execution_date_tp,
                    take_profit=take_profit
                )
                self.backtest.queue.add(tp_event)

        has_reached_sl = self.is_stop_loss_reached(position_close_date_stop_loss)

        stop_loss = transaction.stop_loss
        stop_loss.transaction_id = str(transaction.pk)
        stop_loss.has_reached_sl = has_reached_sl
        if has_reached_sl:
            stop_loss.closed_date = position_close_date_stop_loss
            sl_event = EventStopLoss(
                event_id=stop_loss.generate_stop_loss_id(),
                backtest=self.backtest,
                execution_date=position_close_date_stop_loss,
                stop_loss=stop_loss
            )
            self.backtest.queue.add(sl_event)

        if self.is_any_position_realisation_date_found(transaction):
            transaction.status = TransactionStatusChoices.ANY_POSITION_REALISATION_DATE_NOT_FOUND
            self.backtest.wallet.on_transaction_refund_back(transaction.amount_invested)
            self.backtest.statistics.increment_transaction_any_position_realisation_date_not_found()

        event_cancel = self.add_event_cancel(transaction)

        self.backtest.queue.add(event_cancel)
        self.backtest.statistics.on_event_realised(self, self.backtest.wallet)
        transaction.save()

    def is_stop_loss_reached(self, position_close_date_stop_loss):
        return position_close_date_stop_loss not in [PositionCloseDetector.NOT_FOUND, None]

    def add_event_cancel(self, transaction):
        return EventCancel(
            execution_date=transaction.date_open+timedelta(
                days=self.backtest.config.max_days_in_position
            ),
            backtest=self.backtest,
            transaction=transaction
        )

    def is_any_position_realisation_date_found(self, transaction):
        return all(
            [tp['has_reached_tp'] == False for tp in transaction.take_profits]) \
               and transaction.stop_loss['has_reached_sl'] == False

    def __repr__(self):
        return f"EventSignal: message.id={self.message.id_universal}"


class EventCorrection(Event):

    def __init__(self, message, backtest=None):
        self.message = message
        self.backtest = backtest
        execution_date = message.date
        super(EventCorrection, self).__init__(execution_date, 'event_Correction')


class EventCorrectionCancelAll():

    def __init__(self, transaction_to_correct):
        self.transaction_to_correct = transaction_to_correct

    def execute(self):
        self.transaction_to_correct.cancel_all()


class EventCorrectionCancelParticular():

    def __init__(self, transaction_to_correct, decision):
        self.transaction_to_correct = transaction_to_correct
        self.decision = decision

    def execute(self):
        self.transaction_to_correct.cancel_particular(self.decision.canceled_take_profit)


class EventCorrectionHold():

    def __init__(self, transaction_to_correct, decision):
        self.transaction_to_correct = transaction_to_correct
        self.decision = decision

    def execute(self):
        self.transaction_to_correct.add_hold_days(self.decision.add_days_amount)
