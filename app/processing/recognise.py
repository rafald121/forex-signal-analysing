from datetime import datetime
from dateutil import parser

import logging

from mongoengine import DoesNotExist, MultipleObjectsReturned

from app import mappings, pairs
from app.exceptions.recognise import MoreThanOneMessageTypeHasBeenRecognised, MoreThanOnePairFound
from app.models import choices
from app.models.channels import Channel
from app.models.choices import MessageTypeChoices, MessageSignalTypeChoices
from app.models.messages import Message
from app.processing.process_correction import ProcessorCorrectionGaForex

logger = logging.getLogger(__file__)


class RecognsiseProcessorBase:

    name = None

    @staticmethod
    def get_recognised_message_type(message):
        raise NotImplementedError

    def is_message_signal(self, text) -> bool:
        raise NotImplementedError

    def is_message_correction(self, text) -> bool:
        raise NotImplementedError

    def is_message_skip(self, text) -> bool:
        raise NotImplementedError

    def get_id_internal(self, message):
        raise NotImplementedError

    def get_channel(self, message):
        raise NotImplementedError

    def get_text(self, message):
        raise NotImplementedError

    def get_date(self, message):
        raise NotImplementedError

    def get_type(self, message):
        raise NotImplementedError

    def get_status(self, message):
        raise NotImplementedError

    def get_text_raw(self, message):
        raise NotImplementedError

    def get_quoted_message(self, message):
        raise NotImplementedError

    def get_amount_and_pairs_from_text(self, text):
        found_pairs = [pair
                       for pair in pairs.pairs_without_slash_lower
                       if pair in text.replace('/', '').lower()]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            return 0, None


class RecogniseProcessorGaForex(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.GAFOREX

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""

        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        ).save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)

        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = super().get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        return ('buy' in text_lower or 'sell' in text_lower) and \
               ('tp' in text_lower and 'sl' in text_lower)

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorSureShotSignal(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.SURE_SHOT_FOREX

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        ).save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = super().get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        return ('buy' in text_lower or 'sell' in text_lower) and \
               ('tp' in text_lower and 'sl' in text_lower)

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorLifestylePipsFx(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.LIFESTYLE_PIP_FX

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        )
        message.save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = cls.get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        take_profits_phrases = ['tp', 'take', 't/p']
        stop_loss_phrases = ['sl', 'stop', 's/l']
        is_take_profit = [phrase for phrase in take_profits_phrases if phrase in text_lower]
        is_stop_loss = [phrase for phrase in stop_loss_phrases if phrase in text_lower]
        return ('buy' in text_lower or 'sell' in text_lower) and \
               bool(is_take_profit) and \
               bool(is_stop_loss)

    @classmethod
    def get_amount_and_pairs_from_text(cls, message_text):
        found_pairs = [
            pair for pair in pairs.pairs_without_slash_lower
            if pair in message_text.replace(' ', '').replace('/', '').lower()
        ]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            return 0, None

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorSmartTradeSolutions(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.SMART_TRADE_SOLUTIONS

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        )
        message.save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            logger.error(f"Exception, look at this")
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = cls.get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        take_profits_phrases = ['tp', 'take', 't/p']
        stop_loss_phrases = ['sl', 'stop', 's/l']
        is_take_profit = [phrase for phrase in take_profits_phrases if phrase in text_lower]
        is_stop_loss = [phrase for phrase in stop_loss_phrases if phrase in text_lower]
        return ('buy' in text_lower or 'sell' in text_lower) and \
               bool(is_take_profit) and \
               bool(is_stop_loss)

    @classmethod
    def get_amount_and_pairs_from_text(cls, message_text):
        found_pairs = [
            pair for pair in pairs.pairs_without_slash_lower
            if pair in message_text.replace(' ', '').replace('/', '').lower()
        ]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            if 'gold' in message_text.lower():
                return 1, 'XAUUSD'
            return 0, None

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorBlueCapitalFx(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.BLUECAPITAL_FX

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        )
        message.save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = cls.get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        take_profits_phrases = ['tp', 'take', 't/p']
        stop_loss_phrases = ['sl', 'stop', 's/l']
        is_take_profit = [phrase for phrase in take_profits_phrases if phrase in text_lower]
        is_stop_loss = [phrase for phrase in stop_loss_phrases if phrase in text_lower]
        return ('buy' in text_lower or 'sell' in text_lower) and \
               bool(is_take_profit) and \
               bool(is_stop_loss)

    @classmethod
    def get_amount_and_pairs_from_text(cls, message_text):
        found_pairs = [
            pair for pair in pairs.pairs_without_slash_lower
            if pair in message_text.replace(' ', '').replace('/', '').lower()
        ]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            if 'gold' in message_text.lower():
                return 1, 'XAUUSD'
            return 0, None

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorEuphoriaTrading(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.EUPHORIA_TRADING

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        )
        message.save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = cls.get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        take_profits_phrases = ['tp', 'take', 't/p']
        stop_loss_phrases = ['sl', 'stop', 's/l']
        is_take_profit = [phrase for phrase in take_profits_phrases if phrase in text_lower]
        is_stop_loss = [phrase for phrase in stop_loss_phrases if phrase in text_lower]
        return ('buy' in text_lower or 'sell' in text_lower) and \
               bool(is_take_profit) and \
               bool(is_stop_loss)

    @classmethod
    def get_amount_and_pairs_from_text(cls, message_text):
        found_pairs = [
            pair for pair in pairs.pairs_without_slash_lower
            if pair in message_text.replace(' ', '').replace('/', '').lower()
        ]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            if 'gold' in message_text.lower():
                return 1, 'XAUUSD'
            return 0, None

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorPipsMeUp(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.PIPSMEUP

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        )
        message.save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = cls.get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        take_profits_phrases = ['tp', 'take', 't/p']
        stop_loss_phrases = ['sl', 'stop', 's/l']
        is_take_profit = [phrase for phrase in take_profits_phrases if phrase in text_lower]
        is_stop_loss = [phrase for phrase in stop_loss_phrases if phrase in text_lower]
        return ('buy' in text_lower or 'sell' in text_lower) and \
               bool(is_take_profit) and \
               bool(is_stop_loss)

    @classmethod
    def get_amount_and_pairs_from_text(cls, message_text):
        found_pairs = [
            pair for pair in pairs.pairs_without_slash_lower
            if pair in message_text.replace(' ', '').replace('/', '').lower()
        ]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            if 'gold' in message_text.lower():
                return 1, 'XAUUSD'
            return 0, None

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]


