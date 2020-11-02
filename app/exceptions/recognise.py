class MoreThanOnePairFound(Exception):

    message = "More than one pair has been found in message signal. Message: {}"

    def __init__(self, message):
        super().__init__(self.message.format(message))


class ZeroMessageTypeHasBeenRecognised(Exception):

    message = "Incorrect recognision since our processor recognised 0 message_type " \
              "that match this message. Message: {}"

    def __init__(self, message):
        super().__init__(self.message.format(message))


class MoreThanOneMessageTypeHasBeenRecognised(Exception):

    message = "Incorrect recognision since our processor recognised more than 1 message_type " \
              "that match this message. Message: {}"

    def __init__(self, message):
        super().__init__(self.message.format(message))