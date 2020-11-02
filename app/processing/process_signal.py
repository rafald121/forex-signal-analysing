import logging
import re

from app.exceptions.process import (
    DecisionSignalPairNotFound,
    DecisionSignalTypeUndefined,
    DecisionSignalAnyTakeProfitFound,
    DecisionSignalStopLossNotFound,
    IncorrectDecisionSignalTradeLevels,
    InvalidTakeProfit)
from app.models import choices
from app.models.choices import DecisionSignalTypeChoices
from app.models.decisions import DecisionSignal
from app.pairs import pairs_without_slash

logger = logging.getLogger(__file__)


class ProcessorSignalBase:

    @staticmethod
    def get_decision(message):
        raise NotImplementedError

    def get_pair(self, message):
        raise NotImplementedError

    def get_take_profits(self, message):
        raise NotImplementedError

    def get_stop_loss(self, message):
        raise NotImplementedError

    def get_type(self, message):
        raise NotImplementedError



class ProcessorSignalGaForex(ProcessorSignalBase):

    name = choices.ChannelNameChoices.GAFOREX
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return ([p for p in pairs_without_slash if p.lower() in message.text.lower()][0]).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [msg_part for msg_part in message_parts
                       if 'tp' in msg_part.lower() and 'http' not in msg_part.lower()]
        take_profits = []
        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        if not take_profits[-1]['is_last']:
            logger.error('Last take profit should be is_last = True')

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_sl_replace = re.compile('[sS][lL]')
        pattern_symbols_replace = re.compile('[-!: ]')
        pattern_number_of_pips_at_end = '(\([0-9]{1,3}\.?([0-9]{1})?\+pips\))$'   #(84+pips), (123+pips)

        message_parts = message.text.split("\n")
        if len(message_parts) > 1:
            message_sl = [msg_part for msg_part in message_parts if 'sl' in msg_part.lower()][0]

            price_formatted = re.sub(pattern_sl_replace, "", message_sl)
            price_formatted = re.sub(pattern_symbols_replace, '', price_formatted)
            price_formatted = re.sub(pattern_number_of_pips_at_end, '', price_formatted)

            try:
                price = float(price_formatted)
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_text=\n{message.text}. \n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError:
                    logger.error(f"\nError while converting message_text=\n{message.text}. \n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )

    @classmethod
    def replace_pair(cls, text, pair):
        return


class ProcessorSignalSureShotForex(ProcessorSignalBase):

    """
    TODO gdy będzie czas i chęci : processed_sure_shot_forex_1 - najnowszy raport
    """

    name = choices.ChannelNameChoices.SURE_SHOT_FOREX
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash if p.lower() in message.text.lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [msg_part for msg_part in message_parts
                       if 'tp' in msg_part.lower() and 'http' not in msg_part.lower()]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_sl_replace = re.compile('[sS][lL]')
        pattern_symbols_replace = re.compile('[-!:@– ]')
        pattern_number_of_pips_at_end = '(\([0-9]{1,3}\.?([0-9]{1})?\+pips\))$'   #(84+pips), (123+pips)
        pattern_stop_loss_relative_pips_amount = '[sS][lL]\ {1,5}\d{1,3}\ {1,5}pips'  # SL 50 pips

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [msg_part for msg_part in message_parts if 'sl' in msg_part.lower()][0]

            price_formatted = re.sub(pattern_sl_replace, "", message_sl)
            price_formatted = re.sub(pattern_symbols_replace, '', price_formatted)
            price_formatted = re.sub(pattern_number_of_pips_at_end, '', price_formatted)

            try:
                price = float(price_formatted)
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )


class ProcessorSignalLifestylePipsFx(ProcessorSignalBase):

    name = choices.ChannelNameChoices.LIFESTYLE_PIP_FX
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }
    take_profits_phrases = ['tp', 'take', 't/p']
    stop_loss_phrases = ['sl', 'stop', 's/l']

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash
                 if p.lower() in message.text.replace(' ', '').replace('/', '').lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [
            msg_part for msg_part in message_parts
            if bool(
                [phrase for phrase in cls.take_profits_phrases if phrase in msg_part.lower()]
            )
        ]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        # pattern_price_with_dot = re.compile('\W\d*\.\d*')
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [
                msg_part for msg_part in message_parts
                if bool(
                    [phrase for phrase in cls.stop_loss_phrases if phrase in msg_part.lower()]
                )
            ][0]

            price_formatted = pattern_price_with_dot.search(message_sl)
            try:
                price = float(price_formatted[0])
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )


