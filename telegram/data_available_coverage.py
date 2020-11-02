import os
import json
import constants
from telegram import constants as channels_constants

from pairs import pairs_without_slash_lower
from utils import utils_file

def check_pairs_data_coverage_for_telegram_history(telegram_channel):

    list_of_objects = utils_file.get_list_of_objects_from_file(
        constants.PATH_PROJECT+constants.PATH_TELEGRAM_MESSAGES, telegram_channel
    )
    result_reports = []
    for obj in list_of_objects:
        obj_text = obj.get('text', '-1')
        if obj_text:
            obj_text_lower = obj_text.lower()
        else:
            continue

        if 'sell' in obj_text_lower or 'buy' in obj_text_lower:
            if is_text_contain_pair(obj_text_lower):
                result_reports.append({
                    'id': obj['id'],
                    'pair': is_text_contain_pair(obj_text_lower),
                    'text': obj_text_lower,
                })
    return result_reports

def is_text_contain_pair(text):
    for pair in pairs_without_slash_lower:
        if pair in text:
            return pair
    return False


def do_job():
    result = check_pairs_data_coverage_for_telegram_history(channels_constants.GA_FOREX_SIGNALS)
    result_json = json.dumps(result)
    utils_file.save_to_file(constants.PATH_PROJECT+constants.PATH_TELEGRAM_STATISTIC, 'coverage_blue_capital.json', result_json)

    result = check_pairs_data_coverage_for_telegram_history(channels_constants.BLUE_CAPITAL_FX)
    result_json = json.dumps(result)
    utils_file.save_to_file(constants.PATH_PROJECT+constants.PATH_TELEGRAM_STATISTIC, 'coverage_ga_forex.json', result_json)

