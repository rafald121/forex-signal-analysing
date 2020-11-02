import logging

from app.exceptions.backtest import InsufficientFundsException


logger = logging.getLogger(__name__)


class Wallet:

    def __init__(self, initial_amount, currency, backtest=None):
        self.initial_amount = initial_amount
        self.currency = currency
        self.amount = initial_amount
        self.backtest = backtest

    def on_transaction_open(self):
        if self.amount - self.backtest.config.amount_single_transaction > 0:
            self.amount -= self.backtest.config.amount_single_transaction
            logger.info(f'Amount we get from wallet: {self.backtest.amount_single_transaction} '
                        f'Now in our wallet we have: {self.amount}')
            return self.backtest.config.amount_single_transaction
        else:
            raise InsufficientFundsException(self.amount)

    def on_transaction_position_realised(self, amount):
        logger.info(f"We add to our wallet: {amount}."
                    f"Now in our wallet we have: {self.amount+amount}")
        self.amount += amount

    def on_transaction_refund_back(self, amount):
        """ in case of not found initial price we already refund funds"""
        self.amount += float(amount)

    def get_state(self):
        return self.amount