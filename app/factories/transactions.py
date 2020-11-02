import factory
from factory import fuzzy
from factory.mongoengine import MongoEngineFactory

from app.models.choices import AmountInvestedCurrenciesChoices
from app.models.transactions import Transaction, AmountInvested


class AmountInvestedFactory(MongoEngineFactory):

    amount = fuzzy.FuzzyDecimal(0, 1000)
    currency = fuzzy.FuzzyChoice(AmountInvestedCurrenciesChoices.choices)

    class Meta:
        model = AmountInvested
        strategy = factory.BUILD_STRATEGY


class TransactionFactory(MongoEngineFactory):

    initial_pair_price = fuzzy.FuzzyDecimal(0.1, 500)
    amount_invested = factory.SubFactory(AmountInvestedFactory)

    class Meta:
        model = Transaction
        strategy = factory.BUILD_STRATEGY
