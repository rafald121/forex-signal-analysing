import datetime

import factory
from factory.mongoengine import MongoEngineFactory

from app.factories.channels import ChannelFactory
from app.models.choices import MessageTypeChoices
from app.models.messages import Message
from app.models import channels


class MessageFactory(MongoEngineFactory):

    channel = factory.SubFactory(ChannelFactory)
    id_internal = factory.Sequence(lambda id: "Message_external_id: %d" % id)
    text_raw = factory.Sequence(lambda m: "Message_text_raw: %d" % m)
    date = factory.LazyFunction(datetime.datetime.now)

    class Meta:
        model = Message
        strategy = factory.BUILD_STRATEGY

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        instance = model_class(*args, **kwargs)
        if channels.Channel.objects.all():
            instance.channel = channels.Channel.objects.all().first()
        return super()._create(model_class, *args, **kwargs)


class MessageSkipFactory(MessageFactory):
    type = MessageTypeChoices.SKIP


class MessageSignalFactory(MessageFactory):
    type = MessageTypeChoices.SIGNAL


class MessageCorrectionFactory(MessageFactory):
    type = MessageTypeChoices.CORRECTION
