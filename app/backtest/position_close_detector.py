import logging
import datetime
from collections import OrderedDict

from mongoengine import DoesNotExist

from app.backtest import config
from app.models.choices import DecisionSignalTypeChoices

from app.models.historic import HistoricRow

CROSS_UP = "cross_up"
CROSS_DOWN = "cross_down"

TAKE_PROFIT = "take_profit"
STOP_LOSS = "stop_loss"

UNDEFINED = 'undefined'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_initial_price_of_nearest_historic_row_date_for_pair(pair, date):
    price = None
    retries = 0
    date_query = datetime.datetime(
        year=date.year,
        month=date.month,
        day=date.day,
        hour=date.hour,
        minute=date.minute
    )

    while price is None:
        try:
            historic_row = HistoricRow.objects.get(date=date_query, pair=pair)
            price = (historic_row.low + historic_row.high)/2
        except DoesNotExist:
            if retries == config.POSITION_DETECTOR_MAX_RETRIES:
                logger.error(f'Initial price not found for pair={pair} and date={date}')
                return None, retries
            retries += 1
            date = date + datetime.timedelta(minutes=1)

    return price, retries


class PositionCloseDetector:

    NOT_FOUND = 'NOT_FOUND'

    @classmethod
    def detect(cls, decision_signal):
        result_take_profits, result_stop_loss = OrderedDict(), OrderedDict()

        date_from = decision_signal.date
        take_profits = decision_signal.take_profits
        stop_loss = decision_signal.stop_loss
        type = decision_signal.type
        pair = decision_signal.pair

        direction_tp = cls.get_analysing_direction(type, TAKE_PROFIT)
        direction_sl = cls.get_analysing_direction(type, STOP_LOSS)

        for take_profit in take_profits:
            if take_profit is None:
                logger.error(
                    f"Error occured. Take_profit is null. "
                    f"Decision_signal.pk={decision_signal.pk}"
                )
                result_take_profits[take_profit['order_number']] = None
                continue

            result_take_profits[take_profit['order_number']] = cls.get_date_of_execution(
                take_profit, pair, date_from, direction=direction_tp
            )

        if stop_loss is None:
            logger.error(f"Error occured. Stop_loss is null. "
                         f"Decision_signal.pk={decision_signal.pk}")
            result_stop_loss = None
        else:
            result_stop_loss = cls.get_date_of_execution(
                stop_loss, pair, date_from, direction=direction_sl
            )

        return result_take_profits, result_stop_loss

    @classmethod
    def get_date_of_execution(cls, position, pair, date_from, direction):
        if position['price'] is None:
            logger.error(f"Price is none for position.pk: {position} ")
            return cls.NOT_FOUND

        date_to = date_from+datetime.timedelta(days=config.FETCH_DATES_UNTIL_AMOUNT_DAYS)

        historical_rows_for_pairs = HistoricRow.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
            pair=pair
        )

        for historic_row in historical_rows_for_pairs:
            if direction == CROSS_UP:
                if historic_row.high > position['price']:
                    return historic_row.date
                continue
            if direction == CROSS_DOWN:
                if historic_row.low < position['price']:
                    return historic_row.date
                continue

        return cls.NOT_FOUND

    @classmethod
    def get_analysing_direction(self, transaction_type, transaction_position_type):
        if transaction_type == DecisionSignalTypeChoices.LONG:
            if transaction_position_type == TAKE_PROFIT:
                return CROSS_UP
            return CROSS_DOWN
        elif transaction_type == DecisionSignalTypeChoices.SHORT:
            if transaction_position_type == TAKE_PROFIT:
                return CROSS_DOWN
            return CROSS_UP
        return UNDEFINED