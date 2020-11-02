import logging
from datetime import datetime

from mongoengine import register_connection, DoesNotExist

from app.backtest.backtest import Backtest, BACKTEST_MESSAGES_FILLER_TYPE_MAPPER, BacktestConfig
from app.exceptions.process import (
    DecisionSignalTypeUndefined,
    DecisionSignalAnyTakeProfitFound,
    InvalidTakeProfit,
    DecisionSignalStopLossNotFound,
    IncorrectDecisionSignalTradeLevels
)
from app.mappings import MAPPING_NAME_TO_CHAT_ID
from app.models.channels import Channel
from app.models.decisions import DecisionSignal
from app.models.messages import Message, RawMessage
from app.models.choices import MessageTypeChoices, ChannelNameChoices, MessageFillTypeChoices
from app.processing.process_signal import MAPPING_PROCESS_SIGNAL
from app.processing.recognise import RecogniseMessageManager
from backtest import config
from backtest.reports.reports_fetcher import ReportFetcher
from database import connect_to_db, DB_BACKTEST, MONGO_HOST, MONGO_PORT, get_collection_for_database


logger = logging.getLogger(__name__)


PRE_BACKTEST_RECOGNISED = 'pre_backtest_recognised'
PRE_BACKTEST_PROCESSED = 'pre_backtest_processed'

channel = ChannelNameChoices.BLUECAPITAL_FX
report_version_recognise = 1
report_version_process = 1
report_version_backtest = 3
report_name_recognised = f'recognise_{channel}_{report_version_recognise}'  # Gdy tworzymy nowy raport recognision
process_signal_report_name_input = report_name_recognised  # Gdy tworzymy process signal weź na podstawie
process_signal_report_name_output= f'processed_{channel}_{report_version_process}'  # Gdy tworzymy nowy raport process
backtest_report_name_output= f'backtest_{channel}_{report_version_backtest}'  # Gdy tworzymy nowy raport process


class PreBacktest():

    def __init__(self, analysed_chat_id, analysed_chat_name,
                 recognise_report_name=None,
                 recognise=False,
                 process_signal=False,
                 process_signal_report_name_input=None,
                 process_signal_report_name_output='report_process_signal',
                 run_backtest=False,
                 run_backtest_report_name_input=process_signal_report_name_output,
                 wallet_initial_amount=config.WALLET_INITIAL_AMOUNT):

        connect_to_db()
        register_connection(DB_BACKTEST,
                            db=DB_BACKTEST, name=DB_BACKTEST,
                            host=MONGO_HOST, port=MONGO_PORT)

        if recognise is False and process_signal_report_name_input is None:
            logger.error('Whence do you want to load messages to process ?'
                         'You have to provide initial process_signal_report_name_input '
                         'if recognise=False')
            return

        self.channel = self.get_or_create_channel(analysed_chat_id, analysed_chat_name)

        if recognise:
            prebacktest_recognise = PreBacktestRecognise(
                self.channel.channel_id, analysed_chat_name, recognise_report_name
            )
            self.report_recognision = prebacktest_recognise.recognise()

        if process_signal:
            if hasattr(self, 'report_recognision'):
                recognised_messages_signal = self.report_recognision[MessageTypeChoices.SIGNAL]
            else:
                collection = get_collection_for_database(PRE_BACKTEST_RECOGNISED)
                recognised_messages_signal_report = collection.find_one({
                    'report_name': process_signal_report_name_input
                })
                recognised_messages_signal = recognised_messages_signal_report[MessageTypeChoices.SIGNAL]

            prebacktest_process = PreBacktestProcessSignal(
                recognised_messages_signal,
                channel_name=self.channel.name,
                report_name=process_signal_report_name_output
            )
            prebacktest_process.process()

        if run_backtest:
            messages_processed_successfully = ReportFetcher().get_prebacktest_processed_success(
                run_backtest_report_name_input
            )
            messages_filler = BACKTEST_MESSAGES_FILLER_TYPE_MAPPER[MessageFillTypeChoices.OBJECTS](
                messages_processed_successfully
            )
            backtest_config = BacktestConfig(
                wallet_initial_amount=wallet_initial_amount
            )
            backtest = Backtest(
                messages_filler=messages_filler,
                config=backtest_config
            )
            backtest.create_backtest_related_instances()
            backtest.fill_messages()
            backtest.run_analysing()
            backtest.save_backtest_to_database()

    @staticmethod
    def get_or_create_channel(chat_id, chat_name):
        try:
            return Channel.objects.get(name=chat_name)
        except DoesNotExist:
            return Channel.objects.create(
                channel_id=chat_id,
                name=chat_name
            )


