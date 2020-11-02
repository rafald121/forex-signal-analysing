from mongoengine import connect, DEFAULT_CONNECTION_NAME
from pymongo import MongoClient

COLLECTION_FILLED_PAIR = 'filled_pairs'
RAW_MESSAGES = 'raw_messages'
DB_BACKTEST = 'backtest'
DB_BACKTEST_TEST = 'backtest_test'
MONGO_HOST = 'mongo'
MONGO_PORT = 27017


def connect_to_db(db_name=DB_BACKTEST, host=MONGO_HOST, port=MONGO_PORT, alias=DEFAULT_CONNECTION_NAME):
    connect(db_name, host=host, port=port, alias=alias)


def get_mongoclient(host=MONGO_HOST, port=MONGO_PORT):
    return MongoClient(host, port)


def get_database_for_client(client, db_name=DB_BACKTEST):
    return client[db_name]  # return database


def get_collection_for_database(collection,
                                database=get_database_for_client(get_mongoclient())):
    return database[collection]