class ProcessorSignalSmartTradeSolutions(ProcessorSignalBase):

    name = choices.ChannelNameChoices.SMART_TRADE_SOLUTIONS
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }
    take_profits_phrases = ['tp', 'take', 't/p']
    stop_loss_phrases = ['sl', 'stop', 's/l']

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash
                 if p.lower() in message.text.replace(' ', '').replace('/', '').lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [
            msg_part for msg_part in message_parts
            if bool(
                [phrase for phrase in cls.take_profits_phrases
                 if phrase in msg_part.lower() and 'https' not in msg_part.lower()]
            )
        ]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [
                msg_part for msg_part in message_parts
                if bool(
                    [phrase for phrase in cls.stop_loss_phrases if phrase in msg_part.lower()]
                )
            ][0]

            price_formatted = pattern_price_with_dot.search(message_sl)
            try:
                price = float(price_formatted[0])
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )


class ProcessorSignalBlueCapitalFx(ProcessorSignalBase):

    name = choices.ChannelNameChoices.BLUECAPITAL_FX
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }
    take_profits_phrases = ['tp', 'take', 't/p']
    stop_loss_phrases = ['sl', 'stop', 's/l']

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash
                 if p.lower() in message.text.replace(' ', '').replace('/', '').lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [
            msg_part for msg_part in message_parts
            if bool(
                [phrase for phrase in cls.take_profits_phrases
                 if phrase in msg_part.lower() and 'https' not in msg_part.lower()]
            )
        ]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [
                msg_part for msg_part in message_parts
                if bool(
                    [phrase for phrase in cls.stop_loss_phrases if phrase in msg_part.lower()]
                )
            ][0]

            price_formatted = pattern_price_with_dot.search(message_sl)
            try:
                price = float(price_formatted[0])
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )


class ProcessorSignalEuphoriaTrading(ProcessorSignalBase):

    name = choices.ChannelNameChoices.EUPHORIA_TRADING
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }
    take_profits_phrases = ['tp', 'take', 't/p']
    stop_loss_phrases = ['sl', 'stop', 's/l']

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            initial_price=cls.get_initial_price(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash
                 if p.lower() in message.text.replace(' ', '').replace('/', '').lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_initial_price(cls, message):
        sell_now_price_regex = "(([sS][eE][lL]{1,2})|([bB][uU][yY]))\s*([nN][oO][wW])\s*@?\s*(\d*\.?\d+)"
        sell_now_price_regex_compiled = re.compile(sell_now_price_regex)
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        try:
            sell_now_line = [
                msg_part for msg_part in message.text.split('\n')
                if bool(sell_now_price_regex_compiled.match(msg_part))
            ][0]
        except IndexError:
            logger.error(f'could not find sell now line in message_text={message.text}')
            return None

        try:
            price = float(
                pattern_price_with_dot.search(sell_now_line)[0]
            )
            return price
        except ValueError:
            logger.error(f'Could not get initial price from message text: \n' 
                         f'{message.text}')

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [
            msg_part for msg_part in message_parts
            if bool(
                [phrase for phrase in cls.take_profits_phrases if phrase in msg_part.lower()]
            )
        ]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [
                msg_part for msg_part in message_parts
                if bool(
                    [phrase for phrase in cls.stop_loss_phrases if phrase in msg_part.lower()]
                )
            ][0]

            price_formatted = pattern_price_with_dot.search(message_sl)
            try:
                price = float(price_formatted[0])
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )


