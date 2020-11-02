from app.models.choices import ChannelNameChoices, ChannelSourceChoices


MAPPING_CHAT_ID_TO_NAME = {
    1127289760: ChannelNameChoices.SURE_SHOT_FOREX,
    1109190126: ChannelNameChoices.GAFOREX,
    1388795077: ChannelNameChoices.SMART_TRADE_SOLUTIONS,
    1449086607: ChannelNameChoices.LIFESTYLE_PIP_FX,
    1240285626: ChannelNameChoices.BLUECAPITAL_FX,
    1259691957: ChannelNameChoices.EUPHORIA_TRADING,
    1192184495: ChannelNameChoices.PIPSMEUP,
    1269006602: ChannelNameChoices.FX_SCORPIONS,
}


MAPPING_NAME_TO_CHAT_ID = {
    name: id for id, name in MAPPING_CHAT_ID_TO_NAME.items()
}


MAPPING_WHICH_MESSAGE_ATTRIBUTE_RETURN_CHANNEL = {
    ChannelSourceChoices.TELEGRAM: 'chat'
}