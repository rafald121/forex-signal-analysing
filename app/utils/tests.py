from database import get_mongoclient, DB_BACKTEST_TEST, connect_to_db


def drop_database(db=DB_BACKTEST_TEST):
    get_mongoclient().drop_database(db)