class ProcessorSignalPipsMeUp(ProcessorSignalBase):

    name = choices.ChannelNameChoices.PIPSMEUP
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }
    take_profits_phrases = ['tp', 'take', 't/p']
    stop_loss_phrases = ['sl', 'stop', 's/l']

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            initial_price=cls.get_initial_price(message),
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash
                 if p.lower() in message.text.replace(' ', '').replace('/', '').lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_initial_price(cls, message):
        sell_now_price_regex = "(([sS][eE][lL]{1,2})|([bB][uU][yY]))\s*([nN][oO][wW])\s*@?\s*(\d*\.?\d+)"
        sell_now_price_regex_compiled = re.compile(sell_now_price_regex)
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        try:
            sell_now_line = [
                msg_part for msg_part in message.text.split('\n')
                if bool(sell_now_price_regex_compiled.match(msg_part))
            ][0]
        except IndexError:
            logger.error(f'could not find sell now line in message_text={message.text}')
            return None

        try:
            price = float(
                pattern_price_with_dot.search(sell_now_line)[0]
            )
            return price
        except ValueError:
            logger.error(f'Could not get initial price from message text: \n' 
                         f'{message.text}')

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [
            msg_part for msg_part in message_parts
            if bool(
                [phrase for phrase in cls.take_profits_phrases if phrase in msg_part.lower()]
            )
        ]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [
                msg_part for msg_part in message_parts
                if bool(
                    [phrase for phrase in cls.stop_loss_phrases if phrase in msg_part.lower()]
                )
            ][0]

            price_formatted = pattern_price_with_dot.search(message_sl)
            try:
                price = float(price_formatted[0])
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )


class ProcessorSignalFxScorpions(ProcessorSignalBase):

    name = choices.ChannelNameChoices.FX_SCORPIONS
    type_mapping = {
        DecisionSignalTypeChoices.LONG: "buy",
        DecisionSignalTypeChoices.SHORT: "sell"
    }
    take_profits_phrases = ['tp', 'take', 't/p']
    stop_loss_phrases = ['sl', 'stop', 's/l']

    @classmethod
    def get_decision(cls, message) -> DecisionSignal:
        decision = DecisionSignal(
            date=message.date,
            processor_used=cls.name,
            message=message,
            pair=cls.get_pair(message),
            type=cls.get_type(message),
            initial_price=None,
            take_profits=cls.get_take_profits(message),
            stop_loss=cls.get_stop_loss(message),
        ).save()

        return decision.save()

    @classmethod
    def get_pair(cls, message):
        try:
            return (
                [p for p in pairs_without_slash
                 if p.lower() in message.text.replace(' ', '').replace('/', '').lower()][0]
            ).upper()
        except IndexError:
            if "gold" in message.text.lower():
               return "XAUUSD"
            print(f"Not found any pair in message_text={message.text}")
            raise DecisionSignalPairNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_initial_price(cls, message):
        sell_now_price_regex = "(([sS][eE][lL]{1,2})|([bB][uU][yY]))\s*([nN][oO][wW])\s*@?\s*(\d*\.?\d+)"
        sell_now_price_regex_compiled = re.compile(sell_now_price_regex)
        pattern_price_with_dot = re.compile('(\d*\.?\d+){2}')

        try:
            sell_now_line = [
                msg_part for msg_part in message.text.split('\n')
                if bool(sell_now_price_regex_compiled.match(msg_part))
            ][0]
        except IndexError:
            logger.error(f'could not find sell now line in message_text={message.text}')
            return None

        try:
            price = float(
                pattern_price_with_dot.search(sell_now_line)[0]
            )
            return price
        except ValueError:
            logger.error(f'Could not get initial price from message text: \n' 
                         f'{message.text}')

    @classmethod
    def get_take_profits(cls, message):
        message_parts = message.text.split("\n")
        message_tps = [
            msg_part for msg_part in message_parts
            if bool(
                [phrase for phrase in cls.take_profits_phrases if phrase in msg_part.lower()]
            )
        ]
        take_profits = []

        for order_number, tp in enumerate(message_tps):
            try:
                take_profit = {
                    'order_number': order_number + 1,
                    'price': cls.get_take_profit_from_tp_part(tp),
                    'is_last': message_tps.index(tp) == len(message_tps) - 1
                }
                take_profits.append(take_profit)
            except ValueError as e:
                logger.error(f"Error while converting message_text=\n{message.text}\n "
                             f"Error={e}")
                continue

        if not take_profits:
            raise DecisionSignalAnyTakeProfitFound(
                message.get_universal_id(), message.text
            )

        return take_profits

    @classmethod
    def get_take_profit_from_tp_part(cls, tp):

        if 'open' in tp.lower():
            return -1

        pattern_price_with_dot = re.compile('([\d*]+\.?\d+)')

        tp_price = pattern_price_with_dot.search(tp)
        if tp_price:
            price = float(tp_price[0])
            if price in [1,2,3,4,5,6]:
                logger.error(f"ARE WE SURE THAT WE PROCESSED TP CORRECTLY? "
                             f"price={price}, tp={tp}")
            return price
        else:
            raise InvalidTakeProfit(tp)

    @classmethod
    def get_stop_loss(cls, message):
        pattern_price_with_dot = re.compile('([\d*]+\.?\d+)')

        message_parts = message.text.split("\n")

        if len(message_parts) > 1:

            message_sl = [
                msg_part for msg_part in message_parts
                if bool(
                    [phrase for phrase in cls.stop_loss_phrases if phrase in msg_part.lower()]
                )
            ][0]

            price_formatted = pattern_price_with_dot.search(message_sl)
            try:
                price = float(price_formatted[0])
                return {'price': price}
            except ValueError as e:
                logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                             f"message_text=\n{message.text}\n"
                             f"Error={e}")
                raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)
        else:
            pattern_stop_loss_in_one_line = re.compile('[Ss][Ll]\s*[:\-! ]{1}\s*\d*\.?\d*')
            pattern_stop_loss = re.compile('[\d]*\.\d*')
            sl_and_price = pattern_stop_loss_in_one_line.search(message.text)
            if sl_and_price:
                stop_loss = sl_and_price[0]
                stop_loss_price = pattern_stop_loss.search(stop_loss)[0]
                try:
                    price = float(stop_loss_price)
                    return {'price': price}
                except ValueError as e:
                    logger.error(f"\nError while converting message_id={message.get_universal_id()}\n"
                                 f"message_text=\n{message.text}\n"
                                 f"Error={e}")
                    raise DecisionSignalStopLossNotFound(message.get_universal_id(), message.text)

    @classmethod
    def get_type(cls, message):
        message_text_lower = message.text.lower()

        if "sell" in message_text_lower:
            return DecisionSignalTypeChoices.SHORT
        elif "buy" in message_text_lower:
            return DecisionSignalTypeChoices.LONG
        else:
            raise DecisionSignalTypeUndefined(
                message.get_universal_id(),
                message.text
            )




