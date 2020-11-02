class InsufficientFundsException(Exception):

    message = "Insufficient funds to end this transaction. Remaining funds: {}"

    def __init__(self, remaining_funds):
        super().__init__(self.message.format(remaining_funds))
