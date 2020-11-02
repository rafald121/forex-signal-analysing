from tqdm import tqdm

from database import connect_to_db
from app.models.messages import RawMessage

class Scripts:

    def __init__(self):
        connect_to_db()

    def get_raw_messages_for_channel(self, channel_id):
        messages_for_channel = RawMessage.objects.filter(chat_id=channel_id)
        return messages_for_channel

    def set_chat_id_for_raw_messages(self):
        messages = RawMessage.objects.all()
        for message in tqdm(messages):
            message.chat_id = message.chat.id
            message.save()
