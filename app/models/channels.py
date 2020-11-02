from mongoengine import DynamicDocument, StringField, IntField

from app.models.choices import (
    ChannelTypeChoices,
    ChannelSourceChoices,
    ChannelNameChoices
)


class Channel(DynamicDocument):
    name = StringField(unique=True, required=True, choices=ChannelNameChoices.choices)
    type = StringField(choices=ChannelTypeChoices.choices)
    source = StringField(choices=ChannelSourceChoices.choices)
    title = StringField()
    username = StringField()
    channel_id = IntField()

    def __str__(self):
        return self.name