class RecogniseProcessorFxScorpions(RecognsiseProcessorBase):

    name = choices.ChannelNameChoices.FX_SCORPIONS

    @classmethod
    def get_recognised_message_type(cls, message_json):
        """logic that recognise message and decide what type of message it is"""
        message = Message(
            id_internal=cls.get_id_internal(message_json),
            channel=cls.get_channel(message_json),
            text=cls.get_text(message_json),
            text_raw=cls.get_text_raw(message_json),
            date=cls.get_date(message_json),
            type=cls.get_message_type_from_message(message_json),
            status=choices.MessageStatusChoices.RECOGNIZED,
            quoted_message=cls.get_quoted_message(message_json)
        )
        message.save()
        return message

    @classmethod
    def get_message_type_from_message(cls, message):
        if not message['text']:
            logger.error(f"Message(uuid={message.get_universal_id()}) is blank")
            return choices.MessageTypeChoices.SKIP

        is_signal, signal_type = cls.is_message_signal(message)
        is_correction = cls.is_message_correction(message)
        is_skip = cls.is_message_skip(message)

        # only for tests to see if such a situation can ever occur
        if [is_signal, is_correction, is_skip].count(True) > 1:
            raise MoreThanOneMessageTypeHasBeenRecognised

        if is_signal:
            if signal_type == MessageSignalTypeChoices.SIGNAL_ONE_PAIR:
                return choices.MessageTypeChoices.SIGNAL
            if signal_type == MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS:
                return choices.MessageTypeChoices.SIGNAL_EXTRA
        elif is_correction:
            return choices.MessageTypeChoices.CORRECTION
        elif is_skip:
            return choices.MessageTypeChoices.SKIP
        else:
            return choices.MessageTypeChoices.UNDEFINED

    @classmethod
    def is_message_signal(cls, message):
        if getattr(message, 'reply_to_msg_id', None) is not None:
            return False, None

        text = cls.get_text(message)
        if not text:
            return False, None

        is_message_text_signal, signal_type = cls.is_message_text_signal(message)
        return is_message_text_signal, signal_type

    @classmethod
    def is_message_text_signal(cls, message):
        message_text = cls.get_text(message)
        if cls.is_signal_condition_true(message_text):
            found_pairs_amount, pairs = cls.get_amount_and_pairs_from_text(message_text)
            if found_pairs_amount == 1:
                return True, MessageSignalTypeChoices.SIGNAL_ONE_PAIR
            if found_pairs_amount > 1:
                return True, MessageSignalTypeChoices.SIGNAL_TWO_OR_MORE_PAIRS
        return False, None

    @classmethod
    def is_signal_condition_true(cls, text):
        text_lower = text.lower()
        take_profits_phrases = ['tp', 'take', 't/p']
        stop_loss_phrases = ['sl', 'stop', 's/l']
        is_take_profit = [phrase for phrase in take_profits_phrases if phrase in text_lower]
        is_stop_loss = [phrase for phrase in stop_loss_phrases if phrase in text_lower]
        return ('buy' in text_lower or 'sell' in text_lower) and \
               bool(is_take_profit) and \
               bool(is_stop_loss)

    @classmethod
    def get_amount_and_pairs_from_text(cls, message_text):
        found_pairs = [
            pair for pair in pairs.pairs_without_slash_lower
            if pair in message_text.replace(' ', '').replace('/', '').lower()
        ]
        if len(found_pairs) > 1:
            return len(found_pairs), found_pairs
        elif len(found_pairs) == 1:
            return 1, found_pairs[0]
        else:
            if 'gold' in message_text.lower():
                return 1, 'XAUUSD'
            return 0, None

    @classmethod
    def is_message_correction(cls, message):
        # TODO MESSAGE PATTERNS
        text = cls.get_text(message)
        return ProcessorCorrectionGaForex.is_correction_action_hold(message)[0]

    @classmethod
    def is_message_skip(cls, message):
        words_set1 = ['running', 'pop']
        message_text = message['text']
        if not message_text:
            return True
        for word in words_set1:
            if word not in message['text']:
                return False
        return True

    @classmethod
    def get_id_internal(cls, message):
        return str(message['message_id'])

    @classmethod
    def get_channel(cls, message):
        return Channel.objects.get(name=mappings.MAPPING_CHAT_ID_TO_NAME[message['chat_id']])

    @classmethod
    def get_text(cls, message):
        return message['text']

    @classmethod
    def get_text_raw(cls, message):
        return message['raw_text']

    @classmethod
    def get_date(cls, message):
        if isinstance(message['date'], datetime):
            return message['date']
        else:
            return parser.parse(message['date'])

    @classmethod
    def get_quoted_message(self, message):
        reply_to_msg_pk = message['reply_to_msg_id']
        try:
            quoted_message = Message.objects.get(id_internal=str(reply_to_msg_pk))
            return quoted_message
        except DoesNotExist:
            return None
        except MultipleObjectsReturned:
            return Message.objects.filter(id_internal=str(reply_to_msg_pk))[0]



