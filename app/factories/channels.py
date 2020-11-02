import factory
from factory import fuzzy
from factory.mongoengine import MongoEngineFactory

from app.models.channels import Channel
from app.models.choices import ChannelNameChoices, ChannelTypeChoices, ChannelSourceChoices


class ChannelFactory(MongoEngineFactory):
    name = fuzzy.FuzzyChoice(ChannelNameChoices.choices)
    type = fuzzy.FuzzyChoice(ChannelTypeChoices.choices)
    source = ChannelSourceChoices.TELEGRAM

    class Meta:
        model = Channel
        strategy = factory.BUILD_STRATEGY


class ChannelForexFactory(ChannelFactory):
    type = ChannelTypeChoices.FOREX


class ChannelGAForexFactory(ChannelFactory):
    name = ChannelNameChoices.GAFOREX

