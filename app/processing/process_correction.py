import json
import logging
from typing import Union

from app.models import choices
from app.models.decisions import (
    DecisionSignal,
    DecisionCorrection,
    CorrectionActionHold
)
from app.models.transactions import Transaction

logger = logging.getLogger(__file__)


class ProcessorCorrectionBase:

    @staticmethod
    def get_decision(message):
        raise NotImplementedError

    @staticmethod
    def get_correction_action_object(self, message):
        raise NotImplementedError

    @staticmethod
    def get_transaction_to_correct(self, message):
        raise NotImplementedError

    @staticmethod
    def is_correction_action_hold(self, message):
        raise NotImplementedError


class ProcessorCorrectionGaForex(ProcessorCorrectionBase):

    name = choices.ChannelNameChoices.GAFOREX

    @classmethod
    def get_decision(cls, message):

        decision_parent = DecisionCorrection(
            processor_used=cls.name,
            message=message,
            transaction_to_correct=cls.get_transaction_to_correct(message),
        ).save()

        decision_action = cls.get_correction_action_object(decision_parent)

        return decision_action

    @classmethod
    def get_correction_action_object(cls, decision):

        is_correction_hold, add_days_amount = cls.is_correction_action_hold(decision.message)

        if is_correction_hold:

            return CorrectionActionHold(
                # INHERITED
                processor_used=decision.processor_used,
                message=decision.message,
                transaction_to_correct=decision.transaction_to_correct,
                # CUSTOM
                type=choices.DecisionCorrectionTypeChoices.HOLD,
                add_days_amount=add_days_amount
            )

    @classmethod
    def get_transaction_to_correct(cls, message) -> Union[Transaction, None]:
        quoted_message = message.quoted_message

        if quoted_message.type == choices.MessageTypeChoices.SIGNAL:
            decision_signal_quoted_message_ = DecisionSignal.objects.get(message=quoted_message)
            return Transaction.objects.get(decision=decision_signal_quoted_message_)
        else:
            return None

    @classmethod
    def get_transaction_to_correct_by_message(cls, message):
        decision = DecisionSignal.objects.filter(message=message)
        return Transaction.objects.filter(decision=decision)

    @classmethod
    def is_correction_action_hold(cls, message):

        if not message['text']:
            logger.error(f"Message text is none."
                         f"Message.uuid={message.get_universal_id()}")
            return False, 0
        message_text_lower = message.text.lower()

        if "hold" in message_text_lower and "weekend" in message_text_lower:
            return True, 3
        return False, 0


MAPPING_PROCESS_SIGNAL = {
    choices.ChannelNameChoices.GAFOREX: ProcessorCorrectionGaForex
}


class ProcessCorrectionManager:

    @classmethod
    def get_decision_correction(cls, message) -> DecisionCorrection:

        processor = MAPPING_PROCESS_SIGNAL.get(message.channel.name, None)

        if processor:
            decision_correction = processor.get_decision(message)
            message.status = choices.MessageStatusChoices.PROCESSED
            message.save()
            return decision_correction
        else:
            logger.error("Processor for channel={} not found".format(message.channel))
