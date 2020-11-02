import logging
from datetime import datetime

from mongoengine import (
    DynamicDocument, StringField,
    ReferenceField, DateTimeField, BooleanField,
    IntField, EmbeddedDocumentField,
    UUIDField, EmbeddedDocument, NotUniqueError, DoesNotExist, MultipleObjectsReturned)

from app.models.channels import Channel
from app.models.choices import MessageTypeChoices, MessageStatusChoices

logger = logging.getLogger(__name__)


class Message(DynamicDocument):
    created_at = DateTimeField(default=datetime.now())
    id_universal = StringField(required=True)
    id_internal = StringField(required=True)
    channel = ReferenceField(Channel, required=True)
    text = StringField()
    text_raw = StringField()
    date = DateTimeField(required=True, null=False)
    status = StringField(choices=MessageStatusChoices.choices)
    type = StringField(choices=MessageTypeChoices.choices)
    quoted_message = ReferenceField('Message', default=None)

    def __str__(self):
        return f"{self.id_universal}: {self.text[:20]}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id_universal = self.get_universal_id()
        self.validate()
        return super(Message, self).save(*args, **kwargs)

    def is_message_type_signal(self):
        return self.type == MessageTypeChoices.SIGNAL

    def on_message_processed(self):
        self.status = MessageStatusChoices.PROCESSED
        self.save()

    def validate(self, clean=True):
        return super(Message, self).validate(clean)

    def get_universal_id(self):
        return f"{self.channel.name}__{self.id_internal}"

    @classmethod
    def get_universal_id_for_message(cls, message):
        return f"{message['channel']['name']}__{message['id_internal']}"

    def to_json_representation(self):
        _json_repr = self._data
        _json_repr['channel'] = self.channel._data
        if self.quoted_message is not None:
            _json_repr['quoted_message'] = self.quoted_message.to_json_representation()
        return _json_repr

    def to_json_representation_light(self):
        return {
            "id_internal": self.id_internal,
            "date": self.date,
            "text": self.text,
            "type": self.type,
            "channel_name": self.channel.name,
        }


class RawChannel(EmbeddedDocument):
    id = IntField()
    title = StringField()
    username = StringField()

    def __str__(self):
        return self.title or self.username


class RawMessage(DynamicDocument):
    message_id = IntField()
    sender_id = IntField()
    text = StringField()
    chat_id = IntField()
    message = StringField()
    is_reply = BooleanField()
    raw_text = StringField()
    reply_to_msg_id = IntField(default=None)
    chat = EmbeddedDocumentField(RawChannel)
    date = DateTimeField()
    uuid = StringField()

    meta = {'collection': 'raw_message'}

    def __str__(self):
        return f"{self.message_id}: {self.message[:20]}"

    def get_universal_id(self):
        return self.uuid