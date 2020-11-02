import logging
from collections import defaultdict


from datetime import datetime
from typing import Union

from app.backtest.events import EventSignal, EventTakeProfit, EventStopLoss
from app.exceptions.backtest import InsufficientFundsException
from app.exceptions.process import IncorrectDecisionSignalTradeLevels
from app.models import choices
from app.models.choices import MessageFillTypeChoices
from app.models.messages import Message
from app.models.backtest import Backtest as BacktestModel
from app.processing.recognise import RecogniseMessageManager
from app.backtest import events, config
from app.backtest._queue import Queue
from app.backtest.wallet import Wallet
from app.backtest.strategies import StrategyTakeProfit

date_from = datetime(year=2018, month=1, day=1)
date_to = datetime(year=2018, month=12, day=31)

format = '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
logging.basicConfig(format=format, level=logging.INFO)


class BacktestTimeline:

    def __init__(self, backtest):
        self.backtest = backtest
        self.queue = backtest.queue
        self.events_executed_count = 0

    def run_queue(self):

        while self.queue.get() != None:
            event = self.queue.pop()
            self.save_event(event)
            self.backtest.statistics.add_event(event)

            if self.is_timeline_condition_met(event):
                logging.info(f"Amount of executed events: {self.events_executed_count} "
                             f"Amount of remaining events on queue: {self.queue.get_length()} "
                             f"Wallet state: {self.backtest.wallet.get_state()}")
                try:
                    event.execute()
                    self.events_executed_count += 1
                except InsufficientFundsException:
                    logging.exception(f"Error occured while executing event={event.__repr__()}")
                except IncorrectDecisionSignalTradeLevels:
                    logging.exception(f"Error occured while executing event={event.__repr__()}")
        self.backtest.statistics.executed_events_amount = self.events_executed_count

    def is_timeline_condition_met(self, event):
        return self.is_event_instance_signal_type(event)

    def is_event_instance_signal_type(self, event):
        return isinstance(event, EventSignal) or \
               isinstance(event, EventTakeProfit) or \
               isinstance(event, EventStopLoss)

    def save_event(self, event):
        pass


class Backtest:

    def __init__(self,
                 config: "BacktestConfig",
                 messages_filler: Union["BacktestMessagesFillerObjects", "BacktestMessagesFillerRawMessages"],
                 ):
        self.messages_filler = messages_filler,
        messages_filler.backtest = self
        self.config = config

    def run_analysing(self):
        self.timeline.run_queue()

    def fill_messages(self):
        self.messages_filler.add_messages()

    def create_backtest_related_instances(self):
        self.create_backtest_related_instance_wallet()
        self.create_backtest_related_instance_queue()
        self.create_backtest_related_instance_timeline()
        self.create_backtest_related_instance_statistics()

    def create_backtest_related_instance_wallet(self):
        self.wallet = Wallet(
            initial_amount=self.config.wallet_initial_amount,
            currency="USD"
        )

    def create_backtest_related_instance_timeline(self):
        self.timeline = BacktestTimeline(self)

    def create_backtest_related_instance_queue(self):
        self.queue = Queue()

    def create_backtest_related_instance_statistics(self):
        self.statistics = BacktestStatistics(
            initial_amount=self.config.wallet_initial_amount
        )

    def save_event(self, event):
        pass

    def save_backtest_to_database(self):

        BacktestModel.objects.create(
            created_at=datetime.now(),
            channel=self.config.channel,
            tag=self.config.tag,
            date_to=self.config.date_to,
            date_from=self.config.date_from,
            max_days_in_position=self.config.max_days_in_position,
            profit_result=self.wallet.amount-self.wallet.initial_amount,
            initial_amount=self.wallet.initial_amount,
            strategy_label=self.config.strategy_label,
            statistics=self.statistics.as_json(),
        )


class BacktestConfig:

    def __init__(self,
                 channel=None,
                 tag=None,
                 date_from=date_from,
                 date_to=date_to,
                 strategy=StrategyTakeProfit.PRESET_GREEDY_LOW,
                 strategy_label=StrategyTakeProfit.PRESET_GREEDY_LOW_LABEL,
                 amount_single_transaction=config.AMOUNT_SINGLE_TRANSACTION ,
                 max_days_in_position=config.TRANSACTION_DURATION,
                 wallet_initial_amount=config.WALLET_INITIAL_AMOUNT):
        self.channel = channel
        self.tag = tag
        self.wallet_initial_amount = wallet_initial_amount
        self.date_to = date_to
        self.date_from = date_from
        self.strategy = strategy
        self.strategy_label = strategy_label
        self.amount_single_transaction = amount_single_transaction
        self.max_days_in_position = max_days_in_position