class PreBacktestRecognise():

    def __init__(self, chat_id, analysed_chat_name, report_name='default_name'):
        self.analysed_chat_name = analysed_chat_name
        self.report_name = report_name

        self.collection_recognised_messages = get_collection_for_database(PRE_BACKTEST_RECOGNISED)
        self.raw_messages = RawMessage.objects.filter(chat_id=chat_id)

    def recognise(self):
        report = {
            'initial_date': datetime.now(),
            'channel_name': self.analysed_chat_name,
            'report_name': self.report_name,
            MessageTypeChoices.SKIP: [],
            MessageTypeChoices.SIGNAL: [],
            MessageTypeChoices.SIGNAL_EXTRA: [],
            MessageTypeChoices.CORRECTION: [],
            MessageTypeChoices.UNDEFINED: []
        }

        for message in self.raw_messages:
            try:
                message_recognised = RecogniseMessageManager.get_recognised_message_obj(message)
            except Exception:
                logger.exception(f"Error occurred while recognising message object. "
                                 f"Message_uuid={message.uuid}")
                continue

            message_recognised_json = message_recognised.to_json_representation()

            if message_recognised.type == MessageTypeChoices.SKIP:
                report[message_recognised.type].append(message_recognised_json)

            elif message_recognised.type == MessageTypeChoices.SIGNAL:
                report[message_recognised.type].append(message_recognised_json)

            elif message_recognised.type == MessageTypeChoices.SIGNAL_EXTRA:
                report[message_recognised.type].append(message_recognised_json)

            elif message_recognised.type == MessageTypeChoices.CORRECTION:
                report[message_recognised.type].append(message_recognised_json)

            elif message_recognised.type == MessageTypeChoices.UNDEFINED:
                report[message_recognised.type].append(message_recognised_json)

        self.collection_recognised_messages.insert_one(report)
        return report


class PreBacktestProcessSignal():

    def __init__(self, recognised_messages_signal, channel_name, report_name='default') -> None:
        self.collection_processed_messages = get_collection_for_database(PRE_BACKTEST_PROCESSED)
        self.channel_name = channel_name
        self.report_name = report_name
        self.recognised_messages_signal = recognised_messages_signal

    def process(self):
        report = {
            'initial_date': datetime.now(),
            'report_name': self.report_name,
            'channel_name': self.channel_name,
            'success': [],
            'failures': {
                IncorrectDecisionSignalTradeLevels.__name__: [],
                DecisionSignalTypeUndefined.__name__: [],
                DecisionSignalAnyTakeProfitFound.__name__: [],
                InvalidTakeProfit.__name__: [],
                DecisionSignalStopLossNotFound.__name__: [],
                Exception.__name__: []
            }
        }
        channel_name = self.recognised_messages_signal[0]['channel']['name']
        processor = MAPPING_PROCESS_SIGNAL.get(channel_name)

        for messsage in self.recognised_messages_signal:
            messsage_object = Message.objects \
                .filter(id_universal=messsage['id_universal']) \
                .order_by('-created_at').first()
            try:
                decision = processor.get_decision(messsage_object)
                if isinstance(decision, DecisionSignal):
                    report['success'].append(messsage)
                else:
                    print("SHOULDN BE HERE!!!11")
            except IncorrectDecisionSignalTradeLevels:
                report['failures'][IncorrectDecisionSignalTradeLevels.__name__].append(messsage)
            except DecisionSignalTypeUndefined:
                report['failures'][DecisionSignalTypeUndefined.__name__].append(messsage)
            except DecisionSignalAnyTakeProfitFound:
                report['failures'][DecisionSignalAnyTakeProfitFound.__name__].append(messsage)
            except InvalidTakeProfit:
                report['failures'][InvalidTakeProfit.__name__].append(messsage)
            except DecisionSignalStopLossNotFound:
                report['failures'][DecisionSignalStopLossNotFound.__name__].append(messsage)
            except Exception as e:
                report['failures'][Exception.__name__].append({
                    'message': messsage,
                    'error_message': str(e)
                })

        self.collection_processed_messages.insert_one(report)
        return report


chats = [
    {'title': 'Forexelliotwave group', 'username': None, 'id': 1269026174},
    {'title': 'Sure Shot Forex', 'username': 'sureshotforex', 'id': 1127289760},
    {'title': '🎌FX ScöŕpìoNs🎌', 'username': None, 'id': 1269006602},
    {'title': 'EZ Profit Pips Free Signals', 'username': 'EZProfitPips', 'id': 1261909982},
    {'title': 'Forex Analysis by PaxForex', 'username': 'paxforex', 'id': 1082558830},
    {'title': 'ProFx Analysis Academy', 'username': None, 'id': 1392466168},
    {'title': 'KijunFX Scalper', 'username': 'KijunFXScalper', 'id': 1386485558},
    {'title': 'SMART TRADE SOLUTIONS💱', 'username': None, 'id': 1388795077},
    {'title': 'Pipsmeup', 'username': 'pipsmeupp', 'id': 1192184495},
    {'title': 'ELEMENTARYFX', 'username': 'ElementaryFX', 'id': 1127198630},
    {'title': 'Lifestyle Pips FX', 'username': 'lifestylepips', 'id': 1449086607},
    {'title': '‼️ GA Forex Signals ‼️', 'username': 'GASignals', 'id': 1109190126},
    {'title': 'Market Profile - Forex Signals', 'username': 'marketprof', 'id': 1145131427},
    {'title': 'Euphoria Trading', 'username': 'euphoriatrading', 'id': 1259691957},
    {'title': 'BlueCapitalFX - Signals🏛', 'username': 'bluecapitalfxsignals', 'id': 1240285626}
]

PreBacktest(MAPPING_NAME_TO_CHAT_ID.get(channel), channel,
            recognise=False,
            recognise_report_name=report_name_recognised,
            process_signal=False,
            process_signal_report_name_input=process_signal_report_name_input,
            process_signal_report_name_output=process_signal_report_name_output,
            run_backtest=True,
            run_backtest_report_name_input=process_signal_report_name_output,
            wallet_initial_amount=config.WALLET_INITIAL_AMOUNT
            )