MAPPING_RECOGNISE = {
    choices.ChannelNameChoices.GAFOREX: RecogniseProcessorGaForex,
    choices.ChannelNameChoices.SURE_SHOT_FOREX: RecogniseProcessorSureShotSignal,
    choices.ChannelNameChoices.LIFESTYLE_PIP_FX: RecogniseProcessorLifestylePipsFx,
    choices.ChannelNameChoices.SMART_TRADE_SOLUTIONS: RecogniseProcessorSmartTradeSolutions,
    choices.ChannelNameChoices.BLUECAPITAL_FX: RecogniseProcessorBlueCapitalFx,
    choices.ChannelNameChoices.EUPHORIA_TRADING: RecogniseProcessorEuphoriaTrading,
    choices.ChannelNameChoices.PIPSMEUP: RecogniseProcessorPipsMeUp,
    choices.ChannelNameChoices.FX_SCORPIONS: RecogniseProcessorFxScorpions,
}


class RecogniseMessageManager:

    @classmethod
    def get_recognised_message_obj(cls, message) -> Message:

        if 'chat_id' in message:
            message_channel_name = mappings.MAPPING_CHAT_ID_TO_NAME.get(message['chat_id'])
        else:
            message_channel_name = mappings.MAPPING_CHAT_ID_TO_NAME.get(
                message['channel']['channel_id']
            )

        processor = MAPPING_RECOGNISE.get(message_channel_name, None)
        if processor:
            return processor.get_recognised_message_type(message)
        else:
            logger.error("Processor for channel={} not found".format(message['chat_id']))