class BacktestStatistics:

    def __init__(self, initial_amount, messages_to_analyse=0):
        self.initial_amount = initial_amount
        self.event_signal = 0
        self.events_amount = 0
        self.wallet_state = []
        self.realised_events_by_event_type = defaultdict(list)
        self.position_event_realised__ratio = defaultdict(int)
        self.closed_by_type__ratio = defaultdict(int)
        self.initial_pair_found_retries = []
        self.executed_events_amount = 0
        self.wallet_state_final = 0
        self.messages_to_analyse = messages_to_analyse
        self.messages_recognised_as_signal = 0
        self.messages_recognised_as_skip = 0
        self.messages_processed_to_decision = 0
        self.transaction_initial_pair_not_found = 0
        self.transaction_any_position_realisation_date_not_found = 0

    def on_event_realised(self, event, wallet):
        self.wallet_state.append({
            "date": event.execution_date,
            "type": type(event).__name__,
            "wallet_state": wallet.amount,
        })

    def on_position_event_realised(self, event_type):
        self.position_event_realised__ratio[event_type] += 1

    def on_transaction_closed(self, event_type):
        self.closed_by_type__ratio[event_type] += 1

    def add_event(self, event):
        self.realised_events_by_event_type[type(event).__name__].append(event.__repr__())

    def increment_messages_recognised_as_signal(self):
        self.messages_recognised_as_signal += 1

    def increment_messages_processed_to_decision(self):
        self.messages_processed_to_decision += 1

    def increment_transaction_initial_pair_not_found(self):
        self.transaction_initial_pair_not_found += 1

    def increment_transaction_any_position_realisation_date_not_found(self):
        self.transaction_any_position_realisation_date_not_found += 1

    def as_json(self):
        try:
            return {
                'events_amount': self.events_amount,
                'events_types': self.realised_events_by_event_type,
                'closed_by_type_ratio': self.closed_by_type__ratio,
                'position_events_realised_ratio': self.position_event_realised__ratio,
                'executed_events_amount': self.executed_events_amount,
                'wallet_state_final': self.wallet_state[-1]['wallet_state'],
                'messages_to_analyse': self.messages_to_analyse,
                'messages_processed_to_decision': self.messages_processed_to_decision,
                'messages_recognised_as_signal': self.messages_recognised_as_signal,
                'messages_recognised_as_skip': self.messages_to_analyse-self.messages_recognised_as_signal,
                'transaction_initial_pair_not_found': self.transaction_initial_pair_not_found,
                'transaction_any_position_realisation_date_not_found': self.transaction_any_position_realisation_date_not_found,
                'wallet_state': self.wallet_state,
            }
        except IndexError:
            logging.error('Nie zalapalo sie, trudno')


class BacktestMessagesFiller:
    filler_type = None

    def __init__(self, messages, backtest=None, type=None):
        self.messages = messages,
        self.backtest = backtest
        self.type = type

    def add_messages(self):
        raise NotImplementedError

    @staticmethod
    def is_message_between_date(message, date_from, date_to):
        return message['date'] < date_from or message['date'] > date_to


class BacktestMessagesFillerObjects(BacktestMessagesFiller):

    filler_type = MessageFillTypeChoices.OBJECTS

    def add_messages(self):
        self.backtest.add_messages_objects_signal_to_queue(
            self.messages, date_from=date_from, date_to=date_to
        )

    def add_messages_to_queue(self, messages_objects, date_from=None, date_to=None):

        for message in messages_objects:

            if self.is_message_between_date(date_from=date_from, date_to=date_to):
                continue

            message_obj = Message.objects.filter(
                id_universal=message['id_universal']
            ).order_by('-created_at').first()

            if message.is_message_type_signal():
                self.backtest.statistics.increment_messages_recognised_as_signal()

            message_event = events.EventMessageReceived(message_obj, self, tag=self.backtest.tag).event
            if message_event == None:
                continue

            self.backtest.save_event(message_event)
            self.backtest.queue.add(message_event)


class BacktestMessagesFillerRawMessages(BacktestMessagesFiller):

    filler_type = MessageFillTypeChoices.RAW

    def add_messages(self):
        self.add_messages_raw_to_queue(
            self.messages, date_from=date_from, date_to=date_to
        )

    def add_messages_raw_to_queue(self, raw_messages, date_from=None, date_to=None):

        for message_json in raw_messages:
            if self.is_message_between_date(message_json, date_from=date_from, date_to=date_to):
                continue

            message = RecogniseMessageManager.get_recognised_message_obj(message_json)
            message.status = choices.MessageStatusChoices.RECOGNIZED
            message.save()
            if message.type == choices.MessageTypeChoices.UNDEFINED:
                continue

            message_event = events.EventMessageReceived(message, self, tag=self.backtest.tag).event
            if message_event == None:
                continue

            self.backtest.save_event(message_event)
            self.backtest.queue.add(message_event)


BACKTEST_MESSAGES_FILLER_TYPE_MAPPER = {
    MessageFillTypeChoices.OBJECTS: BacktestMessagesFillerObjects,
    MessageFillTypeChoices.RAW: BacktestMessagesFillerRawMessages
}


class BacktestReport():

    def __init__(self):
        pass

    def preview(self):
        pass