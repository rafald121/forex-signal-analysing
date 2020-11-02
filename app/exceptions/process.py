class DecisionSignalPairNotFound(Exception):

    message = "Decision signal pair not found message(universal_id={}) in text={}"

    def __init__(self, message_universal_id, message_text):
        super().__init__(
            self.message.format(message_universal_id, message_text)
        )


class DecisionSignalTypeUndefined(Exception):

    message = "Decision signal type not defined in message(universal_id={}) in text={}"

    def __init__(self, message_universal_id, message_text):
        super().__init__(
            self.message.format(message_universal_id, message_text)
        )


class DecisionSignalAnyTakeProfitFound(Exception):

    message = "Decision signal has not got any TakeProfit in message(universal_id={}) in text={}"

    def __init__(self, message_universal_id, message_text):
        super().__init__(
            self.message.format(message_universal_id, message_text)
        )


class DecisionSignalStopLossNotFound(Exception):

    message = "Decision signal has got StopLoss in message(universal_id={}) in text={}"

    def __init__(self, message_universal_id, message_text):
        super().__init__(
            self.message.format(message_universal_id, message_text)
        )


class InvalidTakeProfit(Exception):

    message = "Couldn't process TakeProfit. Takeprofit content={}"

    def __init__(self, take_profit_content):
        super().__init__(
            self.message.format(take_profit_content)
        )


class IncorrectDecisionSignalTradeLevels(Exception):

    message = "Decision Signal has to has both stop loss and at least one take profit." \
              "message(universal_id)={}) text={}"

    def __init__(self, message_universal_id, message_text):
        super().__init__(
            self.message.format(message_universal_id, message_text)
        )