import logging
from mongoengine import register_connection

from app.exceptions.process import DecisionSignalStopLossNotFound, InvalidTakeProfit, DecisionSignalAnyTakeProfitFound
from app.models.choices import TransactionStatusChoices
from app.models.transactions import Transaction
from database import connect_to_db, DB_BACKTEST, MONGO_HOST, MONGO_PORT, get_collection_for_database

PRE_BACKTEST_RECOGNISED = 'pre_backtest_recognised'
PRE_BACKTEST_PROCESSED = 'pre_backtest_processed'

report_name_recognised = 'recognise_lifestyle_pip_fx_2'  # Gdy tworzymy nowy raport recognision
process_signal_report_name_input = 'report2'  # Gdy tworzymy process signal weź na podstawie
process_signal_report_name_output= 'processed_bluecapital_fx_1'  # Gdy tworzymy nowy raport process


logger = logging.getLogger(__name__)


class ReportFetcher():

    def __init__(self) -> None:
        self.collection_recognised_messages = get_collection_for_database(PRE_BACKTEST_RECOGNISED)
        self.collection_processed_messages = get_collection_for_database(PRE_BACKTEST_PROCESSED)

    def get_prebacktest_processed_success(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one({'report_name': report_name})['success']

    def get_prebacktest_recognised_report(self, report_name=report_name_recognised):
        return self.collection_recognised_messages.find_one({'report_name': report_name})

    def get_prebacktest_processed_report(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one({'report_name': report_name})

    def get_prebacktest_processed_report_failures(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one({'report_name': report_name})['failures']

    def get_processed_failures_any_takeprofit(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one(
            {'report_name': report_name}
        )['failures'][DecisionSignalAnyTakeProfitFound.__name__]

    def get_processed_failures_stoploss(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one(
            {'report_name': report_name}
        )['failures'][DecisionSignalStopLossNotFound.__name__]

    def get_processed_failures_takeprofit(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one(
            {'report_name': report_name}
        )['failures'][InvalidTakeProfit.__name__]

    def get_processed_failures_exceptions(self, report_name=process_signal_report_name_output):
        return self.collection_processed_messages.find_one(
            {'report_name': report_name}
        )['failures'][Exception.__name__]


class ReportTransaction:

    def __init__(self, transaction_tag):
        connect_to_db(DB_BACKTEST)
        register_connection(DB_BACKTEST,
                            db=DB_BACKTEST, name=DB_BACKTEST,
                            host=MONGO_HOST, port=MONGO_PORT)
        self.transaction_tag = transaction_tag
        self.transactions = Transaction.objects.filter(tag=self.transaction_tag)
        self.amount = 1000

    def analyse(self):
        if not self.is_valid():
            return

        for transaction in self.transactions:
            pass

    def is_valid(self):
        for transaction in self.transactions:
            if transaction.status == TransactionStatusChoices.CLOSED:
                if transaction.take_profits[-1].is_closed == True and transaction.stop_loss.is_closed == True:
                    logger.info('Only one of stop loss or last take profit can be "closed"')
                    return False

