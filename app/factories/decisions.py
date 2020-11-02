import factory
from factory import fuzzy
from factory.mongoengine import MongoEngineFactory

from app.factories.messages import MessageSignalFactory, MessageCorrectionFactory
from app.factories.transactions import TransactionFactory
from app.models.choices import ChannelNameChoices, DecisionSignalTypeChoices
from app.models.decisions import DecisionSignal, DecisionCorrection

from app.pairs import pairs_without_slash
from models.positions import StopLoss, TakeProfit


class StopLossFactory(MongoEngineFactory):
    amount = fuzzy.FuzzyDecimal(0.01, 5000)
    price = fuzzy.FuzzyDecimal(0.0001, 5000)

    class Meta:
        model = StopLoss
        strategy = factory.BUILD_STRATEGY


class TakeProfitFactory(MongoEngineFactory):
    amount = fuzzy.FuzzyDecimal(0.01, 5000)
    price = fuzzy.FuzzyDecimal(0.0001, 5000)

    class Meta:
        model = TakeProfit
        strategy = factory.BUILD_STRATEGY


class DecisionSignalFactory(MongoEngineFactory):
    processor_used = fuzzy.FuzzyChoice(ChannelNameChoices.choices)
    message = factory.SubFactory(MessageSignalFactory)
    pair = fuzzy.FuzzyChoice(pairs_without_slash)
    take_profits = factory.RelatedFactory(TakeProfitFactory)
    stop_loss = factory.RelatedFactory(StopLossFactory)
    type = fuzzy.FuzzyChoice(DecisionSignalTypeChoices.choices)

    class Meta:
        model = DecisionSignal
        strategy = factory.BUILD_STRATEGY


class DecisionCorrectionFactory(MongoEngineFactory):
    processor_used = fuzzy.FuzzyChoice(ChannelNameChoices.choices)
    message = factory.SubFactory(MessageCorrectionFactory)
    transaction_to_correct = factory.SubFactory(TransactionFactory)

    class Meta:
        model = DecisionCorrection
        strategy = factory.BUILD_STRATEGY