MAPPING_PROCESS_SIGNAL = {
    choices.ChannelNameChoices.GAFOREX: ProcessorSignalGaForex,
    choices.ChannelNameChoices.SURE_SHOT_FOREX: ProcessorSignalSureShotForex,
    choices.ChannelNameChoices.LIFESTYLE_PIP_FX: ProcessorSignalLifestylePipsFx,
    choices.ChannelNameChoices.SMART_TRADE_SOLUTIONS: ProcessorSignalSmartTradeSolutions,
    choices.ChannelNameChoices.BLUECAPITAL_FX: ProcessorSignalBlueCapitalFx,
    choices.ChannelNameChoices.EUPHORIA_TRADING: ProcessorSignalEuphoriaTrading,
    choices.ChannelNameChoices.PIPSMEUP: ProcessorSignalPipsMeUp,
    choices.ChannelNameChoices.FX_SCORPIONS: ProcessorSignalFxScorpions
}


class ProcessSignalManager:

    @classmethod
    def get_decision_signal(cls, message) -> DecisionSignal or None:

        processor = MAPPING_PROCESS_SIGNAL.get(message.channel.name, None)

        if processor:
            decision_signal = processor.get_decision(message)
            if not decision_signal.take_profits or not decision_signal.stop_loss:
                raise IncorrectDecisionSignalTradeLevels(
                    message.get_universal_id(), message.text
                )
            message.status = choices.MessageStatusChoices.PROCESSED
            message.save()
            return decision_signal
        else:
            logger.error("Processor for channel={} not found".format(message.channel))
