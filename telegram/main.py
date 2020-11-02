import json
import asyncio

from telegram.db_conn import get_collection_for_database, RAW_MESSAGE

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

api_id = 341990
api_hash = '0679da178cda568e373548b7241ce5d3'
phone = '+48692643349'
username = 'rafald1211'

collection = get_collection_for_database(RAW_MESSAGE)


async def connect(client):
    await client.connect()


async def authorize_user(api_id=api_id, api_hash=api_hash, phone=phone, username=username):
    client = TelegramClient(username, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password=input('Password: '))

    return client


def serialize_object_to_dict(obj):
    new_obj = {}
    object_attributes_serializable = [
        'sender_id', 'text', 'message', 'is_reply',
        'raw_text', 'reply_to_msg_id'
    ]
    new_obj['message_id'] = obj.id

    for attr in object_attributes_serializable:
        new_obj[attr] = getattr(obj, attr)

    new_obj['chat_id'] = obj.chat.id
    new_obj['chat'] = {
        'title': obj.chat.title,
        'username': obj.chat.username,
        'id': obj.chat.id
    }
    if obj.entities:
        new_obj['entities'] = [json.dumps(j.__dict__) for j in obj.entities]
    new_obj['date'] = obj.date

    new_obj['uuid'] = f"{obj.chat.id}_{obj.id}"

    return new_obj


async def get_dialogs(client, limit_channels=15):
    return await client.get_dialogs(limit=limit_channels)


async def get_messages_for_client_and_dialog(client, dialog, limit=10):
    return await client.get_messages(dialog, limit=limit)



def add_all_messages_from_channel_to_database(messages):
    for message in messages:
        obj = serialize_object_to_dict(message)
        collection.insert_one(obj)


async def main(channels_for_save_messages, limit_channel=10, limit_messages=1000):
    client = await authorize_user(api_id, api_hash, phone, username)
    dialogs_list = await get_dialogs(client, limit_channel)
    dialogs_name_list = [d.name for d in dialogs_list]

    for channel_name in channels_for_save_messages:
        if channel_name not in dialogs_name_list:
            print(f"Why channel_name={channel_name} does not exists ?")
        print(f"Fetching messages for channel(name={channel_name}")
        messages = await get_messages_for_client_and_dialog(
            client, channel_name, limit=limit_messages
        )
        print(f"Add all(count={len(messages)} messages of channel(name={channel_name} to databases")
        add_all_messages_from_channel_to_database(messages)


channels_for_save_messages = [
    'Forexelliotwave group',
    'Sure Shot Forex',
    '🎌FX ScöŕpìoNs🎌',
    'EZ Profit Pips Free Signals',
    'Forex Analysis by PaxForex',
    'ProFx Analysis Academy',
    'KijunFX Scalper',
    'SMART TRADE SOLUTIONS💱',
    'Pipsmeup',
    'ELEMENTARYFX',
    'Lifestyle Pips FX',
    '‼️ GA Forex Signals ‼️',
    'Market Profile - Forex Signals',
    'Euphoria Trading',
    'BlueCapitalFX - Signals🏛',
]
loop = asyncio.get_event_loop()
loop.run_until_complete(
    main(channels_for_save_messages, 25, 10000)
)

