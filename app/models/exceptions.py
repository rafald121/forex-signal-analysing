from app.pairs import pairs_without_slash


class IncorrectDecisionSignalMessageType(Exception):

    message = "Incorrect DecisionSignal Message.Type. Message type has to be SIGNAL"

    def __init__(self):
        super().__init__(self.message)


class IncorrectMessageType(Exception):

    message = 'Incorrect Message Type. Message that has quoted message has to have type=correction'

    def __init__(self):
        super().__init__(self.message)


class IncorrectDecisionSignalPair(Exception):
    message = f'Pair has to be one of following choices: {pairs_without_slash}'

    def __init__(self, **kwargs):
        super().__init__(f"Message pair={kwargs['pair']} incorrect. {self.message}")


class IncorrectDecisionCorrectionMessage(Exception):
    message = 'Incorrect Decision Correction message type. It has to be type "CORRECTION'

    def __init__(self):
        super().__init__(self.message)

