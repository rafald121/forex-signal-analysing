# coding=utf-8
ANALYSED_CHANNELS = [
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

chats = [
    {'title': 'Forexelliotwave group', 'username': None, 'id': 1269026174},
    {'title': 'Sure Shot Forex', 'username': 'sureshotforex', 'id': 1127289760},
    {'title': '🎌FX ScöŕpìoNs🎌', 'username': None, 'id': 1269006602},
    {'title': 'EZ Profit Pips Free Signals', 'username': 'EZProfitPips', 'id': 1261909982},
    {'title': 'Forex Analysis by PaxForex', 'username': 'paxforex', 'id': 1082558830},
    {'title': 'ProFx Analysis Academy', 'username': None, 'id': 1392466168},
    {'title': 'KijunFX Scalper', 'username': 'KijunFXScalper', 'id': 1386485558},
    {'title': 'SMART TRADE SOLUTIONS💱', 'username': None, 'id': 1388795077},
    {'title': 'Pipsmeup', 'username': 'pipsmeupp', 'id': 1192184495},
    {'title': 'ELEMENTARYFX', 'username': 'ElementaryFX', 'id': 1127198630},
    {'title': 'Lifestyle Pips FX', 'username': 'lifestylepips', 'id': 1449086607},
    {'title': '‼️ GA Forex Signals ‼️', 'username': 'GASignals', 'id': 1109190126},
    {'title': 'Market Profile - Forex Signals', 'username': 'marketprof', 'id': 1145131427},
    {'title': 'Euphoria Trading', 'username': 'euphoriatrading', 'id': 1259691957},
    {'title': 'BlueCapitalFX - Signals🏛', 'username': 'bluecapitalfxsignals', 'id': 1240285626}
]


class ChannelUsernameConstants:
    SURE_SHOT_FOREX = 'sureshotforex'


class ChannelTitlesConstants:
    SURE_SHOT_FOREX = 'Sure Shot Forex'  # analizujemy
    SMART_TRADE_SOLUTIONS = 'SMART TRADE SOLUTIONS💱'  # analizujemy
    LIFESTYLE_PIP_FX = 'Lifestyle Pips FX'  # analizujemy
    BLUECAPITAL_FX = 'BlueCapitalFX - Signals🏛'  # analizujemy
    EUPHORIA_TRADING = 'Euphoria Trading'  # analizujemy
    GA_FOREX_SIGNALS = '‼️ GA Forex Signals ‼️'  # analizujemy
    PIPSMEUP = 'Pipsmeup'  # analizujemy
    FX_SCORPIONS = '🎌FX ScöŕpìoNs🎌'  # ew. analizujemy jesli starczy czasu(dosc latwe,

    EZ_PROFIT_PIPS_FREE_SIGNALS = 'EZ Profit Pips Free Signals'  # ew. analizujemy
    PROFX_ANALYSIS_ACADEMY = 'ProFx Analysis Academy'  # ew. analizujemy. przekierowania z VIP kanału
    FOREX_ANALYSIS_PAXFOREX = 'Forex Analysis by PaxForex'  # ew. analizujemy, warunkowe sygnały

    MARKET_PROFILE_FOREX = 'Market Profile - Forex Signals'  # nie analizujemy - niejasne sygnaly, przekierowania, obrazki
    KIJUNFX_SCALPER = 'KijunFX Scalper'  # nie analizujemy - nie jasne sygnały
    FOREXELLIOTWAVE_GROUP = 'Forexelliotwave group'  # nie analizujemy - grupa, a nie kanał
    ELEMENTARY_FX = 'ELEMENTARYFX'  # nie analizujemy - ciężkie do analizy


class ChannelNameChoices:
    SURE_SHOT_FOREX = "sure_shot_forex"
    GAFOREX = 'ga_forex'
    SMART_TRADE_SOLUTIONS = 'smart_trade_solutions'
    LIFESTYLE_PIP_FX = 'lifestyle_pip_fx'
    BLUECAPITAL_FX = 'bluecapital_fx'
    EUPHORIA_TRADING = 'euphoria_trading'
    PIPSMEUP = 'pipsmeup'
    FX_SCORPIONS = "fx_scorpions"

    choices = (
        SURE_SHOT_FOREX, GAFOREX,
        SMART_TRADE_SOLUTIONS, LIFESTYLE_PIP_FX,
        BLUECAPITAL_FX, EUPHORIA_TRADING,
        PIPSMEUP, FX_SCORPIONS
    )

    TELEGRAM_CHANNEL_TITLES = {
        GAFOREX: ChannelTitlesConstants.GA_FOREX_SIGNALS,
        SMART_TRADE_SOLUTIONS: ChannelTitlesConstants.SMART_TRADE_SOLUTIONS,
        SURE_SHOT_FOREX: ChannelTitlesConstants.SURE_SHOT_FOREX,
        LIFESTYLE_PIP_FX: ChannelTitlesConstants.LIFESTYLE_PIP_FX,
        BLUECAPITAL_FX: ChannelTitlesConstants.BLUECAPITAL_FX,
        EUPHORIA_TRADING: ChannelTitlesConstants.EUPHORIA_TRADING,
        PIPSMEUP: ChannelTitlesConstants.PIPSMEUP,
        FX_SCORPIONS: ChannelTitlesConstants.FX_SCORPIONS,
    }


class ChannelTypeChoices:
    FOREX = 'forex'
    CRYPTOCURRENCY = 'cryptocurrency'
    STOCK = 'stock'

    choices = (FOREX, CRYPTOCURRENCY, STOCK,)


class ChannelSourceChoices:
    TELEGRAM = 'telegram'

    choices = (TELEGRAM,)


class MessageFillTypeChoices:

    RAW = "raw"
    OBJECTS = "objects"

    choices = (RAW, OBJECTS, )


class MessageStatusChoices:
    RECEIVED = 'received'
    RECOGNIZED = 'recognized'
    PROCESSED = 'processed'

    choices = (RECEIVED, RECOGNIZED, PROCESSED,)


class MessageSignalTypeChoices:
    SIGNAL_ONE_PAIR = 'signal_one_pair'
    SIGNAL_TWO_OR_MORE_PAIRS = 'signal_two_or_more_pairs'

class MessageTypeChoices:
    SKIP = 'skip'
    SIGNAL = 'signal'
    SIGNAL_EXTRA = 'signal_extra'
    CORRECTION = 'correction'
    UNDEFINED = 'undefined'

    choices = (SKIP, SIGNAL, SIGNAL_EXTRA, CORRECTION, UNDEFINED,)


class DecisionSignalTypeChoices:
    SHORT = 'short'
    LONG = 'long'
    UNDEFINED = 'undefined'

    choices = (SHORT, LONG, UNDEFINED,)


class DecisionCorrectionTypeChoices:
    CANCEL_ALL = 'cancel_all'
    CANCEL_PARTICULAR = 'cancel_particular'
    CHANGE_STOP_LOSS = 'change_stop_loss'
    CHANGE_TAKE_PROFIT = 'change_take_profit'
    ADD_TAKE_PROFIT = 'add_take_profit'
    HOLD = 'hold'

    choices = (
        CANCEL_ALL,
        CANCEL_PARTICULAR,
        CHANGE_STOP_LOSS,
        CHANGE_TAKE_PROFIT,
        ADD_TAKE_PROFIT,
        HOLD,
    )


class TransactionStatusChoices:
    OPEN = 'open'
    CLOSED = 'closed'
    INSUFFICIENT_FUNDS = 'insufficient_funds'
    MALFORMED_STOP_LOSS = 'malformed_sl'
    MALFORMED_TAKE_PROFITS = 'malformed_tp'
    INITIAL_PRICE_NOT_FOUND = 'initial_price_not_found'
    ANY_POSITION_REALISATION_DATE_NOT_FOUND = 'any_position_realisation_date_not_found'

    choices = (OPEN, CLOSED, MALFORMED_STOP_LOSS, MALFORMED_TAKE_PROFITS, INITIAL_PRICE_NOT_FOUND, ANY_POSITION_REALISATION_DATE_NOT_FOUND, INSUFFICIENT_FUNDS)
    choices_closed = (CLOSED, MALFORMED_TAKE_PROFITS, MALFORMED_STOP_LOSS, ANY_POSITION_REALISATION_DATE_NOT_FOUND)

class PositionTypeChoices:
    STOP_LOSS = 'stop_loss'
    TAKE_PROFIT = 'take_profit'

    choices = (STOP_LOSS, TAKE_PROFIT,)


class TransactionClosedByChoices(PositionTypeChoices):
    STOP_LOSS = 'stop_loss'
    TAKE_PROFIT = 'take_profit'
    CANCELED = 'canceled'

    choices = (STOP_LOSS, TAKE_PROFIT, CANCELED)

class AmountInvestedCurrenciesChoices:
    PLN = 'PLN'
    EUR = 'EUR'
    USD = 'USD'

    choices = (PLN, EUR, USD,)
